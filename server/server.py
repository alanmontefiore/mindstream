import socket
import threading
import struct
import io
import json
import torch

from img2img import Pipeline, InputParams

class Args:
    taesd = True
    acceleration = "tensorrt"  # or "xformers"
    safety_checker = False
    engine_dir = "engines"

# === Pipeline Initialization ===
print("Initializing pipeline...")

pipeline = Pipeline(
    args=Args(),
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu"),
    torch_dtype=torch.float16,
)

params_lock = threading.Lock()
shared_params = InputParams()

def handle_status_data(status_conn):
    global shared_params
    buffer = b''
    try:
        while True:
            # Receive JSON status data
            while b'\n' not in buffer:
                chunk = status_conn.recv(1024)
                if not chunk:
                    return
                buffer += chunk
            line, buffer = buffer.split(b'\n', 1)
            try:
                update = json.loads(line.decode())
                with params_lock:
                    shared_params_dict = shared_params.dict()
                    shared_params_dict.update(update)
                    shared_params = InputParams(**shared_params_dict)  # Validate types here
                print(f"[Status] Updated params: {shared_params}")
            except Exception as e:
                print(f"[Status] Error updating params: {e}")
    except Exception as e:
        print(f"[Status] Connection error: {e}")
    finally:
        status_conn.close()

# === Receiver: handles both image + status based on prefix ===
def receive_image(conn):
    while True:
        try:
            prefix = conn.recv(1)
            if not prefix:
                print("[Receive] Connection closed by client.")
                break

            if prefix == b'I':
                size_data = b''
                while len(size_data) < 4:
                    chunk = conn.recv(4 - len(size_data))
                    if not chunk:
                        print("[Receive] Connection closed while reading size.")
                        return
                    size_data += chunk

                size = struct.unpack('>I', size_data)[0]

                data = b''
                while len(data) < size:
                    chunk = conn.recv(size - len(data))
                    if not chunk:
                        print("[Receive] Connection closed while reading image data.")
                        return
                    data += chunk

                img_bytes = process_image(data)
                send_image(img_bytes, conn)
            else:
                print(f"[Receive] Unknown prefix: {prefix}")
        except Exception as e:
            print(f"[Receive] Error: {e}")
            break

# === Image Processor Thread ===
def process_image(data):
    global shared_params

    try:
        image_bytes = data

        with params_lock:
            prompt = shared_params.prompt
            width = shared_params.width
            height = shared_params.height
            quality = shared_params.quality
            seed = shared_params.seed
            num_inference_steps = shared_params.num_inference_steps
            guidance_scale = shared_params.guidance_scale

        try:
            params = InputParams(
                prompt=prompt,
                width=width,
                height=height,
                seed=seed,
                image=image_bytes,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
                quality=quality,
            )
        except Exception as e:
            print(f"[Process] Error creating InputParams: {e}")
            return

        try:
            output_image = pipeline.predict(params)
        except Exception as e:
            print(f"[Process] Error during prediction: {e}")
            return   

        # Encode and enqueue
        buf = io.BytesIO()
        output_image.save(buf, format="JPEG", quality=quality)
        return buf.getvalue()
    
    except Exception as e:
        print(f"[Process] Error: {e}")

# === Send back to client ===
def send_image(data, conn):
    try:
        conn.sendall(struct.pack('>I', len(data)) + data)
    except Exception as e:
        print(f"[Send] Error: {e}")
        return
        
# === Server setup ===
def handle_client(conn, status_conn, addr):
    print(f"Client connected: {addr}")
    threading.Thread(target=receive_image, args=(conn,), daemon=True).start()
    threading.Thread(target=handle_status_data, args=(status_conn,), daemon=True).start()

# === Server setup ===
def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', 6969))
    server.listen(5)
    print("Server listening on port 6969...")

    status_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    status_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    status_socket.bind(('0.0.0.0', 7860))
    status_socket.listen(5)
    print("Status server listening on port 7860...")

    while True:
        conn, addr = server.accept()
        status_conn, addr = status_socket.accept()
        threading.Thread(target=handle_client, args=(conn, status_conn, addr), daemon=True).start()

# Start the server
if __name__ == "__main__":
    start_server()
