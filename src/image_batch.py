import torch

class WAS_Image_Batch:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
            },
            "optional": {
                "images_a": ("IMAGE",),
                "images_b": ("IMAGE",),
                "images_c": ("IMAGE",),
                "images_d": ("IMAGE",),
                # "images_e": ("IMAGE",),
                # "images_f": ("IMAGE",),
                # Theoretically, an infinite number of image input parameters can be added.
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "image_batch"
    CATEGORY = "WAS Suite/Image"

    def _check_image_dimensions(self, tensors, names):
        reference_dimensions = tensors[0].shape[1:]  # Ignore batch dimension
        mismatched_images = [names[i] for i, tensor in enumerate(tensors) if tensor.shape[1:] != reference_dimensions]

        if mismatched_images:
            raise ValueError(f"WAS Image Batch Warning: Input image dimensions do not match for images: {mismatched_images}")

    def image_batch(self, **kwargs):
        batched_tensors = [kwargs[key] for key in kwargs if kwargs[key] is not None]
        image_names = [key for key in kwargs if kwargs[key] is not None]

        if not batched_tensors:
            raise ValueError("At least one input image must be provided.")

        self._check_image_dimensions(batched_tensors, image_names)
        batched_tensors = torch.cat(batched_tensors, dim=0)
        return (batched_tensors,)