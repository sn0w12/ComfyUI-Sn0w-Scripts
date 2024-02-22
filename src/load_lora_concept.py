import os
import re
import folder_paths
from nodes import LoraLoader
from .sn0w import Logger, Utility

class LoadLoraConceptNode:
    logger = Logger()

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": ("MODEL",),
                "clip": ("CLIP", ),
                "prompt": ("STRING", {"default": ""}),
                "xl": ("BOOLEAN", {"default": False},),
                "lora_strength": ("FLOAT", {"default": 1.0, "min": -10.0, "max": 10.0, "step": 0.01}),
                "separator": ("STRING", {"default": ", "}),
            },
        }

    RETURN_TYPES = ("MODEL", "CLIP",)
    RETURN_NAMES = ("MODEL", "CLIP",)
    FUNCTION = "find_and_apply_lora"
    CATEGORY = "sn0w"

    def clean_string(self, input_string):
        cleaned_string = re.sub(r'[\\()]', '', input_string)
        cleaned_string = re.sub(r':\d+(\.\d+)?', '', cleaned_string)
        cleaned_string = re.sub(r',$', '', cleaned_string.strip())
        return cleaned_string.lower()
        
    def find_and_apply_lora(self, model, clip, prompt, xl, lora_strength, separator):
        if prompt is None:
            prompt = ''
        prompt_parts = [self.clean_string(part) for part in prompt.split(separator)]

        # Retrieve the full list of lora paths
        full_lora_paths = folder_paths.get_filename_list("loras")
        filtered_lora_paths = folder_paths.get_filename_list("loras_xl" if xl else "loras_15")
        lora_paths = [path for path in filtered_lora_paths if "concept" in path.lower()]

        # Initialize a dictionary to store potential loras for each prompt part
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
                                # Store the candidate with its distance and full path
                                if prompt_part not in lora_candidates:
                                    lora_candidates[prompt_part] = []
                                lora_candidates[prompt_part].append({'full_path': full_path, 'distance': distance})
                                self.logger.print_sn0w("Distance: " + str(distance) + " Lora: " + lora_filename + " Tag: " + prompt_part)
                                break

        # Apply the Lora with the lowest distance for each prompt_part, ensuring no duplicates
        for prompt_part, candidates in lora_candidates.items():
            if candidates:
                selected_candidate = min(candidates, key=lambda x: x['distance'])
                if selected_candidate['full_path'] not in loaded_loras:  # Check if this Lora has already been loaded
                    self.logger.print_sn0w(f"Loading Concept Lora: {os.path.split(selected_candidate['full_path'])[-1]}")
                    model, clip = LoraLoader().load_lora(model, clip, selected_candidate['full_path'], lora_strength, lora_strength)
                    loaded_loras.add(selected_candidate['full_path'])  # Mark this Lora as loaded

        return (model, clip, )