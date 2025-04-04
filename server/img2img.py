import sys
import os
import io

sys.path.append(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
    )
)

from utils.wrapper import StreamDiffusionWrapper
import torch
from pydantic import BaseModel
from PIL import Image
from typing import Optional

base_model = "stabilityai/sd-turbo"
# base_model = "digiplay/LusterMix_v1.5_safetensors"
# base_model = "stabilityai/stable-diffusion-3.5-large"
# base_model = "digiplay/CleanLinearMix_nsfw"
# base_model = "digiplay/Colorful_v3.1"
# base_model = "recoilme/colorfulxl"
# base_model = "dreamlike-art/dreamlike-photoreal-2.0"

taesd_model = "madebyollin/taesd"

default_prompt: str = "cats in a cyberpunk city"
default_negative_prompt: str = "black, blurry, low quality, text, logo, watermark, cropped, extra limbs, bad anatomy"

class InputParams(BaseModel):
        prompt: str = default_prompt
        width: int = 512
        height: int = 512
        quality: int = 85
        seed: int = 42
        num_inference_steps: int = 50
        guidance_scale: float = 1.2
        image: Optional[bytes] = None
class Pipeline:
    class Info(BaseModel):
        name: str = "MindStream img2img"
        input_mode: str = "image"
        page_content: str = ""

    def __init__(self, args, device: torch.device, torch_dtype: torch.dtype):
        params = InputParams()
        self.stream = StreamDiffusionWrapper(
            model_id_or_path=base_model,
            use_tiny_vae=args.taesd,
            device=device,
            dtype=torch_dtype,
            t_index_list=[35, 45],
            frame_buffer_size=1,
            width=params.width,
            height=params.height,
            use_lcm_lora=False,
            output_type="pil",
            warmup=10,
            vae_id=None,
            acceleration=args.acceleration,
            mode="img2img",
            use_denoising_batch=True,
            cfg_type="full",
            use_safety_checker=args.safety_checker,
            #enable_similar_image_filter=True,
            #similar_image_filter_threshold=0.98,
            engine_dir=args.engine_dir,
        )

        self.last_prompt = default_prompt
        self.last_guidance_scale = params.guidance_scale
        self.last_num_inference_steps = params.num_inference_steps
        
        self.stream.prepare(
            prompt=default_prompt,
            negative_prompt=default_negative_prompt,
            num_inference_steps=params.num_inference_steps,
            guidance_scale=params.guidance_scale,
        )

    def predict(self, params: InputParams) -> Image.Image:
        # Check if guidance_scale or num_inference_steps has changed
        if (
            params.guidance_scale != self.last_guidance_scale
            or params.num_inference_steps != self.last_num_inference_steps
        ):
            self.stream.prepare(
                prompt=params.prompt,
                negative_prompt=default_negative_prompt,
                num_inference_steps=params.num_inference_steps,
                guidance_scale=params.guidance_scale,
            )
            # Update the last used values
            self.last_guidance_scale = params.guidance_scale
            self.last_num_inference_steps = params.num_inference_steps

        pil_image = Image.open(io.BytesIO(params.image))
        image_tensor = self.stream.preprocess_image(pil_image)
        output_image = self.stream(
            image=image_tensor, 
            prompt=params.prompt, 
        )
        return output_image
