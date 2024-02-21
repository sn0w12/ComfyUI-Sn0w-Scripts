import os
import json

class CharacterSelectNode:
    # Get the directory of the current file
    dir_path = os.path.dirname(os.path.realpath(__file__))
    # Check if the last part of the path is 'src' and adjust the path accordingly
    if os.path.basename(dir_path) == "src":
        dir_path = os.path.dirname(dir_path)

    # Construct the path to the 'characters.json' file
    json_path = os.path.join(dir_path, 'characters.json')
    # Load character data from the JSON file
    with open(json_path, 'r') as file:
        character_data = json.load(file)

    # Attempt to load 'custom_characters.json' and merge its contents
    custom_json_path = os.path.join(dir_path, 'custom_characters.json')
    if os.path.exists(custom_json_path):
        with open(custom_json_path, 'r') as file:
            custom_character_data = json.load(file)
            if custom_character_data:  # Check if the custom data is not empty
                # Merge custom character data, prioritizing existing data in character_data
                for custom_character in custom_character_data:
                    if custom_character['name'] not in [character['name'] for character in character_data]:
                        character_data.append(custom_character)
                        
    # Create a dictionary mapping character names to their data
    character_dict = {character['name']: character for character in character_data}

    @classmethod
    def INPUT_TYPES(cls):
        character_names = ['None'] + sorted(cls.character_dict.keys())
        return {
            "required": {
                "character": (character_names, ),
                "character_strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 100.0, "step": 0.05, "round": 0.01}),
                "character_prompt": ("BOOLEAN", {"default": False}),
                "xl": ("BOOLEAN", {"default": False},),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "BOOLEAN",)
    RETURN_NAMES = ("CHARACTER STRING", "CHARACTER PROMPT", "XL",)
    FUNCTION = "find_associated_string"
    CATEGORY = "sn0w"
        
    def find_associated_string(self, character, character_strength, character_prompt, xl):
        char_item = self.character_dict.get(character)
        if char_item:
            associated_string = char_item['associated_string']
            prompt = char_item['prompt'] if character_prompt else ""
            strength_part = f":{character_strength}" if character_strength != 1 else None

            if associated_string != "":
                if strength_part:
                    return (f"({associated_string}{strength_part}), ", prompt, xl,)
                else:
                    return (f"{associated_string}, ", prompt, xl,)
            else:
                return ("", prompt, xl,)

        return ("None", "None", "None")
