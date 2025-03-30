from fastapi import FastAPI, WebSocket, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import PlainTextResponse
import markdown2
import logging
import time
import asyncio
import os
import mimetypes
import torch
from types import SimpleNamespace

from config import config, Args
from util import pil_to_frame, bytes_to_pil
from img2img import Pipeline

# fix mime error on Windows
mimetypes.add_type("application/javascript", ".js")

THROTTLE = 1.0 / 120

class App:
    def __init__(self, config: Args, pipeline):
        self.args = config
        self.pipeline = pipeline
        self.latest_params = None  # store latest input for single user
        self.app = FastAPI()
        self.init_app()

    def init_app(self):
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        @self.app.exception_handler(Exception)
        async def global_exception_handler(request: Request, exc: Exception):
            logging.error(f"Unhandled server error: {exc}")
            return PlainTextResponse("An unexpected error occurred. Please try again later.", status_code=500)

        @self.app.websocket("/api/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            try:
                await self.handle_websocket_data(websocket)
            except Exception as e:
                logging.error(f"WebSocket error: {e}")
            finally:
                await websocket.close()
                logging.info("User disconnected")

        async def handle_websocket_data(websocket: WebSocket):
            last_time = time.time()
            try:
                while True:
                    try:
                        if self.args.timeout > 0 and time.time() - last_time > self.args.timeout:
                            await websocket.send_json({"status": "timeout", "message": "Your session has ended"})
                            await websocket.close()
                            return
                        data = await websocket.receive_json()
                        if data is None:
                            logging.error("Received None data")
                            await websocket.close()
                            return
                        if data.get("status") == "next_frame":
                            info = self.pipeline.Info()
                            params_data = await websocket.receive_json()
                            params = self.pipeline.InputParams(**params_data)
                            params = SimpleNamespace(**params.dict())
                            if info.input_mode == "image":
                                image_data = await websocket.receive_bytes()
                                if not image_data:
                                    await websocket.send_json({"status": "send_frame"})
                                    continue
                                params.image = bytes_to_pil(image_data)
                            self.latest_params = params
                            last_time = time.time()
                    except Exception as e:
                        logging.error(f"Error during WebSocket data handling: {e}")
                        await websocket.send_json({"status": "error", "message": str(e)})
            except Exception as e:
                logging.error(f"WebSocket processing error: {e}")
                await websocket.close()

        self.handle_websocket_data = handle_websocket_data

        @self.app.get("/api/stream")
        async def stream(request: Request):
            async def generate():
                while True:
                    try:
                        start = time.time()
                        if self.latest_params is None:
                            await asyncio.sleep(0.1)
                            continue
                        image = self.pipeline.predict(self.latest_params)
                        if image is None:
                            continue
                        frame = pil_to_frame(image)
                        yield frame
                        if self.args.debug:
                            print(f"Frame generated in {time.time() - start:.2f} seconds")
                    except Exception as e:
                        logging.error(f"Error during frame generation: {e}")
                        await asyncio.sleep(1) 
                        
            return StreamingResponse(
                generate(),
                media_type="multipart/x-mixed-replace;boundary=frame",
                headers={"Cache-Control": "no-cache"},
            )

        @self.app.get("/api/settings")
        async def settings():
            info_schema = self.pipeline.Info.schema()
            info = self.pipeline.Info()
            page_content = markdown2.markdown(info.page_content) if info.page_content else ""
            input_params = self.pipeline.InputParams.schema()
            return JSONResponse({
                "info": info_schema,
                "input_params": input_params,
                "max_queue_size": self.args.max_queue_size,
                "page_content": page_content,
            })

        if not os.path.exists("public"):
            os.makedirs("public")

        self.app.mount("/", StaticFiles(directory="./frontend/public", html=True), name="public")


device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
torch_dtype = torch.float16
pipeline = Pipeline(config, device, torch_dtype)
app = App(config, pipeline).app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=config.host,
        port=config.port,
        reload=config.reload,
        ssl_certfile=config.ssl_certfile,
        ssl_keyfile=config.ssl_keyfile,
    )
