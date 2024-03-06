from comfy_extras.nodes_upscale_model import ImageUpscaleWithModel
from nodes import ImageScaleBy

class UpscaleImageBy:
    @classmethod
    def INPUT_TYPES(s):
        return {"required":
                    {
                    "image": ("IMAGE", ),
                    "upscale_by": ("FLOAT", {"default": 2.0, "min": 0.0, "max": 100.0, "step":0.1, "round": 0.01}),
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
        upscaler = ImageUpscaleWithModel()
        scale_image = ImageScaleBy()

        # Get original image size
        original_size = self.get_image_size(image)
        upscaled_image = upscaler.upscale(upscale_model, image)[0]

        # Get upscaled image size
        upscaled_size = self.get_image_size(upscaled_image)
        actual_upscale_factor = self.calculate_upscale_factor(original_size, upscaled_size)
        desired_scale_factor = upscale_by / actual_upscale_factor

        upscaled_image = scale_image.upscale(upscaled_image, "bicubic", desired_scale_factor)

        return (upscaled_image[0],)