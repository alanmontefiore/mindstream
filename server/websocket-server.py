import asyncio
import time
import json
import websockets
import torch # type: ignore

from img2img import Pipeline, InputParams
from processImage import process_image

IMAGE_PORT = 5001

WIDTH, HEIGHT = 512, 512

class Args:
    taesd = True
    acceleration = "none"  # or tensorrt or xformers
    safety_checker = False
    engine_dir = "engines"

# === Pipeline Initialization ===
print("Initializing pipeline...")

pipeline = Pipeline(
    args=Args(),
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu"),
    torch_dtype=torch.float16,
)

shared_params = InputParams()

async def handle_json_status(message):
    try:
        status_data = json.loads(message)
        print(f"[Metadata] Received status_data: {status_data}")
    except json.JSONDecodeError:
        print("[Warning] Invalid JSON received.")

async def handle_websocket(websocket):
    async for message in websocket:
        # Handle JSON metadata (text messages)
        if isinstance(message, str):
            await handle_json_status(message)
        # Handle frame data (binary messages)
        elif isinstance(message, bytes):
            print(f"[WebSocket] Received frame data of size: {len(message)} bytes")

            result_bytes = process_image(pipeline, message, shared_params)

            if result_bytes is None:
                print("[process_image] No result bytes received.")
                continue

            await websocket.send(result_bytes)


async def run_websocket_server(host='0.0.0.0', port=IMAGE_PORT):
    print(f"[WebSocket Server] Listening on {host}:{port}")
    async with websockets.serve(handle_websocket, host, port):
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(run_websocket_server())