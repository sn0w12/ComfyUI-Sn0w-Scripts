from nodes import KSampler, VAEDecode, VAEEncode, EmptyLatentImage, LoraLoader
from .image_batch import WAS_Image_Batch
from comfy_extras.nodes_clip_sdxl import CLIPTextEncodeSDXL
import comfy.samplers
import folder_paths

class LoraTestXLNode:
    @classmethod
    def INPUT_TYPES(s):
        return {"required":
                    {"model": ("MODEL",),
                    "clip": ("CLIP", ),
                    "vae": ("VAE", ),
                    "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
                    "steps": ("INT", {"default": 20, "min": 1, "max": 10000}),
                    "cfg": ("FLOAT", {"default": 8.0, "min": 0.0, "max": 100.0, "step":0.1, "round": 0.01}),
                    "width": ("INT", {"default": 0, "min": 0}),
                    "height": ("INT", {"default": 0, "min": 0}),
                    "sampler_name": (comfy.samplers.KSampler.SAMPLERS, ),
                    "scheduler": (comfy.samplers.KSampler.SCHEDULERS, ),
                    "positive": ("STRING", {"default": ""}),
                    "negative": ("STRING", {"default": ""}),
                    "denoise": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01}),
                    "lora_info": ("STRING", {"default": ""}),
                    "add_default_generation": ("BOOLEAN", {"default": False},),
                     }
                }

    RETURN_TYPES = ("IMAGE", "INT")
    RETURN_NAMES = ("IMAGES", "FONT_SIZE")
    FUNCTION = "sample"

    CATEGORY = "sampling"

    def sample(self, model, clip, vae, seed, steps, cfg, width, height, sampler_name, scheduler, positive, negative, denoise, lora_info, add_default_generation):
        k_sampler_node = KSampler()
        vae_decode = VAEDecode()
        text_encode_xl = CLIPTextEncodeSDXL()
        lora_loader = LoraLoader()
        image_batcher = WAS_Image_Batch()

        latent_image = EmptyLatentImage().generate(width, height)[0]

        full_loras_list = folder_paths.get_filename_list("loras")

        loras = lora_info.split(";")
        images = []

        for lora in loras:
            # Skip empty or improperly formatted lora strings
            if lora.startswith("<lora:"):
                trimmed_string = lora[6:-1]
                parts = trimmed_string.split(':')

                if len(parts) < 2 or not parts[1]:
                    continue  # Skip if lora string is incomplete or strength is missing

                lora_name_suffix = parts[0] + ".safetensors"
                lora_strength = float(parts[1])

                # Find the full path of the lora
                full_lora_path = next((full_path for full_path in full_loras_list if lora_name_suffix in full_path), None)

                if full_lora_path:
                    modified_model, modified_clip = lora_loader.load_lora(model, clip, full_lora_path, lora_strength, lora_strength)

                positive_prompt = text_encode_xl.encode(modified_clip, width, height, 0, 0, width, height, positive, positive)[0]
                negative_prompt = text_encode_xl.encode(modified_clip, width, height, 0, 0, width, height, negative, negative)[0]

                # Sampling
                samples = k_sampler_node.sample(modified_model, seed, steps, cfg, sampler_name, scheduler, positive_prompt, negative_prompt, latent_image, denoise)[0]
            else:
                positive_prompt = text_encode_xl.encode(clip, width, height, 0, 0, width, height, positive, positive)[0]
                negative_prompt = text_encode_xl.encode(clip, width, height, 0, 0, width, height, negative, negative)[0]

                # Sampling
                samples = k_sampler_node.sample(model, seed, steps, cfg, sampler_name, scheduler, positive_prompt, negative_prompt, latent_image, denoise)[0]

            # Decode the samples
            image = vae_decode.decode(vae, samples)[0]

            images.append(image)

        # Dynamically construct kwargs for image_batch
        image_batch_kwargs = {f"images_{chr(97 + i)}": image for i, image in enumerate(images)}

        longest_string = max(loras, key=len)
        font_char = len(longest_string)

        font_size = self.estimate_font_size(width, font_char, 50, 50)

        # Using WAS_Image_Batch to batch the images together
        batched_images = image_batcher.image_batch(**image_batch_kwargs)
        return (batched_images, font_size)

    def estimate_font_size(image_width, text_length, initial_font_size=16, tolerance=50):
        font_size = initial_font_size
        estimated_char_width = font_size * 0.55  # Estimate: character width is 60% of font size

        while True:
            estimated_text_width = text_length * estimated_char_width
            width_difference = abs(estimated_text_width - image_width)

            if width_difference <= tolerance:
                # If within tolerance, stop adjusting
                break
            elif estimated_text_width < image_width - tolerance:
                # If text is too narrow, increase font size
                font_size += 1
            elif estimated_text_width > image_width + tolerance:
                # If text is too wide, decrease font size
                font_size -= 1

            # Recalculate estimated character width
            estimated_char_width = font_size * 0.55

        return font_size
