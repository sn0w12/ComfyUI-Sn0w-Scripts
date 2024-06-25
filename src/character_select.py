import os
import json
import random
from ..sn0w import ConfigReader, Logger, AnyType, Utility

from server import PromptServer
from aiohttp import web

any = AnyType("*")

routes = PromptServer.instance.routes
API_PREFIX = '/sn0w'

@routes.post(f'{API_PREFIX}/update_characters')
async def handle_update_characters(request):
    CharacterSelectNode.initialize()
    return web.json_response({"status": "ok"})

class CharacterSelectNode:
    # Initialize class variables
    character_dict = {}
    final_character_dict = {}
    final_characters = []
    cached_sorting_setting = ConfigReader.get_setting("sn0w.SortBySeries", False)
    cached_default_character_setting = ConfigReader.get_setting("sn0w.DisableDefaultCharacters", False)
    last_character = ""

    logger = Logger()

    @classmethod
    def initialize(cls):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        if os.path.basename(dir_path) == "src":
            dir_path = os.path.dirname(dir_path)
        
        cls.load_characters(dir_path)

    @classmethod
    def load_characters(cls, dir_path):
        character_data = []
        if (not cls.cached_default_character_setting):
            json_path = os.path.join(dir_path, 'web/settings/characters.json')
            with open(json_path, 'r') as file:
                character_data = json.load(file)

        custom_json_path = os.path.join(dir_path, 'web/settings/custom_characters.json')
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

        cls.sort_characters(True)

    @staticmethod
    def extract_series_name(character_name):
        return character_name.split('(')[-1].split(')')[0].strip()
    
    @classmethod
    def sort_characters(cls, force_sort = False):
        current_sorting_setting = ConfigReader.get_setting("sn0w.SortBySeries", False)
        if current_sorting_setting != cls.cached_sorting_setting or force_sort:
            if current_sorting_setting:
                cls.final_character_dict = {name: cls.character_dict[name] for name in sorted(cls.character_dict, key=cls.extract_series_name)}
            else:
                cls.final_character_dict = {name: cls.character_dict[name] for name in sorted(cls.character_dict)}

            cls.cached_sorting_setting = current_sorting_setting
        
        # Put favourite characters on top
        cls.final_characters = Utility.put_favourite_on_top("sn0w.FavouriteCharacters", cls.final_character_dict)

    @classmethod
    def INPUT_TYPES(cls):
        if not cls.final_characters:  # Check if initialization is needed
            cls.initialize()
        elif cls.cached_default_character_setting != ConfigReader.get_setting("sn0w.DisableDefaultCharacters", False):
            cls.cached_default_character_setting = not cls.cached_default_character_setting
            cls.initialize()
        else:
            cls.sort_characters()
        character_names = ['None'] + list(cls.final_characters)
        return {
            "required": {
                "character": (character_names, ),
                "character_strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 100.0, "step": 0.05, "round": 0.01}),
                "character_prompt": ("BOOLEAN", {"default": False}),
                "random_character": ("BOOLEAN", {"default": False}),
            },
        }
    
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        if kwargs["random_character"]:
            return float("NaN")

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("CHARACTER NAME", "CHARACTER PROMPT")
    FUNCTION = "find_character"
    CATEGORY = "sn0w"
        
    def find_character(self, character, character_strength, character_prompt, random_character):
        if random_character:
            char_item = self.select_random_character()
        elif character == "None":
            return ("", "",)
        else:
            char_item = self.final_character_dict.get(character)

        self.last_character = char_item

        if char_item:
            associated_string = char_item['associated_string']
            prompt = char_item['prompt'] if character_prompt else ""
            strength_part = f":{character_strength}" if character_strength != 1 else ""

            if associated_string:
                return (f"({associated_string}{strength_part}), ", prompt,)
            else:
                return ("", prompt,)

        return ("", "",)
    
    def select_random_character(self):
        # Fetching the exclusion settings
        exclude_characters = ConfigReader.get_setting("sn0w.ExcludedRandomCharacters", False)
        if (exclude_characters == False):
            random_character_name = random.choice(list(self.final_character_dict.keys()))
            char_item = self.final_character_dict[random_character_name]
            self.logger.log("Random Character: " + str(char_item["name"]), "INFORMATIONAL")
            return char_item

        favourite_characters = ConfigReader.get_setting("sn0w.FavouriteCharacters", [])
        if (favourite_characters == []):
            self.logger.log("No valid characters found based on the specified criteria.", "WARNING")
            return ""

        # Filter the characters by excluding the ones in the exclusion list
        filtered_characters = {name: char for name, char in self.final_character_dict.items() if name in favourite_characters}

        # Choosing a random character from the filtered list
        if filtered_characters:
            if len(filtered_characters) == 1:
                random_character_name = random.choice(list(filtered_characters.keys()))
                char_item = filtered_characters[random_character_name]
            else:
                while True:
                    random_character_name = random.choice(list(filtered_characters.keys()))
                    char_item = filtered_characters[random_character_name]
                    if char_item != self.last_character:
                        break

            # Logging the chosen character's name
            self.logger.log("Random Character: " + str(char_item["name"]), "INFORMATIONAL")
            return char_item
        else:
            # Handling the case where no characters meet the criteria
            self.logger.log("No valid characters found based on the specified criteria.", "WARNING")
        
        return ""