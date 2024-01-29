import os
import json

class CharacterSelectNode:
    @classmethod
    def INPUT_TYPES(cls):
        # Get the directory of the current script
        dir_path = os.path.dirname(os.path.realpath(__file__))
        # Construct the full path to the JSON file
        json_path = os.path.join(dir_path, 'characters.json')

        # Load character data from a JSON file
        with open(json_path, 'r') as file:
            character_data = json.load(file)

        # Extracting only the character names for the input list
        character_names = ['None'] + [character['name'] for character in character_data]

        return {
            "required": {
                "character": (character_names, ),
                "character_strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 100.0, "step":0.05, "round": 0.01}),
                "character_pronpt": ("BOOLEAN", {"default": False},),
            },
        }

    RETURN_TYPES = ("STRING","STRING",)
    RETURN_NAMES = ("CHARACTER STRING","CHARACTER PROMPT",)
    FUNCTION = "find_associated_string"
    CATEGORY = "sn0w"
        
    def find_associated_string(self, character, character_strength, character_pronpt):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        json_path = os.path.join(dir_path, 'characters.json')

        with open(json_path, 'r') as file:
            character_data = json.load(file)

        for char_item in character_data:
            if char_item['name'] == character:
                if character_strength == 1:
                    if(character_pronpt):
                        return (char_item['associated_string'], char_item['prompt'], )
                    else:
                        return (char_item['associated_string'], )
                else:
                    if(character_pronpt):
                        return (f"({char_item['associated_string']}:{character_strength})", char_item['prompt'], )
                    else:
                        return (f"({char_item['associated_string']}:{character_strength})", )

        return (None,)  # Return a tuple if character not found
