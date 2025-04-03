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
import tkinter as tk
from PIL import ImageTk

HOST = '213.173.110.94'
PORT = 47962
STATUS_PORT = 47961

FPS_LIMIT = 1 / 22.0

send_queue = queue.Queue()
display_queue = queue.Queue()

status_data = {"prompt": "african woman", "width": 512, "height": 512, "quality": 65, "seed": 6324527, "num_inference_steps": 50, "guidance_scale": 1.2}

# === Sender thread: capture webcam and send ===
def sender(sock):
    cap = cv2.VideoCapture(0)
    
    try:
        while True:
            start = time.time()

            ret, frame = cap.read()
            if not ret:
                continue

            resized = cv2.resize(frame, (512, 512))
            image = Image.fromarray(cv2.cvtColor(resized, cv2.COLOR_BGR2RGB))

            buf = io.BytesIO()
            image.save(buf, format='JPEG', quality=85)
            img_bytes = buf.getvalue()

            try:
                sock.sendall(b'I' + struct.pack('>I', len(img_bytes)) + img_bytes)
            except Exception as e:
                print(f"Sender error: {e}")
                break

            # Enforce 25 FPS cap
            elapsed = time.time() - start
            if elapsed < FPS_LIMIT:
                time.sleep(FPS_LIMIT - elapsed)
    finally:
        cap.release()

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

# === GUI for Client ===
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

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((HOST, PORT))

# === Create a separate socket for status data ===
status_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
status_sock.connect((HOST, STATUS_PORT))

threading.Thread(target=sender, args=(sock,), daemon=True).start()
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
