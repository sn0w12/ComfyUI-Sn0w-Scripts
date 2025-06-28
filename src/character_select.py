import os
import json
import random

from ..sn0w import ConfigReader, Logger, Utility

# File paths
CHARACTER_FILE_PATH = "web/settings/characters.json"
CUSTOM_CHARACTER_FILE_PATH = "web/settings/custom_characters.json"


class CharacterSelectNode:
    """
    Node that lets a user select a character and then returns the character and character prompt
    """

    character_dict = {}
    final_character_dict = {}
    final_characters = []
    cached_sorting_setting = ConfigReader.get_setting("sn0w.CharacterSettings.SortCharactersBy", "alphabetical")
    cached_default_character_setting = ConfigReader.get_setting(
        "sn0w.CharacterSettings.DisableDefaultCharacters", False
    )
    last_character = ""
    favorites = ConfigReader.get_setting("SyntaxHighlighting.favorites", [])

    logger = Logger()

    @classmethod
    def initialize(cls):
        dir_path = cls.get_base_dir()

        cls.load_characters(dir_path)

    @classmethod
    def get_base_dir(cls):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        if os.path.basename(dir_path) == "src":
            dir_path = os.path.dirname(dir_path)
        return dir_path

    @classmethod
    def check_initialize(cls):
        if not cls.final_characters or cls.cached_default_character_setting != ConfigReader.get_setting(
            "sn0w.CharacterSettings.DisableDefaultCharacters", False
        ):
            cls.cached_default_character_setting = ConfigReader.get_setting(
                "sn0w.CharacterSettings.DisableDefaultCharacters", False
            )
            cls.initialize()
        elif cls.cached_sorting_setting != ConfigReader.get_setting(
            "sn0w.CharacterSettings.SortCharactersBy", "alphabetical"
        ):
            cls.sort_characters()

    @classmethod
    def load_characters(cls, dir_path):
        character_data = []
        if not cls.cached_default_character_setting:
            json_path = os.path.join(dir_path, CHARACTER_FILE_PATH)
            with open(json_path, "r", encoding="utf-8") as file:
                character_data = json.load(file)

        custom_json_path = os.path.join(dir_path, CUSTOM_CHARACTER_FILE_PATH)
        if not os.path.exists(custom_json_path):
            cls.logger.log(
                f"Custom character file doesn't exist. Please create the json file at: {custom_json_path}", "WARNING"
            )
        else:
            with open(custom_json_path, "r", encoding="utf-8") as file:
                custom_character_data = json.load(file)
                for custom_character in custom_character_data:
                    for character in character_data:
                        if custom_character["name"] == character["name"]:
                            character["associated_string"] += ", " + custom_character["associated_string"]
                            character["prompt"] += ", " + custom_character["prompt"]
                            break
                    else:
                        character_data.append(custom_character)

        cls.character_dict = {character["name"]: character for character in character_data}

        cls.sort_characters(True)

    @staticmethod
    def extract_series_name(character_name):
        series = character_name.split("(")[-1].split(")")[0].strip()
        if character_name == series:
            Logger().log(f"{character_name} has no series name.", "DEBUG")
        return series

    @classmethod
    def sort_characters(cls, force_sort=False):
        current_sorting_setting = ConfigReader.get_setting("sn0w.CharacterSettings.SortCharactersBy", "alphabetical")
        if current_sorting_setting != cls.cached_sorting_setting or force_sort:
            if current_sorting_setting == "series":
                cls.final_character_dict = {
                    name: cls.character_dict[name] for name in sorted(cls.character_dict, key=cls.extract_series_name)
                }
            if current_sorting_setting == "alphabetical":
                cls.final_character_dict = {name: cls.character_dict[name] for name in sorted(cls.character_dict)}

            cls.cached_sorting_setting = current_sorting_setting

        favorite_names = []
        non_favorite_names = []

        for name in cls.final_character_dict.keys():
            if name in cls.favorites:
                favorite_names.append(name)
            else:
                non_favorite_names.append(name)

        ordered_characters = {}
        for fav_name in favorite_names:
            ordered_characters[fav_name] = cls.final_character_dict[fav_name]

        for name in non_favorite_names:
            ordered_characters[name] = cls.final_character_dict[name]

        cls.final_characters = list(ordered_characters.keys())

    @classmethod
    def INPUT_TYPES(cls):
        cls.check_initialize()
        character_names = ["None"] + list(cls.final_characters) + ["SN0W_CHARACTER_SELECTOR"]
        return {
            "required": {
                "character": (character_names,),
                "character_strength": (
                    "FLOAT",
                    {"default": 1.0, "min": 0.0, "max": 100.0, "step": 0.05, "round": 0.01},
                ),
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
        elif character == "None" or character == "SN0W_CHARACTER_SELECTOR":
            return ("", "")
        else:
            char_item = self.final_character_dict.get(character)

        self.last_character = char_item
        character_name = ""
        prompt = ""

        if char_item:
            character_name = char_item["associated_string"]
            prompt = char_item["prompt"] if character_prompt else ""
            strength_part = f":{character_strength}" if character_strength != 1 else None

            if character_name:
                if strength_part is not None:
                    character_name = f"({character_name}{strength_part}), "
                else:
                    character_name = f"{character_name}, "

        return (character_name, prompt)

    def select_random_character(self):
        # Fetching the exclusion settings
        exclude_characters = ConfigReader.get_setting("sn0w.CharacterSettings.ExcludedRandomCharacters", False)
        if exclude_characters is False:
            random_character_name = random.choice(list(self.final_character_dict.keys()))
            char_item = self.final_character_dict[random_character_name]
            self.logger.log("Random Character: " + str(char_item["name"]), "INFORMATIONAL")
            return char_item

        favourite_characters = ConfigReader.get_setting("sn0w.FavouriteCharacters", [])
        if favourite_characters == []:
            self.logger.log("No valid characters found based on the specified criteria.", "WARNING")
            return ""

        # Filter the characters by excluding the ones in the exclusion list
        filtered_characters = {
            name: char for name, char in self.final_character_dict.items() if name in favourite_characters
        }

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

        # Handling the case where no characters meet the criteria
        self.logger.log("No valid characters found based on the specified criteria.", "WARNING")
        return ""
