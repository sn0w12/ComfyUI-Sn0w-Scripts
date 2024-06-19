import folder_paths
from nodes import LoraLoader
from pathlib import Path
from ..sn0w import Logger, Utility

def generate_lora_node_class(lora_type, required_folders = None, combos = 1):
    class DynamicLoraNode:
        logger = Logger()

        @classmethod
        def INPUT_TYPES(cls):
            try:
                # Get the list of filenames based on the lora_type
                loras = folder_paths.get_filename_list(lora_type)
            except:
                cls.logger.log(f"{lora_type} doesnt exist. Please add {lora_type} to extra_model_paths.yaml", "WARNING")
                loras = folder_paths.get_filename_list("loras")
            
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
                
            filtered_sorted_loras = Utility.put_favourite_on_top("sn0w.FavouriteLoras", filtered_sorted_loras)

            inputs = {
                "required": {
                    "model": ("MODEL",),
                    "clip": ("CLIP",),
                },
            }
            if combos == 1:
                inputs["required"][f"lora"] = (['None'] + filtered_sorted_loras,)
                inputs["required"][f"lora_strength"] = ("FLOAT", {"default": 1.0, "min": -10.0, "max": 10.0, "step": 0.01})
            elif combos < 1:
                cls.logger.log("Combos cannot be less than 0", "ERROR")
            else:
                for idx in range(combos):
                    suffix = chr(97 + idx)  # 'a', 'b', 'c', etc.
                    inputs["required"][f"lora_{suffix}"] = (['None'] + filtered_sorted_loras,)
                    inputs["required"][f"lora_strength_{suffix}"] = ("FLOAT", {"default": 1.0, "min": -10.0, "max": 10.0, "step": 0.01})

            return inputs

        RETURN_TYPES = ("MODEL", "CLIP",)
        RETURN_NAMES = ("MODEL", "CLIP",)
        FUNCTION = "find_lora"
        CATEGORY = "sn0w/lora"
        OUTPUT_NODE = True

        def load_lora(self, model, clip, lora, lora_strength):
            if lora == "None":
                return (model, clip,)

            lora_loader = LoraLoader()
            full_loras_list = folder_paths.get_filename_list("loras")
            full_lora_path = next((full_path for full_path in full_loras_list if lora in full_path), None)
            return lora_loader.load_lora(model, clip, full_lora_path, lora_strength, lora_strength)

        def find_lora(self, model, clip, **kwargs):
            if combos == 1:
                model, clip = self.load_lora(model, clip, kwargs["lora"], kwargs["lora_strength"])
            else:
                for idx in range(combos):
                    suffix = chr(97 + idx)
                    model, clip = self.load_lora(model, clip, kwargs[f"lora_{suffix}"], kwargs[f"lora_strength_{suffix}"])
            
            return (model, clip, )

    return DynamicLoraNode
