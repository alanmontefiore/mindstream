import cv2
import socket
import struct
import io
import threading
import queue
import time
from PIL import Image
import numpy as np
import json
import asyncio
import websockets
import tkinter as tk
from PIL import ImageTk

HOST = '213.173.110.171'
PORT = 12046
STATUS_PORT = 12045
LOCAL_WS_PORT = 8765

FPS_LIMIT = 1 / 22.0

send_queue = queue.Queue()
display_queue = queue.Queue()

status_data = {"prompt": "african woman", "width": 512, "height": 512, "quality": 65, "seed": 6324527, "num_inference_steps": 50, "guidance_scale": 1.2}

# === Receiver thread: get processed image and show ===
def receiver(sock):
    try:
        while True:
            size_data = sock.recv(4)
            if not size_data or len(size_data) < 4:
                print("Receiver error: Connection closed or incomplete size data")
                break
            size = struct.unpack('>I', size_data)[0]

            data = b''
            while len(data) < size:
                chunk = sock.recv(size - len(data))
                if not chunk:
                    return
                data += chunk

            try:
                img = Image.open(io.BytesIO(data))
                frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
                display_queue.put(frame)
            except Exception as e:
                print(f"Receiver error: Invalid image data - {e}")
    except Exception as e:
        print(f"Receiver error: {e}")

# === Function to Update Prompt ===
def update_params(status_sock):
    global status_data

    try:
        status_sock.sendall(json.dumps(status_data).encode() + b'\n')
    except Exception as e:
        print(f"Error sending updated prompt: {e}")

# === Local WebSocket Server Handler ===
async def handle_local_server(websocket):
    print("[WebSocket] Client connected.")
    try:
        async for message in websocket:
            if isinstance(message, bytes):
                img_bytes = message
            else:
                print(f"[WebSocket] Unknown message type: {type(message)}")
                continue

            # Forward to the remote server with a prefix and 4-byte length header
            sock.sendall(b'I' + struct.pack('>I', len(img_bytes)) + img_bytes)# Forward to the remote server

    except websockets.exceptions.ConnectionClosed as e:
        print(f"[WebSocket] Connection closed: {e}")
    except Exception as e:
        print(f"[WebSocket] Error: {e}")


async def start_local_websocket_server():
    print(f"[WebSocket] Server starting on ws://localhost:{LOCAL_WS_PORT}")
    async with websockets.serve(
        handle_local_server, 
        "localhost",
        LOCAL_WS_PORT
    ):
        await asyncio.Future()  # Run forever

def create_gui(status_sock):
    global status_data
    def on_update():
        status_data["prompt"] = prompt_entry.get()
        status_data["seed"] = int(seed_entry.get())
        status_data["guidance_scale"] = float(guidance_scale_entry.get())

        update_params(status_sock)

    def update_frame():
        if not display_queue.empty():
            frame = display_queue.get()
            if frame is not None and isinstance(frame, np.ndarray):
                # Convert the frame to a format compatible with tkinter
                img = ImageTk.PhotoImage(image=Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))
                video_label.config(image=img)
                video_label.image = img  # Keep a reference to avoid garbage collection
        root.after(10, update_frame)  # Schedule the next frame update

    def on_close():
        print("Closing application...")
        sock.close()
        status_sock.close()
        cv2.destroyAllWindows()
        root.destroy()
        exit(0) 

    root = tk.Tk()
    root.title("Update Params")
    root.protocol("WM_DELETE_WINDOW", on_close)

    # Prompt update section
    tk.Label(root, text="Enter new prompt:").pack(pady=5)
    prompt_entry = tk.Entry(root, width=50)
    prompt_entry.pack(pady=5)
    prompt_entry.insert(0, status_data["prompt"])

    # Seed update section
    tk.Label(root, text="Enter new seed:").pack(pady=5)
    seed_entry = tk.Entry(root, width=50)
    seed_entry.pack(pady=5)
    seed_entry.insert(0, str(status_data["seed"])) 

    # Guidance scale update section
    tk.Label(root, text="Guidance scale:").pack(pady=5)
    guidance_scale_entry = tk.Entry(root, width=50)
    guidance_scale_entry.pack(pady=5)
    guidance_scale_entry.insert(0, str(status_data.get("guidance_scale", 1.2))) 

    update_button = tk.Button(root, text="Update Params", command=on_update)
    update_button.pack(pady=5)

    # Video stream section
    video_label = tk.Label(root)
    video_label.pack(pady=10)

    # Start updating frames
    root.after(10, update_frame)

    root.mainloop()


# === Main Function ===
if __name__ == "__main__":
    print("[Main] WebSocket server is running. Waiting for browser connections...")

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))

    # Start WebSocket server in a separate thread
    threading.Thread(target=lambda: asyncio.run(start_local_websocket_server()), daemon=True).start()

    # === Create a separate socket for status data ===
    status_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    status_sock.connect((HOST, STATUS_PORT))

    threading.Thread(target=receiver, args=(sock,), daemon=True).start()

    # Start the GUI in the main thread
    create_gui(status_sock)

    try:
        while True:
            if cv2.waitKey(1) == 27:  # ESC
                break
    finally:
        sock.close()
        status_sock.close()
        cv2.destroyAllWindows()