import os
import re
import folder_paths
from nodes import LoraLoader
from .sn0w import Logger, Utility

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
                "xl": ("BOOLEAN", {"default": False}),
                "lora_strength": ("FLOAT", {"default": 1.0, "min": -10.0, "max": 10.0, "step": 0.01}),
                "separator": ("STRING", {"default": ", "}),
            },
        }

    RETURN_TYPES = ("MODEL", "CLIP",)
    RETURN_NAMES = ("MODEL", "CLIP",)
    FUNCTION = "find_and_apply_lora"
    CATEGORY = "sn0w/lora"

    def clean_string(self, input_string):
        cleaned_string = input_string.replace(r'\(', '(').replace(r'\)', ')')
        cleaned_string = re.sub(r'[:]+(\d+(\.\d+)?)?', '', cleaned_string)
        cleaned_string = re.sub(r',\s*$', '', cleaned_string.strip())
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

    def find_and_apply_lora(self, model, clip, prompt, folders, xl, lora_strength, separator):
        if prompt is None:
            prompt = ''
        prompt_parts = [self.clean_string(part) for part in prompt.split(separator)]

        # Retrieve paths and apply folder constraints
        full_lora_paths = folder_paths.get_filename_list("loras")
        filtered_lora_paths = folder_paths.get_filename_list("loras_xl" if xl else "loras_15")
        master_folder, include_folders, exclude_folders = self.parse_folders(folders)

        # Filter by master folder if specified
        if master_folder:
            filtered_lora_paths = [path for path in filtered_lora_paths if master_folder in self.normalize_folder_name(path)]

        # Filter by included and excluded folders
        lora_paths = [path for path in filtered_lora_paths if any(folder in self.normalize_folder_name(path) for folder in include_folders)]
        lora_paths = [path for path in lora_paths if not any(exclude in self.normalize_folder_name(path) for exclude in exclude_folders)]

        lora_candidates = {}
        loaded_loras = set()

        for prompt_part in prompt_parts:
            for lora_path in lora_paths:
                lora_filename = os.path.split(lora_path)[-1].lower()
                processed_lora_filename = lora_filename.replace(".safetensors", "").replace("_", " ")

                if prompt_part in processed_lora_filename:
                    distance = Utility.levenshtein_distance(prompt_part, processed_lora_filename)
                    for full_path in full_lora_paths:
                        if lora_filename in full_path.lower():
                            if distance <= 5:
                                if prompt_part not in lora_candidates:
                                    lora_candidates[prompt_part] = []
                                lora_candidates[prompt_part].append({'full_path': full_path, 'distance': distance})
                                self.logger.log("Distance: " + str(distance) + " Lora: " + lora_filename + " Tag: " + prompt_part, "ALL")
                                break

        for prompt_part, candidates in lora_candidates.items():
            if candidates:
                selected_candidate = min(candidates, key=lambda x: x['distance'])
                folder_name = self.normalize_folder_name(os.path.dirname(selected_candidate['full_path']))
                if selected_candidate['full_path'] not in loaded_loras and (folder_name not in include_folders or len(loaded_loras) < include_folders[folder_name]):
                    self.logger.log(f"Loading Lora: {os.path.split(selected_candidate['full_path'])[-1]}", "GENERAL")
                    model, clip = LoraLoader().load_lora(model, clip, selected_candidate['full_path'], lora_strength, lora_strength)
                    loaded_loras.add(selected_candidate['full_path'])
            else:
                self.logger.log(f"No matching Lora found for any tags.", "GENERAL")

        return (model, clip,)
