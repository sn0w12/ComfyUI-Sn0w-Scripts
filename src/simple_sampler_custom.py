from nodes import VAEDecode, EmptyLatentImage, CLIPTextEncode
from comfy_extras.nodes_custom_sampler import SamplerCustom, BasicScheduler, PolyexponentialScheduler, VPScheduler
from comfy_extras.nodes_align_your_steps import AlignYourStepsScheduler
from server import PromptServer
from ..sn0w import Logger, MessageHolder
import comfy.samplers

class SimpleSamplerCustom:
    logger = Logger()
    scheduler_list = comfy.samplers.KSampler.SCHEDULERS + ["align_your_steps", "polyexponential", "vp"]

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
                    "denoise": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step":0.01, "round": 0.01}),
                },
                "optional": {
                    "positive": ("*"),
                    "negative": ("*"),
                    "sigmas (optional)": ("SIGMAS", ),
                },
                "hidden": {
                    "unique_id": "UNIQUE_ID",
                },
            }
    
    RETURN_TYPES = ("IMAGE", "LATENT", "CONDITIONING", "CONDITIONING")
    RETURN_NAMES = ("IMAGE", "LATENT", "POSITIVE", "NEGATIVE")

    FUNCTION = "sample"

    CATEGORY = "sampling/custom_sampling"

    def sample(self, model, model_type, clip, vae, add_noise, noise_seed, steps, cfg, sampler_name, scheduler_name, width, height, denoise, **kwargs):
        custom_sampler = SamplerCustom()
        vae_decode = VAEDecode()
        text_encode = CLIPTextEncode()

        # Encode inputs
        positive_prompt = self.get_prompt("positive", text_encode, clip, kwargs)
        negative_prompt = self.get_prompt("negative", text_encode, clip, kwargs)

        # Create latent
        latent_image = EmptyLatentImage().generate(width, height)[0]

        # Get sampler and sigmas
        sampler = self.get_sampler(sampler_name)[0]
        if 'sigmas (optional)' in kwargs and kwargs['sigmas (optional)'] is not None:
            sigmas = kwargs['sigmas (optional)']
        else:
            sigmas = self.get_custom_sigmas(model, model_type, scheduler_name, steps, denoise, kwargs["unique_id"])

        # Generate and decode image
        samples = custom_sampler.sample(model, add_noise, noise_seed, cfg, positive_prompt, negative_prompt, sampler, sigmas, latent_image)
        image = vae_decode.decode(vae, samples[1])

        return (image[0], samples[1], positive_prompt, negative_prompt)
    
    def get_sampler(self, sampler_name):
        sampler = comfy.samplers.sampler_object(sampler_name)
        return (sampler, )
    
    def get_scheduler_values(self, unique_id):
        PromptServer.instance.send_sync("get_scheduler_values", {
            "id": unique_id,
        })
        outputs = MessageHolder.waitForMessage(unique_id)
        return outputs
    
    def get_custom_sigmas(self, model, model_type, scheduler_name, steps, denoise, unique_id):
        if scheduler_name == "align_your_steps":
            sigmas = AlignYourStepsScheduler.get_sigmas(self, model_type, steps, denoise)[0]
        elif scheduler_name == "polyexponential":
            values = self.get_scheduler_values(unique_id)
            
            # Extract the values from the list of dictionaries
            for param in values:
                if param['name'] == 'sigma_max':
                    sigma_max = param['value']
                elif param['name'] == 'sigma_min':
                    sigma_min = param['value']
                elif param['name'] == 'rho':
                    rho = param['value']

            sigmas = PolyexponentialScheduler.get_sigmas(self, steps, sigma_max, sigma_min, rho)[0]
        elif scheduler_name == "vp":
            values = self.get_scheduler_values(unique_id)
            
            # Extract the values from the list of dictionaries
            for param in values:
                if param['name'] == 'beta_d':
                    beta_d = param['value']
                elif param['name'] == 'beta_min':
                    beta_min = param['value']
                elif param['name'] == 'eps_s':
                    eps_s = param['value']

            sigmas = VPScheduler.get_sigmas(self, steps, beta_d, beta_min, eps_s)[0]
        else:
            sigmas = BasicScheduler.get_sigmas(self, model, scheduler_name, steps, denoise)[0]
        
        return sigmas
    
    def get_prompt(self, name, text_encode, clip, kwargs):
        if name in kwargs and kwargs[name] is not None:
            if isinstance(kwargs[name], str):
                return text_encode.encode(clip, kwargs[name])[0]
            elif isinstance(kwargs[name], list):
                return kwargs[name]
            else:
                log = f"{name} prompt cannot be {type(kwargs[name]).__name__}, it has to be either a string or conditioning."
                self.logger.log(log, "ERROR")
                raise TypeError(log)
