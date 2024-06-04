import os
import folder_paths
from nodes import LoraLoader
from pathlib import Path
from ..sn0w import Logger, ConfigReader

def generate_lora_node_class(lora_type, required_folders = None):
    class DynamicLoraNode:
        logger = Logger()

        @classmethod
        def INPUT_TYPES(cls):
            try:
                # Get the list of filenames based on the lora_type
                loras = folder_paths.get_filename_list(lora_type)
            except:
                loras = "ERROR"
                cls.logger.log(f"Folder path: {lora_type} doesnt exist.", "ERROR")
            
            # Normalize the paths and sort them alphabetically
            sorted_loras = sorted(loras, key=lambda p: [part.lower() for part in Path(p).parts])
            
            if required_folders is not None:
                # Normalize required_folders to handle subdirectory paths correctly
                normalized_required_folders = [str(Path(folder)).lower() for folder in required_folders]

                # Filter the sorted list to include paths that contain any of the required folder names
                filtered_sorted_loras = [
                    lora for lora in sorted_loras
                    if any(required_folder in str(Path(lora)).lower() for required_folder in normalized_required_folders)
                ]
            else:
                filtered_sorted_loras = sorted_loras

            favourite_loras = ConfigReader.get_setting("sn0w.FavouriteLoras", [])
            # Create an empty list to store the prioritized list
            prioritized_loras = []

            # Iterate through filtered loras
            for lora in filtered_sorted_loras:
                # Check for partial match (case-insensitive) with any favorite lora
                if any(favorite_lora.lower() in lora.lower() for favorite_lora in favourite_loras):
                    # Add the matching lora to the prioritized list
                    prioritized_loras.append(lora)
                    # Remove the matching lora from filtered_sorted_loras to avoid duplicates
                    filtered_sorted_loras.remove(lora)

            # Append the remaining filtered loras to the prioritized list
            prioritized_loras.extend(filtered_sorted_loras)

            return {
                "required": {
                    "model": ("MODEL",),
                    "clip": ("CLIP",),
                    "lora": (['None'] + prioritized_loras,),
                    "lora_strength": ("FLOAT", {"default": 1.0, "min": -10.0, "max": 10.0, "step": 0.01}),
                },
            }

        RETURN_TYPES = ("MODEL", "CLIP",)
        RETURN_NAMES = ("MODEL", "CLIP",)
        FUNCTION = "find_lora"
        CATEGORY = "sn0w/lora"
        OUTPUT_NODE = True

        def find_lora(self, model, clip, lora, lora_strength):
            if lora == "None":
                return (model, clip,)

            lora_loader = LoraLoader()
            full_loras_list = folder_paths.get_filename_list("loras")
            full_lora_path = next((full_path for full_path in full_loras_list if lora in full_path), None)
            modified_model, modified_clip = lora_loader.load_lora(model, clip, full_lora_path, lora_strength, lora_strength)
            return (modified_model, modified_clip, )

    return DynamicLoraNode
