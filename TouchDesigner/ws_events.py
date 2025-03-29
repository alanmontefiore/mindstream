import json
import numpy as np
import cv2
import io

def onConnect(dat):
    print("✅ WebSocket connected, sending prompt...")

    prompt_data = {
        "prompt": "a futuristic samurai in the rain",
        "steps": 4,
        "guidance_scale": 2.0,
        "width": 512,
        "height": 512,
        "fps": 25
    }

    dat.sendText(json.dumps(prompt_data))
    return

def onReceiveText(dat, text):
    print("📥 Text received:", text)
    return

def onReceiveBinary(dat, data):
    # Convert binary JPEG → numpy array
    image_np = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)

    if image_np is None:
        print("⚠️ Failed to decode image")
        return

    # Convert BGR (OpenCV) to RGB
    image_np = cv2.cvtColor(image_np, cv2.COLOR_BGR2RGB)

    # Send to TOP
    top = op('imageTOP')
    top.copyNumpyArray(image_np)
    return
