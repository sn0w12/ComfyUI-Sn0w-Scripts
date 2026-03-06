import os
import re
import folder_paths

from nodes import LoraLoader
from ..sn0w import Logger, Utility, ConfigReader


class LoadLoraFolderNode:
    """
    Automatically load loras from based on a prompt and a specified folder
    """

    logger = Logger()

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": ("MODEL",),
                "clip": ("CLIP",),
                "prompt": ("STRING", {"default": ""}),
                "folders": ("STRING", {"default": "character:1,concept"}),
                "lora_strength": ("FLOAT", {"default": 1.0, "min": -10.0, "max": 10.0, "step": 0.01}),
                "separator": ("STRING", {"default": ", "}),
            },
        }

    RETURN_TYPES = (
        "MODEL",
        "CLIP",
    )
    RETURN_NAMES = (
        "MODEL",
        "CLIP",
    )
    FUNCTION = "find_and_apply_lora"
    CATEGORY = "sn0w/lora"

    def clean_string(self, input_string):
        cleaned_string = input_string.replace(r"\(", "").replace(r"\)", "")
        cleaned_string = re.sub(r"[:]+(\d+(\.\d+)?)?", "", cleaned_string)
        cleaned_string = re.sub(r",\s*$", "", cleaned_string.strip())
        cleaned_string = input_string.replace("(", "").replace(")", "").replace("\\", "")
        return cleaned_string.lower()

    def normalize_folder_name(self, folder_name):
        return folder_name.strip().replace("\\", "/").lower()

    def parse_folders(self, folder_string):
        master_folder = None
        include_folders = {}
        exclude_folders = set()
        folder_specs = folder_string.split(",")

        for spec in folder_specs:
            parts = spec.split(":")
            folder_name = self.normalize_folder_name(parts[0])

            if folder_name.startswith("*"):
                master_folder = folder_name[1:]  # Remove the '*' to get the master folder name
            elif folder_name.startswith("-"):
                exclude_folder = folder_name[1:]  # Remove the '-' to get the folder name to exclude
                exclude_folders.add(exclude_folder)
            else:
                max_count = int(parts[1]) if len(parts) > 1 else None
                include_folders[folder_name] = max_count

        return master_folder, include_folders, exclude_folders

    def find_and_apply_lora(self, model, clip, prompt, folders, lora_strength, separator):
        # Set default prompt if None provided
        if prompt is None:
            prompt = ""
            self.logger.log("No prompt provided", "WARNING")

        # Clean and split the prompt into parts
        prompt_parts = [self.clean_string(part) for part in prompt.split(separator)]
        model_type = Utility.get_model_type_simple(model)

        # Retrieve and filter Lora file paths
        full_lora_paths = folder_paths.get_filename_list("loras")

        try:
            if model_type == "SD15":
                filtered_lora_paths = folder_paths.get_filename_list("loras_15")
            elif model_type == "SDXL":
                filtered_lora_paths = folder_paths.get_filename_list("loras_xl")
            elif model_type == "SD3":
                filtered_lora_paths = folder_paths.get_filename_list("loras_3")
            else:
                filtered_lora_paths = folder_paths.get_filename_list("loras_vd")
        except Exception:
            self.logger.log(
                f'Correct lora folder path for "{model_type}" doesnt exist. Please add the required lora path to extra_model_paths.yaml',
                "WARNING",
            )
            filtered_lora_paths = full_lora_paths

        master_folder, include_folders, exclude_folders = self.parse_folders(folders)

        # Include only paths in the master folder, if specified
        if master_folder:
            filtered_lora_paths = [
                path for path in filtered_lora_paths if master_folder in self.normalize_folder_name(path)
            ]

        # Filter paths to include and exclude specific folders in a single pass
        lora_paths = [
            path
            for path in filtered_lora_paths
            if any(folder in self.normalize_folder_name(path) for folder in include_folders)
            and not any(exclude in self.normalize_folder_name(path) for exclude in exclude_folders)
        ]

        max_distance = int(ConfigReader.get_setting("sn0w.LoraSettings.LoraFolderMinDistance", 5))
        self.logger.log("Max Distance: " + str(max_distance), "DEBUG")

        # Pre-build a filename -> full_path lookup to avoid a nested search loop
        full_path_lookup = {os.path.split(p)[-1].lower(): p for p in full_lora_paths}

        # Pre-process lora_paths once: resolve filenames, display names, and full paths
        lora_entries = [
            (lora_filename, lora_filename.replace(".safetensors", "").replace("_", " "), full_path)
            for lora_path in lora_paths
            for lora_filename in (os.path.split(lora_path)[-1].lower(),)
            if (full_path := full_path_lookup.get(lora_filename)) is not None
        ]

        # Find the single best matching Lora candidate per prompt part
        best_candidates = {}
        for prompt_part in prompt_parts:
            for lora_filename, processed_name, full_path in lora_entries:
                if prompt_part not in processed_name:
                    continue
                distance = Utility.levenshtein_distance(prompt_part, processed_name)
                self.logger.log(f"Processing: Distance: {distance} Lora: {lora_filename} Tag: {prompt_part}", "DEBUG")
                if distance > max_distance:
                    continue
                if prompt_part not in best_candidates or distance < best_candidates[prompt_part]["distance"]:
                    best_candidates[prompt_part] = {"full_path": full_path, "distance": distance}
                    self.logger.log(f"Final: Distance: {distance} Lora: {lora_filename} Tag: {prompt_part}", "DEBUG")

        # Load the best candidate Lora for each prompt part
        loaded_loras = set()
        for prompt_part, candidate in best_candidates.items():
            folder_name = self.normalize_folder_name(os.path.dirname(candidate["full_path"]))
            # Load Lora if not already loaded and within the allowed number per folder
            if candidate["full_path"] not in loaded_loras and (
                folder_name not in include_folders or len(loaded_loras) < include_folders[folder_name]
            ):
                self.logger.log(f"Loading Lora: {os.path.split(candidate['full_path'])[-1]}", "INFORMATIONAL")
                model, clip = LoraLoader().load_lora(model, clip, candidate["full_path"], lora_strength, lora_strength)
                loaded_loras.add(candidate["full_path"])

        if not best_candidates:
            self.logger.log("No matching Lora found for any tags.", "INFORMATIONAL")

        return (model, clip)
