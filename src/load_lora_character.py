import os
import json
import re
import folder_paths
from nodes import LoraLoader
from .print_sn0w import print_sn0w

class LoadLoraCharacterNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": ("MODEL",),
                "clip": ("CLIP", ),
                "character": ("STRING", {"default": ""}),
                "xl": ("BOOLEAN", {"default": False},),
                "lora_strength": ("FLOAT", {"default": 1.0, "min": -10.0, "max": 10.0, "step": 0.01}),
            },
        }

    RETURN_TYPES = ("MODEL", "CLIP",)
    RETURN_NAMES = ("MODEL", "CLIP",)
    FUNCTION = "find_and_apply_lora"
    CATEGORY = "sn0w"

    def clean_string(self, input_string):
        # Remove parentheses and escape characters
        cleaned_string = re.sub(r'[\\()]', '', input_string)
        # Remove patterns like ':1.2'
        cleaned_string = re.sub(r':\d+(\.\d+)?', '', cleaned_string)
        # Remove trailing commas
        cleaned_string = re.sub(r',$', '', cleaned_string.strip())
        # Convert to lowercase for case-insensitive comparison
        return cleaned_string.lower()
        
    def find_and_apply_lora(self, model, clip, character, xl, lora_strength):
        dir_path = os.path.dirname(os.path.realpath(__file__)).replace("\\src", "")
        json_path = os.path.join(dir_path, 'characters.json')
        with open(json_path, 'r') as file:
            character_data = json.load(file)

        character_name = None
        cleaned_character = self.clean_string(character)

        for char in character_data:
            cleaned_associated_string = self.clean_string(char['associated_string'])
            if cleaned_associated_string == cleaned_character:
                character_name = char['name']
                break
        
        if character_name:
            lora_loader = LoraLoader()

            full_lora_path = folder_paths.get_filename_list("loras")

            # Select the appropriate lora list based on 'xl'
            lora_paths = folder_paths.get_filename_list("loras_xl" if xl else "loras_15")

            # Extract just the filenames for comparison
            lora_filenames = [path.split('\\')[-1] for path in lora_paths]

            # Find the associated lora path
            lora_path = None
            character_name_parts = character_name.lower().split()

            for filename in lora_filenames:
                if any(part in filename.lower() for part in character_name_parts):
                    # Find the full path in full_lora_path
                    for full_path in full_lora_path:
                        if filename.lower() in full_path.lower():
                            lora_path = full_path
                            break
                    if lora_path:
                        break

            print_sn0w(lora_path)

            if lora_path:
                model, clip = lora_loader.load_lora(model, clip, lora_path, lora_strength, lora_strength)

        return (model, clip, )