import socket
import threading
import struct
import io
import json
import torch # type: ignore
import time
import uuid

from img2img import Pipeline, InputParams
from processImage import process_image

IMAGE_PORT = 6969

WIDTH, HEIGHT = 512, 512
FRAME_SIZE = WIDTH * HEIGHT * 3

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

async def handle_json_status(reader):
    metadata_bytes = b'{'
    while True:
        byte = await reader.readexactly(1)
        metadata_bytes += byte
        if byte == b'}':
            break
    try:
        status_data = json.loads(metadata_bytes.decode())
        print(f"[Metadata] Received status_data: {status_data}")
    except json.JSONDecodeError:
        print("[Warning] Invalid JSON received.")

async def handle_client(reader, writer):
    try:
        while True:
            # Peek to decide what kind of message it is (metadata or frame)
            peek = await reader.readexactly(1)
            if peek == b'{':  # JSON (assumes metadata messages start with `{`)
                await handle_json_status(reader)
                continue

            # Put the peeked byte back for frame reading
            image_bytes = peek + await reader.readexactly(FRAME_SIZE - 1)
            
            result_bytes = process_image(pipeline, image_bytes, shared_params)

            # Ensure correct size
            if len(result_bytes) != FRAME_SIZE:
                print("Warning: processed frame size mismatch.")
                continue

            writer.write(result_bytes)
            await writer.drain()
    except (asyncio.IncompleteReadError, ConnectionResetError):
        pass
    finally:
        writer.close()
        await writer.wait_closed()

async def run_server(host='0.0.0.0', port=IMAGE_PORT):
    server = await asyncio.start_server(handle_client, host, port)
    async with server:
        print(f"[Binary Server] Listening on {host}:{port}")
        await server.serve_forever()

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_server())
