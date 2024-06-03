import os
import re
import time
import folder_paths
from nodes import LoraLoader
from ..sn0w import Logger, Utility, ConfigReader

class LoadLoraFolderNode:
    logger = Logger()

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": ("MODEL",),
                "clip": ("CLIP", ),
                "prompt": ("STRING", {"default": ""}),
                "folders": ("STRING", {"default": "character:1,concept"}),
                "lora_strength": ("FLOAT", {"default": 1.0, "min": -10.0, "max": 10.0, "step": 0.01}),
                "separator": ("STRING", {"default": ", "}),
            },
        }

    RETURN_TYPES = ("MODEL", "CLIP",)
    RETURN_NAMES = ("MODEL", "CLIP",)
    FUNCTION = "find_and_apply_lora"
    CATEGORY = "sn0w/lora"

    def clean_string(self, input_string):
        cleaned_string = input_string.replace(r'\(', '').replace(r'\)', '')
        cleaned_string = re.sub(r'[:]+(\d+(\.\d+)?)?', '', cleaned_string)
        cleaned_string = re.sub(r',\s*$', '', cleaned_string.strip())
        cleaned_string = input_string.replace('(', '').replace(')', '').replace('\\', '')
        return cleaned_string.lower()

    def normalize_folder_name(self, folder_name):
        return folder_name.strip().replace('\\', '/').lower()

    def parse_folders(self, folder_string):
        master_folder = None
        include_folders = {}
        exclude_folders = set()
        folder_specs = folder_string.split(',')

        for spec in folder_specs:
            parts = spec.split(':')
            folder_name = self.normalize_folder_name(parts[0])

            if folder_name.startswith('*'):
                master_folder = folder_name[1:]  # Remove the '*' to get the master folder name
            elif folder_name.startswith('-'):
                exclude_folder = folder_name[1:]  # Remove the '-' to get the folder name to exclude
                exclude_folders.add(exclude_folder)
            else:
                max_count = int(parts[1]) if len(parts) > 1 else None
                include_folders[folder_name] = max_count

        return master_folder, include_folders, exclude_folders

    def find_and_apply_lora(self, model, clip, prompt, folders, lora_strength, separator):
        # Set default prompt if None provided
        if prompt is None:
            prompt = ''
            self.logger.log("No prompt provided", "WARNING")
        
        # Clean and split the prompt into parts
        prompt_parts = [self.clean_string(part) for part in prompt.split(separator)]
        model_type = Utility.get_model_type(model)

        # Retrieve and filter Lora file paths
        full_lora_paths = folder_paths.get_filename_list("loras")
        if model_type == "BaseModel":
            filtered_lora_paths = folder_paths.get_filename_list("loras_15")
        elif model_type == "SDXL":
            filtered_lora_paths = folder_paths.get_filename_list("loras_xl")
        else:
            filtered_lora_paths = folder_paths.get_filename_list("loras_vd")
        master_folder, include_folders, exclude_folders = self.parse_folders(folders)

        # Include only paths in the master folder, if specified
        if master_folder:
            filtered_lora_paths = [path for path in filtered_lora_paths if master_folder in self.normalize_folder_name(path)]

        # Further filter paths to include and exclude specific folders
        lora_paths = [path for path in filtered_lora_paths if any(folder in self.normalize_folder_name(path) for folder in include_folders)]
        lora_paths = [path for path in lora_paths if not any(exclude in self.normalize_folder_name(path) for exclude in exclude_folders)]

        lora_candidates = {}
        loaded_loras = set()
        lora_found = False

        max_distance = int(ConfigReader.get_setting('sn0w.LoraFolderMinDistance', 5))
        self.logger.log("Max Distance: " + str(max_distance), "DEBUG")

        # Match prompt parts with Lora filenames
        for prompt_part in prompt_parts:
            for lora_path in lora_paths:
                lora_filename = os.path.split(lora_path)[-1].lower()
                # Clean up the filename for matching
                processed_lora_filename = lora_filename.replace(".safetensors", "").replace("_", " ")
                
                # Check if prompt part matches the cleaned filename
                if prompt_part in processed_lora_filename:
                    distance = Utility.levenshtein_distance(prompt_part, processed_lora_filename)
                    self.logger.log("Processing: Distance: " + str(distance) + " Lora: " + lora_filename + " Tag: " + prompt_part, "DEBUG")
                    # Store matching Loras if within acceptable distance
                    for full_path in full_lora_paths:
                        if lora_filename in full_path.lower() and distance <= max_distance:
                            if prompt_part not in lora_candidates:
                                lora_candidates[prompt_part] = []
                            lora_candidates[prompt_part].append({'full_path': full_path, 'distance': distance})
                            self.logger.log("Final: Distance: " + str(distance) + " Lora: " + lora_filename + " Tag: " + prompt_part, "DEBUG")
                            break

        # Load the best candidate Lora for each prompt part
        for prompt_part, candidates in lora_candidates.items():
            if candidates:
                lora_found = True
                selected_candidate = min(candidates, key=lambda x: x['distance'])
                folder_name = self.normalize_folder_name(os.path.dirname(selected_candidate['full_path']))
                # Load Lora if not already loaded and within the allowed number per folder
                if selected_candidate['full_path'] not in loaded_loras and (folder_name not in include_folders or len(loaded_loras) < include_folders[folder_name]):
                    self.logger.log(f"Loading Lora: {os.path.split(selected_candidate['full_path'])[-1]}", "INFORMATIONAL")
                    model, clip = LoraLoader().load_lora(model, clip, selected_candidate['full_path'], lora_strength, lora_strength)
                    loaded_loras.add(selected_candidate['full_path'])
        
        if not lora_found:
            self.logger.log(f"No matching Lora found for any tags.", "INFORMATIONAL")

        return (model, clip)
