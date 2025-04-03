import asyncio
import time
import json

IMAGE_PORT = 5001

WIDTH, HEIGHT = 512, 512
FRAME_SIZE = WIDTH * HEIGHT * 3

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
            data = peek + await reader.readexactly(FRAME_SIZE - 1)

            # Process raw bytes → raw bytes
            # result_bytes = process_frame(data)
            # Simulate processing time
            time.sleep(0.05)
            result_bytes = data

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