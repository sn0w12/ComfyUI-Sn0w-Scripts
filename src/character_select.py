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

    cached_default_character_setting = ConfigReader.get_setting(
        "sn0w.CharacterSettings.DisableDefaultCharacters", False
    )
    character_dict = {}
    last_character = ""
    logger = Logger()

    @classmethod
    def get_base_dir(cls):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        if os.path.basename(dir_path) == "src":
            dir_path = os.path.dirname(dir_path)
        return dir_path

    @classmethod
    def INPUT_TYPES(cls):
        dir_path = cls.get_base_dir()
        filtered_character_names = CharacterLoader.get_filtered_character_dict(
            dir_path,
            include_default=not ConfigReader.get_setting("sn0w.CharacterSettings.DisableDefaultCharacters", False),
        )
        cls.character_dict = filtered_character_names
        character_names = ["None"] + list(filtered_character_names.keys()) + ["SN0W_CHARACTER_SELECTOR"]
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
            char_item = self.character_dict.get(character)

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
            random_character_name = random.choice(list(self.character_dict.keys()))
            char_item = self.character_dict[random_character_name]
            self.logger.log("Random Character: " + str(char_item["name"]), "INFORMATIONAL")
            return char_item

        favourite_characters = ConfigReader.get_setting("sn0w.FavouriteCharacters", [])
        if favourite_characters == []:
            self.logger.log("No valid characters found based on the specified criteria.", "WARNING")
            return ""

        # Filter the characters by excluding the ones in the exclusion list
        filtered_characters = {name: char for name, char in self.character_dict.items() if name in favourite_characters}

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
