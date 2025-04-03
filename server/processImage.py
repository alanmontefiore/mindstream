import io
from img2img import InputParams
import threading

params_lock = threading.Lock()

def process_image(pipeline, image_bytes: bytes, shared_params: InputParams):
    try:
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