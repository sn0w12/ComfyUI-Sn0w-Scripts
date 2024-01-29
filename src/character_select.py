import os
import json

class CharacterSelectNode:
    dir_path = os.path.dirname(os.path.realpath(__file__)).replace("\\src", "")
    json_path = os.path.join(dir_path, 'characters.json')
    with open(json_path, 'r') as file:
        character_data = json.load(file)
    character_dict = {character['name']: character for character in character_data}

    @classmethod
    def INPUT_TYPES(cls):
        character_names = ['None'] + list(cls.character_dict.keys())
        return {
            "required": {
                "character": (character_names, ),
                "character_strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 100.0, "step": 0.05, "round": 0.01}),
                "character_pronpt": ("BOOLEAN", {"default": False}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING",)
    RETURN_NAMES = ("CHARACTER STRING", "CHARACTER PROMPT",)
    FUNCTION = "find_associated_string"
    CATEGORY = "sn0w"
        
    def find_associated_string(self, character, character_strength, character_pronpt):
        char_item = self.character_dict.get(character)
        if char_item:
            associated_string = char_item['associated_string']
            prompt = char_item['prompt'] if character_pronpt else ""
            strength_part = f":{character_strength}" if character_strength != 1 else ""
            return (f"({associated_string}{strength_part}), ", prompt)
        return (None,)  # Return a tuple if character not found
