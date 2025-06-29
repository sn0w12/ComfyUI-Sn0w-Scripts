import json
import os
import random

from ..sn0w import CharacterLoader, ConfigReader, Logger

# File paths
CHARACTER_FILE_PATH = "web/settings/characters.csv"
CUSTOM_CHARACTER_FILE_PATH = "web/settings/custom_characters.json"
VISIBLE_SERIES_PATH = "web/settings/visible_series.json"


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
        include_default = not cls.cached_default_character_setting
        cls.character_dict = CharacterLoader.get_character_dict(dir_path, include_default)
        cls.sort_characters(True)

    @staticmethod
    def extract_series_name(character_name):
        return CharacterLoader.extract_series_name(character_name)

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
        dir_path = cls.get_base_dir()
        filtered_character_names = CharacterLoader.get_filtered_character_list(dir_path, cls.final_character_dict)
        character_names = ["None"] + filtered_character_names + ["SN0W_CHARACTER_SELECTOR"]
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
