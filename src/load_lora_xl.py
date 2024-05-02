import folder_paths
from nodes import LoraLoader
from pathlib import Path

class LoraLoraXLNode:
    @classmethod
    def INPUT_TYPES(cls):
        # Sort the loras_xl list alphabetically
        loras_xl = folder_paths.get_filename_list("loras_xl")
        sorted_loras_xl = sorted(loras_xl, key=lambda p: [part.lower() for part in Path(p).parts])
        
        return {
            "required": {
                "model": ("MODEL",),
                "clip": ("CLIP", ),
                "lora": (['None'] + sorted_loras_xl, ),
                "lora_strength": ("FLOAT", {"default": 1.0, "min": -10.0, "max": 10.0, "step": 0.01}),
            },
        }

    RETURN_TYPES = ("MODEL", "CLIP",)
    RETURN_NAMES = ("MODEL", "CLIP",)
    FUNCTION = "find_lora"
    CATEGORY = "sn0w/lora"
    OUTPUT_NODE = True

    def find_lora(self, model, clip, lora, lora_strength):
        lora_loader = LoraLoader()
        full_loras_list = folder_paths.get_filename_list("loras")
        # Find the full path of the lora
        full_lora_path = next((full_path for full_path in full_loras_list if lora in full_path), None)
        modified_model, modified_clip = lora_loader.load_lora(model, clip, full_lora_path, lora_strength, lora_strength)
        return (modified_model, modified_clip, )
