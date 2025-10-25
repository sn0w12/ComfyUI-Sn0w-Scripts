import torch
import latent_preview
import comfy.samplers
from nodes import VAEDecode, EmptyLatentImage, CLIPTextEncode
from comfy.k_diffusion import sampling as k_diffusion_sampling
from comfy_extras.nodes_align_your_steps import AlignYourStepsScheduler
from ..sn0w import Logger, Utility
from .custom_schedulers.custom_schedulers import CustomSchedulers


class Noise_EmptyNoise:
    def __init__(self):
        self.seed = 0

    def generate_noise(self, input_latent):
        latent_image = input_latent["samples"]
        return torch.zeros(latent_image.shape, dtype=latent_image.dtype, layout=latent_image.layout, device="cpu")


class Noise_RandomNoise:
    def __init__(self, seed):
        self.seed = seed

    def generate_noise(self, input_latent):
        latent_image = input_latent["samples"]
        batch_inds = input_latent["batch_index"] if "batch_index" in input_latent else None
        return comfy.sample.prepare_noise(latent_image, self.seed, batch_inds)


class _SplitSigmasDenoise:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "sigmas": ("SIGMAS",),
                "denoise": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01}),
            }
        }

    RETURN_TYPES = ("SIGMAS", "SIGMAS")
    RETURN_NAMES = ("high_sigmas", "low_sigmas")
    CATEGORY = "sampling/custom_sampling/sigmas"

    FUNCTION = "get_sigmas"

    def get_sigmas(self, sigmas, denoise):
        steps = max(sigmas.shape[-1] - 1, 0)
        total_steps = round(steps * denoise)
        sigmas1 = sigmas[:-(total_steps)]
        sigmas2 = sigmas[-(total_steps + 1) :]
        return (sigmas1, sigmas2)


class _VPScheduler:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "steps": ("INT", {"default": 20, "min": 1, "max": 10000}),
                "beta_d": ("FLOAT", {"default": 19.9, "min": 0.0, "max": 5000.0, "step": 0.01, "round": False}),  # TODO: fix default values
                "beta_min": ("FLOAT", {"default": 0.1, "min": 0.0, "max": 5000.0, "step": 0.01, "round": False}),
                "eps_s": ("FLOAT", {"default": 0.001, "min": 0.0, "max": 1.0, "step": 0.0001, "round": False}),
            }
        }

    RETURN_TYPES = ("SIGMAS",)
    CATEGORY = "sampling/custom_sampling/schedulers"

    FUNCTION = "get_sigmas"

    def get_sigmas(self, steps, beta_d, beta_min, eps_s):
        sigmas = k_diffusion_sampling.get_sigmas_vp(n=steps, beta_d=beta_d, beta_min=beta_min, eps_s=eps_s)
        return (sigmas,)


class _PolyexponentialScheduler:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "steps": ("INT", {"default": 20, "min": 1, "max": 10000}),
                "sigma_max": ("FLOAT", {"default": 14.614642, "min": 0.0, "max": 5000.0, "step": 0.01, "round": False}),
                "sigma_min": ("FLOAT", {"default": 0.0291675, "min": 0.0, "max": 5000.0, "step": 0.01, "round": False}),
                "rho": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 100.0, "step": 0.01, "round": False}),
            }
        }

    RETURN_TYPES = ("SIGMAS",)
    CATEGORY = "sampling/custom_sampling/schedulers"

    FUNCTION = "get_sigmas"

    def get_sigmas(self, steps, sigma_max, sigma_min, rho):
        sigmas = k_diffusion_sampling.get_sigmas_polyexponential(n=steps, sigma_min=sigma_min, sigma_max=sigma_max, rho=rho)
        return (sigmas,)


class _BasicScheduler:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "model": ("MODEL",),
                "scheduler": (comfy.samplers.SCHEDULER_NAMES,),
                "steps": ("INT", {"default": 20, "min": 1, "max": 10000}),
                "denoise": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01}),
            }
        }

    RETURN_TYPES = ("SIGMAS",)
    CATEGORY = "sampling/custom_sampling/schedulers"

    FUNCTION = "get_sigmas"

    def get_sigmas(self, model, scheduler, steps, denoise):
        total_steps = steps
        if denoise < 1.0:
            if denoise <= 0.0:
                return (torch.FloatTensor([]),)
            total_steps = int(steps / denoise)

        sigmas = comfy.samplers.calculate_sigmas(model.get_model_object("model_sampling"), scheduler, total_steps).cpu()
        sigmas = sigmas[-(steps + 1) :]
        return (sigmas,)


class _SamplerCustom:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "model": ("MODEL",),
                "add_noise": ("BOOLEAN", {"default": True}),
                "noise_seed": ("INT", {"default": 0, "min": 0, "max": 0xFFFFFFFFFFFFFFFF, "control_after_generate": True}),
                "cfg": ("FLOAT", {"default": 8.0, "min": 0.0, "max": 100.0, "step": 0.1, "round": 0.01}),
                "positive": ("CONDITIONING",),
                "negative": ("CONDITIONING",),
                "sampler": ("SAMPLER",),
                "sigmas": ("SIGMAS",),
                "latent_image": ("LATENT",),
            }
        }

    RETURN_TYPES = ("LATENT", "LATENT")
    RETURN_NAMES = ("output", "denoised_output")

    FUNCTION = "sample"

    CATEGORY = "sampling/custom_sampling"

    def sample(self, model, add_noise, noise_seed, cfg, positive, negative, sampler, sigmas, latent_image):
        latent = latent_image
        latent_image = latent["samples"]
        latent = latent.copy()
        latent_image = comfy.sample.fix_empty_latent_channels(model, latent_image)
        latent["samples"] = latent_image

        if not add_noise:
            noise = Noise_EmptyNoise().generate_noise(latent)
        else:
            noise = Noise_RandomNoise(noise_seed).generate_noise(latent)

        noise_mask = None
        if "noise_mask" in latent:
            noise_mask = latent["noise_mask"]

        x0_output = {}
        callback = latent_preview.prepare_callback(model, sigmas.shape[-1] - 1, x0_output)

        disable_pbar = not comfy.utils.PROGRESS_BAR_ENABLED
        samples = comfy.sample.sample_custom(
            model,
            noise,
            cfg,
            sampler,
            sigmas,
            positive,
            negative,
            latent_image,
            noise_mask=noise_mask,
            callback=callback,
            disable_pbar=disable_pbar,
            seed=noise_seed,
        )

        out = latent.copy()
        out["samples"] = samples
        if "x0" in x0_output:
            out_denoised = latent.copy()
            out_denoised["samples"] = model.model.process_latent_out(x0_output["x0"].cpu())
        else:
            out_denoised = out
        return (out, out_denoised)


class SimpleSamplerCustom:
    logger = Logger()

    scheduler_list = None

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
        if cls.scheduler_list is None:
            cls.initialize()
        return {
            "required": {
                "model": ("MODEL",),
                "clip": ("CLIP",),
                "vae": ("VAE",),
                "add_noise": ("BOOLEAN", {"default": True}),
                "noise_seed": ("INT", {"default": 0, "min": 0, "max": 0xFFFFFFFFFFFFFFFF}),
                "steps": ("INT", {"default": 20, "min": 1, "max": 10000}),
                "cfg": ("FLOAT", {"default": 8.0, "min": 0.0, "max": 100.0, "step": 0.1, "round": 0.01}),
                "sampler_name": (comfy.samplers.KSampler.SAMPLERS,),
                "scheduler_name": (cls.scheduler_list,),
                "denoise": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01, "round": 0.01}),
                "width": ("INT", {"default": 0, "min": 0, "step": 64}),
                "height": ("INT", {"default": 0, "min": 0, "step": 64}),
            },
            "optional": {
                "positive": ("*"),
                "negative": ("*"),
            },
            "hidden": {
                "extra_info": "EXTRA_PNGINFO",
                "id": "UNIQUE_ID",
            },
        }

    @classmethod
    def VALIDATE_INPUTS(cls, input_types):
        return True

    RETURN_TYPES = ("IMAGE", "LATENT", "CONDITIONING", "CONDITIONING")
    RETURN_NAMES = ("IMAGE", "LATENT", "POSITIVE", "NEGATIVE")

    FUNCTION = "sample"

    CATEGORY = "sampling/custom_sampling"

    def sample(
        self,
        model,
        clip,
        vae,
        add_noise,
        noise_seed,
        steps,
        cfg,
        sampler_name,
        scheduler_name,
        denoise,
        width,
        height,
        **kwargs,
    ):
        custom_sampler = _SamplerCustom()
        vae_decode = VAEDecode()
        text_encode = CLIPTextEncode()

        positive_prompt = self.get_prompt("positive", text_encode, clip, kwargs)
        negative_prompt = self.get_prompt("negative", text_encode, clip, kwargs)
        model_type = Utility.get_model_type_simple(model)
        image_output = Utility.get_node_output(kwargs["extra_info"], kwargs["id"], 0)
        latent_image = EmptyLatentImage().generate(width, height)[0]

        # Get sampler and sigmas
        sampler = self.get_sampler(sampler_name)[0]
        sigmas = self.get_custom_sigmas(model, model_type, scheduler_name, steps, denoise)
        self.logger.print_sigmas_differences(scheduler_name, sigmas)

        samples = custom_sampler.sample(model, add_noise, noise_seed, cfg, positive_prompt, negative_prompt, sampler, sigmas, latent_image)
        try:
            if image_output is not None and image_output["links"] != []:
                image = vae_decode.decode(vae, samples[1])
            else:
                image = (None,)
        except (TypeError, KeyError):
            # If we get a TypeError (NoneType) or KeyError, decode the image
            image = vae_decode.decode(vae, samples[1])

        return (image[0], samples[1], positive_prompt, negative_prompt)

    def get_denoised_sigmas(self, sigmas, denoise):
        if denoise == 1:
            return (None, sigmas)

        return _SplitSigmasDenoise.get_sigmas(self, sigmas, denoise)

    def get_custom_sigmas(self, model, model_type, scheduler_name, steps, denoise):
        if denoise > 0 and scheduler_name not in comfy.samplers.KSampler.SCHEDULERS:
            steps = int(steps / denoise)

        if scheduler_name == "align_your_steps":
            if model_type == "SD3":  # Temporary to make AYS work with sd3 models
                model_type = "SDXL"
            sigmas = AlignYourStepsScheduler.get_sigmas(self, model_type, steps, denoise)[0]
        elif scheduler_name == "polyexponential":
            sigmas = self.get_denoised_sigmas(_PolyexponentialScheduler.get_sigmas(self, steps, 14.614642, 0.0291675, 1.0)[0], denoise)[1]
        elif scheduler_name == "vp":
            sigmas = self.get_denoised_sigmas(_VPScheduler.get_sigmas(self, steps, 14.0, 0.05, 0.075)[0], denoise)[1]
        elif scheduler_name in comfy.samplers.KSampler.SCHEDULERS:
            sigmas = _BasicScheduler.get_sigmas(self, model, scheduler_name, steps, denoise)[0]
        else:
            defaults = self.get_custom_scheduler_defaults(scheduler_name)
            sigmas = self.get_denoised_sigmas(self.get_custom_class_sigmas(scheduler_name, steps, *defaults.values())[0], denoise)[1]

        return sigmas

    def get_sampler(self, sampler_name):
        sampler = comfy.samplers.sampler_object(sampler_name)
        return (sampler,)

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
