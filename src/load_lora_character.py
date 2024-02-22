import os
import json
import re
import folder_paths
from nodes import LoraLoader
from .sn0w import Logger, Utility

class LoadLoraCharacterNode:
    logger = Logger()

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

        min_character_distance = float('inf')

        for char in character_data:
            cleaned_character_lower = cleaned_character.lower().split()
            normalized_character_lower = [self.clean_string(word) for word in cleaned_character_lower]

            if any(word in char['name'].lower() for word in normalized_character_lower):
                cleaned_associated_string = self.clean_string(char['associated_string'])
                distance = Utility.levenshtein_distance(cleaned_associated_string, cleaned_character)
                
                if distance < min_character_distance:
                    self.logger.log(f"Distance: {distance} Name: {char['name']}", "ALL")
                    min_character_distance = distance
                    character_name = char['name']
                    if distance <= 2:
                        break

        if character_name:
            lora_loader = LoraLoader()

            full_lora_path = folder_paths.get_filename_list("loras")

            # Select the appropriate lora list based on 'xl'
            lora_paths = folder_paths.get_filename_list("loras_xl" if xl else "loras_15")

            # Extract just the filenames for comparison
            lora_filenames = [path.split('\\')[-1] for path in lora_paths]

            character_name_lower = character_name.lower()
            character_name_parts = character_name_lower.split()
            closest_match = None
            lowest_distance = float('inf')
            lowest_distance_character_parts = None

            for filename in lora_filenames:
                # Convert filename to lowercase for case-insensitive comparison and remove file extension.
                filename_lower = os.path.splitext(filename.lower())[0]

                if any(part in filename_lower for part in character_name_parts):
                    # Calculate the Levenshtein distance for the full character name as one of the metrics.
                    full_name_distance = Utility.levenshtein_distance(character_name_lower, filename_lower)
                    
                    # Calculate the distances for each part of the character name and get the sum of them.
                    parts_distance = sum(Utility.levenshtein_distance(part, filename_lower) for part in character_name_parts)
                    
                    # Use the minimum of full name distance and parts distance as the total distance.
                    total_distance = min(full_name_distance, parts_distance)

                    self.logger.log("Distance: " + str(total_distance) + " Lora: " + filename + " Name: " + character_name_lower, "ALL")

                    if total_distance < lowest_distance:
                        lowest_distance = total_distance
                        closest_match = filename
                        lowest_distance_character_parts = [character_name_parts]
                        
                        if total_distance == 0:
                            break
                    elif total_distance == lowest_distance:
                        # If the distance is the same as the lowest distance, check the first part of the character name as a final check.
                        parts_distance_final_new = Utility.levenshtein_distance(character_name_parts[0], filename_lower)
                        parts_distance_final_old = Utility.levenshtein_distance(lowest_distance_character_parts[0], filename_lower)
                        if parts_distance_final_new < parts_distance_final_old:
                            parts_distance_final_new = total_distance
                            closest_match = filename

                            self.logger.log("Distance: " + str(parts_distance_final_new) + " Lora: " + filename + " Name: " + character_name_lower, "ALL")

            # Find the full path for the closest match
            if closest_match is not None:
                lora_path = next((full_path for full_path in full_lora_path if closest_match.lower() in full_path.lower()), None)
            else:
                lora_path = None

            if lora_path:
                self.logger.log(f"Loading Character lora: {closest_match}", "GENERAL")
                model, clip = lora_loader.load_lora(model, clip, lora_path, lora_strength, lora_strength)
            else:
                self.logger.log(f"No matching Lora found for the character {character_name}.", "GENERAL")

        return model, clip