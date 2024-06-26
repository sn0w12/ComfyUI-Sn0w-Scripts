from nodes import VAEDecode, EmptyLatentImage, CLIPTextEncode
from comfy_extras.nodes_custom_sampler import SamplerCustom, BasicScheduler, PolyexponentialScheduler, VPScheduler, SplitSigmasDenoise
from comfy_extras.nodes_align_your_steps import AlignYourStepsScheduler
from ..sn0w import Logger, Utility
from .custom_schedulers.custom_schedulers import CustomSchedulers
import comfy.samplers

class SimpleSamplerCustom:
    logger = Logger()

    @classmethod
    def initialize(cls):
        cls.custom_schedulers = CustomSchedulers()
        cls.build_scheduler_list()

    @classmethod
    def build_scheduler_list(cls):
        custom_scheduler_names = list(cls.custom_schedulers.get_scheduler_settings().keys())
        cls.logger.log(custom_scheduler_names, "DEBUG")
        cls.scheduler_list = comfy.samplers.KSampler.SCHEDULERS + ["align_your_steps", "polyexponential", "vp"] + custom_scheduler_names
        cls.scheduler_settings = {name: settings for name, settings in cls.custom_schedulers.get_scheduler_settings().items()}
        cls.custom_scheduler_defaults = cls.custom_schedulers.get_scheduler_defaults()

    @classmethod
    def get_custom_class_sigmas(cls, scheduler_name, *args, **kwargs):
        return cls.custom_schedulers.get_sigmas(scheduler_name, *args, **kwargs)

    @classmethod
    def INPUT_TYPES(cls):
        cls.initialize()
        return {
                "required": {
                    "model": ("MODEL",),
                    "clip": ("CLIP", ),
                    "vae": ("VAE", ),
                    "add_noise": ("BOOLEAN", {"default": True}),
                    "noise_seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
                    "steps": ("INT", {"default": 20, "min": 1, "max": 10000}),
                    "cfg": ("FLOAT", {"default": 8.0, "min": 0.0, "max": 100.0, "step":0.1, "round": 0.01}),
                    "sampler_name": (comfy.samplers.KSampler.SAMPLERS, ),
                    "scheduler_name": (cls.scheduler_list, ),
                    "denoise": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step":0.01, "round": 0.01}),
                    "width": ("INT", {"default": 0, "min": 0, "step":64}),
                    "height": ("INT", {"default": 0, "min": 0, "step":64}),
                },
                "optional": {
                    "positive": ("*"),
                    "negative": ("*"),
                },
                "hidden" : {
                    "extra_info": "EXTRA_PNGINFO",
                    "id": "UNIQUE_ID",
                }
            }
    
    RETURN_TYPES = ("IMAGE", "LATENT", "CONDITIONING", "CONDITIONING",)
    RETURN_NAMES = ("IMAGE", "LATENT", "POSITIVE", "NEGATIVE",)

    FUNCTION = "sample"

    CATEGORY = "sampling/custom_sampling"

    def sample(self, model, clip, vae, add_noise, noise_seed, steps, cfg, sampler_name, scheduler_name, denoise, width, height, **kwargs):
        custom_sampler = SamplerCustom()
        vae_decode = VAEDecode()
        text_encode = CLIPTextEncode()

        positive_prompt = self.get_prompt("positive", text_encode, clip, kwargs)
        negative_prompt = self.get_prompt("negative", text_encode, clip, kwargs)
        model_type = Utility.get_model_type_simple(model)
        image_output = Utility.get_node_output(kwargs['extra_info'], kwargs['id'], 0)
        latent_image = EmptyLatentImage().generate(width, height)[0]

        # Get sampler and sigmas
        sampler = self.get_sampler(sampler_name)[0]
        sigmas = self.get_custom_sigmas(model, model_type, scheduler_name, steps, denoise)

        samples = custom_sampler.sample(model, add_noise, noise_seed, cfg, positive_prompt, negative_prompt, sampler, sigmas, latent_image)
        if (image_output["links"] != []):
            image = vae_decode.decode(vae, samples[1])
        else:
            image = (None, )

        return (image[0], samples[1], positive_prompt, negative_prompt,)
    
    def get_denoised_sigmas(self, sigmas, denoise):
        if denoise == 1:
            return (None, sigmas, )
        
        return SplitSigmasDenoise.get_sigmas(self, sigmas, denoise)
    
    def get_custom_sigmas(self, model, model_type, scheduler_name, steps, denoise):
        if denoise > 0 and scheduler_name not in comfy.samplers.KSampler.SCHEDULERS:
            steps = int(steps / denoise)
        
        if scheduler_name == "align_your_steps":
            if (model_type == "SD3"): # Temporary to make AYS work with sd3 models
                model_type = "SDXL"
            sigmas = AlignYourStepsScheduler.get_sigmas(self, model_type, steps, denoise)[0]
        elif scheduler_name == "polyexponential":
            sigmas = self.get_denoised_sigmas(PolyexponentialScheduler.get_sigmas(self, steps, 14.614642, 0.0291675, 1.0)[0], denoise)[1]
        elif scheduler_name == "vp":
            sigmas = self.get_denoised_sigmas(VPScheduler.get_sigmas(self, steps, 14.0, 0.05, 0.075)[0], denoise)[1]
        elif scheduler_name in comfy.samplers.KSampler.SCHEDULERS:
            sigmas = BasicScheduler.get_sigmas(self, model, scheduler_name, steps, denoise)[0]
        else:
            defaults = self.get_custom_scheduler_defaults(scheduler_name)
            sigmas = self.get_denoised_sigmas(self.get_custom_class_sigmas(scheduler_name, steps, *defaults.values())[0], denoise)[1]

        return sigmas
    
    def get_sampler(self, sampler_name):
        sampler = comfy.samplers.sampler_object(sampler_name)
        return (sampler, )
    
    def get_custom_scheduler_defaults(self, scheduler):
        return {key: value[1] for key, value in self.custom_scheduler_defaults[scheduler].items()}
    
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
