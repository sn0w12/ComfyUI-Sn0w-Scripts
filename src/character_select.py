import os
import json
from .sn0w import ConfigReader

class CharacterSelectNode:
    # Initialize class variables
    character_dict = {}
    final_character_dict = {}

    @classmethod
    def initialize(cls):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        if os.path.basename(dir_path) == "src":
            dir_path = os.path.dirname(dir_path)
        
        cls.load_characters(dir_path)

    @classmethod
    def load_characters(cls, dir_path):
        json_path = os.path.join(dir_path, 'characters.json')
        with open(json_path, 'r') as file:
            character_data = json.load(file)

        custom_json_path = os.path.join(dir_path, 'custom_characters.json')
        if os.path.exists(custom_json_path):
            with open(custom_json_path, 'r') as file:
                custom_character_data = json.load(file)
                for custom_character in custom_character_data:
                    for character in character_data:
                        if custom_character['name'] == character['name']:
                            character['prompt'] += ", " + custom_character['prompt']
                            break
                    else:
                        character_data.append(custom_character)

        cls.character_dict = {character['name']: character for character in character_data}

        if ConfigReader.get_setting("sn0w.SortBySeries", False):
            cls.final_character_dict = {name: cls.character_dict[name] for name in sorted(cls.character_dict, key=cls.extract_series_name)}
        else:
            cls.final_character_dict = {name: cls.character_dict[name] for name in sorted(cls.character_dict)}

    @staticmethod
    def extract_series_name(character_name):
        return character_name.split('(')[-1].split(')')[0].strip()

    @classmethod
    def INPUT_TYPES(cls):
        if not cls.final_character_dict:  # Check if initialization is needed
            cls.initialize()
        character_names = ['None'] + list(cls.final_character_dict.keys())
        return {
            "required": {
                "character": (character_names, ),
                "character_strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 100.0, "step": 0.05, "round": 0.01}),
                "character_prompt": ("BOOLEAN", {"default": False}),
                "xl": ("BOOLEAN", {"default": False}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "BOOLEAN")
    RETURN_NAMES = ("CHARACTER STRING", "CHARACTER PROMPT", "XL")
    FUNCTION = "find_associated_string"
    CATEGORY = "sn0w"
        
    def find_associated_string(self, character, character_strength, character_prompt, xl):
        char_item = self.character_dict.get(character)
        if char_item:
            associated_string = char_item['associated_string']
            prompt = char_item['prompt'] if character_prompt else ""
            strength_part = f":{character_strength}" if character_strength != 1 else ""

            if associated_string:
                return (f"({associated_string}{strength_part}), ", prompt, xl,)
            else:
                return ("", prompt, xl,)

        return ("", "", "")