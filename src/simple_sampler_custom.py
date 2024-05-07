from nodes import VAEDecode, EmptyLatentImage, CLIPTextEncode
from comfy_extras.nodes_custom_sampler import SamplerCustom, BasicScheduler
from comfy_extras.nodes_align_your_steps import AlignYourStepsScheduler
import comfy.samplers

class SimpleSamplerCustom:
    scheduler_list = comfy.samplers.KSampler.SCHEDULERS + ["align_your_steps"]

    @classmethod
    def INPUT_TYPES(cls):
        return {
                "required": {
                    "model": ("MODEL",),
                    "model_type": (["SD1", "SDXL", "SVD"], ),
                    "clip": ("CLIP", ),
                    "vae": ("VAE", ),
                    "add_noise": ("BOOLEAN", {"default": True}),
                    "noise_seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
                    "steps": ("INT", {"default": 10, "min": 10, "max": 10000}),
                    "cfg": ("FLOAT", {"default": 8.0, "min": 0.0, "max": 100.0, "step":0.1, "round": 0.01}),
                    "sampler_name": (comfy.samplers.KSampler.SAMPLERS, ),
                    "scheduler_name": (cls.scheduler_list, ),
                    "width": ("INT", {"default": 0, "min": 0, "step":64}),
                    "height": ("INT", {"default": 0, "min": 0, "step":64}),
                    "positive": ("STRING", {"default": ""}),
                    "negative": ("STRING", {"default": ""}),
                },
                "optional": {
                    "sigmas (optional)": ("SIGMAS", ),
                }
            }
    
    RETURN_TYPES = ("IMAGE", "LATENT", "CONDITIONING", "CONDITIONING")
    RETURN_NAMES = ("IMAGE", "LATENT", "POSITIVE", "NEGATIVE")

    FUNCTION = "sample"

    CATEGORY = "sampling/custom_sampling"

    def sample(self, model, model_type, clip, vae, add_noise, noise_seed, steps, cfg, sampler_name, scheduler_name, width, height, positive, negative, **kwargs):
        custom_sampler = SamplerCustom()
        vae_decode = VAEDecode()
        text_encode = CLIPTextEncode()

        # Encode inputs
        positive_prompt = text_encode.encode(clip, positive)[0]
        negative_prompt = text_encode.encode(clip, negative)[0]

        # Create latent
        latent_image = EmptyLatentImage().generate(width, height)[0]

        # Get sampler and sigmas
        sampler = self.get_sampler(sampler_name)[0]
        if 'sigmas (optional)' in kwargs and kwargs['sigmas (optional)'] is not None:
            sigmas = kwargs['sigmas (optional)']
        else:
            sigmas = self.get_custom_sigmas(model, model_type, scheduler_name, steps)

        # Generate and decode image
        samples = custom_sampler.sample(model, add_noise, noise_seed, cfg, positive_prompt, negative_prompt, sampler, sigmas, latent_image)
        image = vae_decode.decode(vae, samples[1])

        return (image[0], samples[1], positive_prompt, negative_prompt)
    
    def get_sampler(self, sampler_name):
        sampler = comfy.samplers.sampler_object(sampler_name)
        return (sampler, )
    
    def get_custom_sigmas(self, model, model_type, scheduler_name, steps):
        if scheduler_name == "align_your_steps":
            sigmas = AlignYourStepsScheduler.get_sigmas(self, model_type, steps, 1)[0]
        else:
            sigmas = BasicScheduler.get_sigmas(self, model, scheduler_name, steps, 1)[0]
        
        return sigmas
