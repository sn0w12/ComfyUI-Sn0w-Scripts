import os
import folder_paths
from nodes import LoraLoader
from pathlib import Path
from .sn0w import ConfigReader, Logger

def generate_lora_node_class(lora_type, required_folders):
    class DynamicLoraNode:
        @classmethod
        def INPUT_TYPES(cls):
            # Get the list of filenames based on the lora_type
            loras = folder_paths.get_filename_list(lora_type)
            
            # Normalize the paths and sort them alphabetically
            sorted_loras = sorted(loras, key=lambda p: [part.lower() for part in Path(p).parts])
            
            # Normalize required_folders to handle subdirectory paths correctly
            normalized_required_folders = [str(Path(folder)).lower() for folder in required_folders]

            # Filter the sorted list to include paths that contain any of the required folder names
            filtered_sorted_loras = [
                lora for lora in sorted_loras
                if any(required_folder in str(Path(lora)).lower() for required_folder in normalized_required_folders)
            ]

            return {
                "required": {
                    "model": ("MODEL",),
                    "clip": ("CLIP",),
                    "lora": (['None'] + filtered_sorted_loras,),
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
            full_lora_path = next((full_path for full_path in full_loras_list if lora in full_path), None)
            modified_model, modified_clip = lora_loader.load_lora(model, clip, full_lora_path, lora_strength, lora_strength)
            return (modified_model, modified_clip, )

    return DynamicLoraNode
