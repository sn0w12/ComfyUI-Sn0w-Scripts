import torch
import comfy.utils
from comfy import model_management


class _ImageUpscaleWithModel:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "upscale_model": ("UPSCALE_MODEL",),
                "image": ("IMAGE",),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "upscale"

    CATEGORY = "image/upscaling"

    def upscale(self, upscale_model, image):
        device = model_management.get_torch_device()

        memory_required = model_management.module_size(upscale_model.model)
        memory_required += (
            (512 * 512 * 3) * image.element_size() * max(upscale_model.scale, 1.0) * 384.0
        )  # The 384.0 is an estimate of how much some of these models take, TODO: make it more accurate
        memory_required += image.nelement() * image.element_size()
        model_management.free_memory(memory_required, device)

        upscale_model.to(device)
        in_img = image.movedim(-1, -3).to(device)

        tile = 512
        overlap = 32

        oom = True
        while oom:
            try:
                steps = in_img.shape[0] * comfy.utils.get_tiled_scale_steps(
                    in_img.shape[3], in_img.shape[2], tile_x=tile, tile_y=tile, overlap=overlap
                )
                pbar = comfy.utils.ProgressBar(steps)
                s = comfy.utils.tiled_scale(
                    in_img,
                    lambda a: upscale_model(a),
                    tile_x=tile,
                    tile_y=tile,
                    overlap=overlap,
                    upscale_amount=upscale_model.scale,
                    pbar=pbar,
                )
                oom = False
            except model_management.OOM_EXCEPTION as e:
                tile //= 2
                if tile < 128:
                    raise e

        upscale_model.to("cpu")
        s = torch.clamp(s.movedim(-3, -1), min=0, max=1.0)
        return (s,)


class _ImageScaleBy:
    upscale_methods = ["nearest-exact", "bilinear", "area", "bicubic", "lanczos"]

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
                "upscale_method": (s.upscale_methods,),
                "scale_by": ("FLOAT", {"default": 1.0, "min": 0.01, "max": 8.0, "step": 0.01}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "upscale"

    CATEGORY = "image/upscaling"

    def upscale(self, image, upscale_method, scale_by):
        samples = image.movedim(-1, 1)
        width = round(samples.shape[3] * scale_by)
        height = round(samples.shape[2] * scale_by)
        s = comfy.utils.common_upscale(samples, width, height, upscale_method, "disabled")
        s = s.movedim(1, -1)
        return (s,)


class UpscaleImageBy:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "upscale_by": ("FLOAT", {"default": 2.0, "min": 0.0, "max": 100.0, "step": 0.1, "round": 0.01}),
                "upscale_model": ("UPSCALE_MODEL",),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("IMAGE",)
    FUNCTION = "upscale"

    CATEGORY = "image/upscaling"

    def get_image_size(self, image):
        # Attempt to determine if the image is a batch or a single image
        try:
            # Assume image is a batch and try to get the width of the first image
            width = image[0].shape[1]  # Image batch format: [N, C, H, W]
        except TypeError:
            # If it's not a batch, get the width as a single image
            width = image.shape[1]  # Single image format: [C, H, W]
        return width

    def calculate_upscale_factor(self, original_width, upscaled_width):
        factor_width = upscaled_width / original_width
        return factor_width

    def upscale(self, image, upscale_by, upscale_model):
        upscaler = _ImageUpscaleWithModel()
        scale_image = _ImageScaleBy()

        # Get original image size
        original_size = self.get_image_size(image)
        upscaled_image = upscaler.upscale(upscale_model, image)[0]

        # Get upscaled image size
        upscaled_size = self.get_image_size(upscaled_image)
        actual_upscale_factor = self.calculate_upscale_factor(original_size, upscaled_size)
        desired_scale_factor = upscale_by / actual_upscale_factor

        upscaled_image = scale_image.upscale(upscaled_image, "bicubic", desired_scale_factor)

        return (upscaled_image[0],)
