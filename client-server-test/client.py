import asyncio
import numpy as np
from PIL import Image
import time
from collections import deque
import json
import websockets
import threading
import io

WIDTH, HEIGHT = 512, 512
FRAME_SIZE = WIDTH * HEIGHT * 3

status_data = {"prompt": "psychedelic patterns, cats, colorful", "width": 512, "height": 512, "quality": 85, "seed": 42, "num_inference_steps": 50, "guidance_scale": 5.2}

HOST = '213.173.110.135'
PORT = 18885
LOCAL_WS_PORT = 8765

client = None

class AsyncFrameClient:
    def __init__(self, host=HOST, port=PORT):
        self.host = host
        self.port = port
        self.reader = None
        self.writer = None

    async def connect(self):
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)

    async def send_status_data(self, status_data: dict):
        encoded = json.dumps(status_data).encode()
        self.writer.write(encoded)
        await self.writer.drain()

    async def send_frame(self, img: Image.Image) -> tuple[Image.Image, float]:
        arr = np.asarray(img.resize((WIDTH, HEIGHT)), dtype=np.uint8)

        start_time = time.perf_counter()

        self.writer.write(arr.tobytes())
        await self.writer.drain()

        result_data = await self.reader.readexactly(FRAME_SIZE)
        end_time = time.perf_counter()

        result_np = np.frombuffer(result_data, dtype=np.uint8).reshape((HEIGHT, WIDTH, 3))
        duration_ms = (end_time - start_time) * 1000  # in milliseconds
        return Image.fromarray(result_np), duration_ms

    async def close(self):
        self.writer.close()
        await self.writer.wait_closed()

async def handle_websocket(websocket):
    global client
    print("[WebSocket] Client connected.")
    durations = deque(maxlen=60)
    try:
        async for message in websocket:
            if isinstance(message, bytes):
                image = Image.open(io.BytesIO(message)).convert("RGB")
                _result, duration = await client.send_frame(image)
                durations.append(duration)

                avg_duration = sum(durations) / len(durations)
                print(f"Avg RTD: {avg_duration:.2f} ms")
            else:
                print(f"[WebSocket] Unknown message type: {type(message)}")
    except Exception as e:
        print(f"[WebSocket] Error: {e}")

async def start_websocket():
    print(f"[WebSocket] Server starting on ws://localhost:{LOCAL_WS_PORT}")
    async with websockets.serve(
        handle_websocket, 
        "localhost",
        LOCAL_WS_PORT
    ):
        await asyncio.Future()

async def main():
    global client
    client = AsyncFrameClient()
    await client.connect()
    await client.send_status_data(status_data)

async def run_all():
    await asyncio.gather(main(), start_websocket())

if __name__ == "__main__":
    asyncio.run(run_all())
