import folder_paths
from nodes import LoraLoader

class LoraLoraXLNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": ("MODEL",),
                "clip": ("CLIP", ),
                "lora": (['None'] + folder_paths.get_filename_list("loras_xl"), ),
                "lora_strength": ("FLOAT", {"default": 1.0, "min": -10.0, "max": 10.0, "step": 0.01}),
            },
        }

    RETURN_TYPES = ("MODEL", "CLIP",)
    RETURN_NAMES = ("MODEL", "CLIP",)
    FUNCTION = "process_lora_strength"
    CATEGORY = "sn0w"
    OUTPUT_NODE = True

    def process_lora_strength(self, model, clip, lora, lora_strength):
        lora_loader = LoraLoader()
        full_loras_list = folder_paths.get_filename_list("loras")
        # Find the full path of the lora
        full_lora_path = next((full_path for full_path in full_loras_list if lora in full_path), None)
        modified_model, modified_clip = lora_loader.load_lora(model, clip, full_lora_path, lora_strength, lora_strength)
        return (modified_model, modified_clip, )
