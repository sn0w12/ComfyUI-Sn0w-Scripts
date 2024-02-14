from nodes import KSamplerAdvanced, VAEDecode, VAEEncode, EmptyLatentImage, ImageScaleBy
from comfy_extras.nodes_clip_sdxl import CLIPTextEncodeSDXL
from comfy_extras.nodes_upscale_model import ImageUpscaleWithModel
import comfy.samplers

class SimpleSamplerXlNode:
    @classmethod
    def INPUT_TYPES(s):
        return {"required":
                    {"model": ("MODEL",),
                    "clip": ("CLIP", ),
                    "vae": ("VAE", ),
                    "add_noise": (["enable", "disable"], ),
                    "noise_seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
                    "steps": ("INT", {"default": 20, "min": 1, "max": 10000}),
                    "cfg": ("FLOAT", {"default": 8.0, "min": 0.0, "max": 100.0, "step":0.1, "round": 0.01}),
                    "width": ("INT", {"default": 0, "min": 0}),
                    "height": ("INT", {"default": 0, "min": 0}),
                    "sampler_name": (comfy.samplers.KSampler.SAMPLERS, ),
                    "scheduler": (comfy.samplers.KSampler.SCHEDULERS, ),
                    "positive": ("STRING", {"default": ""}),
                    "negative": ("STRING", {"default": ""}),
                    "start_at_step": ("INT", {"default": 0, "min": 0, "max": 10000}),
                    "end_at_step": ("INT", {"default": 10000, "min": 0, "max": 10000}),
                    "return_with_leftover_noise": (["disable", "enable"], ),
                    "hires": ("BOOLEAN", {"default": False},),
                    "upscale_model": ("UPSCALE_MODEL",),
                    "hires_steps": ("INT", {"default": 5, "min": 1, "max": 20}),
                     }
                }

    RETURN_TYPES = ("IMAGE", "CONDITIONING", "CONDITIONING")
    RETURN_NAMES = ("IMAGE", "POSITIVE", "NEGATIVE")
    FUNCTION = "sample"

    CATEGORY = "sampling"

    def sample(self, model, clip, vae, add_noise, noise_seed, steps, cfg, width, height, sampler_name, scheduler, positive, negative, start_at_step, end_at_step, return_with_leftover_noise, hires, upscale_model, hires_steps):
        k_sampler_node = KSamplerAdvanced()
        vae_decode = VAEDecode()
        vae_encode = VAEEncode()
        text_encode_xl = CLIPTextEncodeSDXL()
        upscaler = ImageUpscaleWithModel()
        scale_image = ImageScaleBy()

        latent_image = EmptyLatentImage().generate(width, height)[0]

        positive_prompt = text_encode_xl.encode(clip, width, height, 0, 0, width, height, positive, positive)[0]
        negative_prompt = text_encode_xl.encode(clip, width, height, 0, 0, width, height, negative, negative)[0]

        # Sampling
        samples = k_sampler_node.sample(model, add_noise, noise_seed, steps, cfg, sampler_name, scheduler, positive_prompt, negative_prompt, latent_image, start_at_step, end_at_step, return_with_leftover_noise)[0]

        if (hires):
            # Decode the samples
            image = vae_decode.decode(vae, samples)[0]

            total_hires_steps = 25 - hires_steps
            
            upscaled_image = upscaler.upscale(upscale_model, image)[0]
            upscaled_image = scale_image.upscale(upscaled_image, "nearest-exact", 0.5)[0]
            upscaled_latent = vae_encode.encode(vae, upscaled_image)[0]
            upscaled_samples = k_sampler_node.sample(model, add_noise, noise_seed, 25, cfg, sampler_name, scheduler, positive_prompt, negative_prompt, upscaled_latent, total_hires_steps, 1000, return_with_leftover_noise)[0]
            image = vae_decode.decode(vae, upscaled_samples)
        else:
            image = vae_decode.decode(vae, samples)

        return (image[0], positive_prompt, negative_prompt)