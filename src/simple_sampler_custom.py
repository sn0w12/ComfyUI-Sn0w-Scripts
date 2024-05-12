from nodes import VAEDecode, EmptyLatentImage, CLIPTextEncode
from comfy_extras.nodes_custom_sampler import SamplerCustom, BasicScheduler, PolyexponentialScheduler, VPScheduler, SplitSigmasDenoise
from comfy_extras.nodes_align_your_steps import AlignYourStepsScheduler
from server import PromptServer
from ..sn0w import Logger, MessageHolder
from .custom_schedulers.custom_schedulers import CustomSchedulers
from .show_sigmas import ShowSigmasNode
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

    @classmethod
    def get_custom_class_sigmas(cls, scheduler_name, *args, **kwargs):
        return cls.custom_schedulers.get_sigmas(scheduler_name, *args, **kwargs)

    @classmethod
    def INPUT_TYPES(cls):
        cls.initialize()
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
                    "denoise": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step":0.01, "round": 0.01}),
                },
                "optional": {
                    "positive": ("*"),
                    "negative": ("*"),
                    "scheduler_name": (cls.scheduler_list, ),
                    "sigmas (optional)": ("SIGMAS", ),
                    "latent (optional)": ("LATENT", ),
                    "width": ("INT", {"default": 0, "min": 0, "step":64}),
                    "height": ("INT", {"default": 0, "min": 0, "step":64}),
                },
                "hidden": {
                    "unique_id": "UNIQUE_ID",
                },
            }
    
    RETURN_TYPES = ("IMAGE", "LATENT", "CONDITIONING", "CONDITIONING", "IMAGE")
    RETURN_NAMES = ("IMAGE", "LATENT", "POSITIVE", "NEGATIVE", "SIGMAS GRAPH")

    FUNCTION = "sample"

    CATEGORY = "sampling/custom_sampling"

    def sample(self, model, model_type, clip, vae, add_noise, noise_seed, steps, cfg, sampler_name, denoise, **kwargs):
        custom_sampler = SamplerCustom()
        vae_decode = VAEDecode()
        text_encode = CLIPTextEncode()

        # Encode inputs
        positive_prompt = self.get_prompt("positive", text_encode, clip, kwargs)
        negative_prompt = self.get_prompt("negative", text_encode, clip, kwargs)

        # Create latent
        if 'latent (optional)' in kwargs and kwargs['latent (optional)'] is not None:
            latent_image = kwargs['latent (optional)']
        else:
            if 'width' in kwargs and 'height' in kwargs:
                latent_image = EmptyLatentImage().generate(kwargs['width'], kwargs['height'])[0]
            else:
                raise ValueError(f"If no latent is provided width and height is needed.")

        # Get sampler and sigmas
        sampler = self.get_sampler(sampler_name)[0]
        if 'sigmas (optional)' in kwargs and kwargs['sigmas (optional)'] is not None:
            sigmas = kwargs['sigmas (optional)']
        else:
            sigmas = self.get_custom_sigmas(model, model_type, kwargs["scheduler_name"], steps, denoise, kwargs["unique_id"])

        # Generate and decode image
        samples = custom_sampler.sample(model, add_noise, noise_seed, cfg, positive_prompt, negative_prompt, sampler, sigmas, latent_image)
        if (self.should_decode_image(kwargs["unique_id"])):
            image = vae_decode.decode(vae, samples[1])
        else:
            image = (None, )

        sigmas_list = ShowSigmasNode.sigmas_to_list(self, sigmas)

        PromptServer.instance.send_sync("sampler_get_sigmas", {
            "id": kwargs["unique_id"],
            "sigmas": sigmas_list,
        })
        outputs = MessageHolder.waitForMessage(kwargs["unique_id"])
        
        final_tensor = ShowSigmasNode.image_to_tensor(self, outputs)

        return (image[0], samples[1], positive_prompt, negative_prompt, final_tensor,)
    
    def get_sampler(self, sampler_name):
        sampler = comfy.samplers.sampler_object(sampler_name)
        return (sampler, )
    
    def get_scheduler_values(self, unique_id, widgets_needed):
        PromptServer.instance.send_sync("get_scheduler_values", {
            "id": unique_id,
            "widgets_needed": widgets_needed,
        })
        outputs = MessageHolder.waitForMessage(unique_id)
        return outputs
    
    def get_denoised_sigmas(self, sigmas, denoise):
        if denoise == 1:
            return (None, sigmas, )
        
        return SplitSigmasDenoise.get_sigmas(self, sigmas, denoise)

    def get_custom_sigmas(self, model, model_type, scheduler_name, steps, denoise, unique_id):
        if scheduler_name == "align_your_steps":
            sigmas = AlignYourStepsScheduler.get_sigmas(self, model_type, steps, denoise)[0]
        elif scheduler_name == "polyexponential":
            values = self.get_scheduler_values(unique_id, ["sigma_max_poly", "sigma_min_poly", "rho"])
            
            sigma_max = values["sigma_max_poly"]["value"]
            sigma_min = values["sigma_min_poly"]["value"]
            rho = values["rho"]["value"]
            self.logger.log(f"Sigma Max: {sigma_max}, Sigma Min: {sigma_min}, Rho: {rho}", "DEBUG")

            sigmas = self.get_denoised_sigmas(PolyexponentialScheduler.get_sigmas(self, steps, sigma_max, sigma_min, rho)[0], denoise)[1]
                
        elif scheduler_name == "vp":
            values = self.get_scheduler_values(unique_id, ["beta_d", "beta_min", "eps_s"])
            
            beta_d = values["beta_d"]["value"]
            beta_min = values["beta_min"]["value"]
            eps_s = values["eps_s"]["value"]
            self.logger.log(f"Beta D: {beta_d}, Beta Min: {beta_min}, Eps S: {eps_s}", "DEBUG")

            sigmas = self.get_denoised_sigmas(VPScheduler.get_sigmas(self, steps, beta_d, beta_min, eps_s)[0], denoise)[1]
        elif scheduler_name in comfy.samplers.KSampler.SCHEDULERS:
            sigmas = BasicScheduler.get_sigmas(self, model, scheduler_name, steps, denoise)[0]
        else:
            scheduler_settings = self.scheduler_settings.get(scheduler_name)
            if not scheduler_settings:
                raise ValueError(f"No settings found for scheduler '{scheduler_name}'")

            # Fetch settings from the node API
            values = self.get_scheduler_values(unique_id, scheduler_settings)

            # Map the settings to their actual values using the names from the scheduler settings
            mapped_settings = [values[setting_name]["value"] for setting_name in scheduler_settings]

            # Log the fetched settings
            self.logger.log(f"Fetched settings for {scheduler_name}: {mapped_settings}", "DEBUG")

            # Get sigmas using the custom scheduler
            sigmas = self.get_denoised_sigmas(self.get_custom_class_sigmas(scheduler_name, steps, *mapped_settings)[0], denoise)[1]
        
        self.logger.print_sigmas_differences(scheduler_name, sigmas)
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
            
    def should_decode_image(self, unique_id):
        PromptServer.instance.send_sync("should_decode_image", {
            "id": unique_id,
        })
        outputs = MessageHolder.waitForMessage(unique_id)
        return outputs
