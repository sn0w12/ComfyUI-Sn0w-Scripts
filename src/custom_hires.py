from nodes import KSamplerAdvanced, VAEDecode, VAEEncode
from .upscale_with_model_by import UpscaleImageBy
import comfy.samplers

class CustomHires:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": ("MODEL",),
                "vae": ("VAE", ),
                "image": ("IMAGE", ),
                "upscale_by": ("FLOAT", {"default": 1.5, "min": 0.0, "max": 100.0, "step":0.1, "round": 0.01}),
                "add_noise": (["enable", "disable"], ),
                "noise_seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
                "cfg": ("FLOAT", {"default": 8.0, "min": 0.0, "max": 100.0, "step":0.1, "round": 0.01}),
                "sampler_name": (comfy.samplers.KSampler.SAMPLERS, ),
                "scheduler": (comfy.samplers.KSampler.SCHEDULERS, ),
                "positive": ("CONDITIONING",),
                "negative": ("CONDITIONING",),
                "steps": ("INT", {"default": 0, "min": 0, "max": 10000}),
                "start_at_step": ("INT", {"default": 0, "min": 0, "max": 10000}),
                "end_at_step": ("INT", {"default": 10000, "min": 0, "max": 10000}),
                "upscale_model": ("UPSCALE_MODEL",),
            },
        }

    RETURN_TYPES = ("IMAGE", )
    RETURN_NAMES = ("IMAGE", )
    FUNCTION = "hires_fix"
    CATEGORY = "sn0w"

    def hires_fix(self, model, vae, image, upscale_by, add_noise, noise_seed, cfg, sampler_name, scheduler, positive, negative, steps, start_at_step, end_at_step, upscale_model):
        k_sampler_node = KSamplerAdvanced()
        vae_decode = VAEDecode()
        vae_encode = VAEEncode()
        image_upscaler = UpscaleImageBy()
        
        upscaled_image = image_upscaler.upscale(image, upscale_by, upscale_model)[0]
        upscaled_latent = vae_encode.encode(vae, upscaled_image)[0]
        upscaled_samples = k_sampler_node.sample(model, add_noise, noise_seed, steps, cfg, sampler_name, scheduler, positive, negative, upscaled_latent, start_at_step, end_at_step, "disable")[0]
        image = vae_decode.decode(vae, upscaled_samples)

        return image
    