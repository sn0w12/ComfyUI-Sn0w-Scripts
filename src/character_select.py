import json
import os
import random
import sqlite3
import threading
from typing import TypedDict

from ..sn0w import ConfigReader, Logger


class SeriesInfo(TypedDict):
    series: str
    characters: list[str]


class Character:
    def __init__(self, name: str, prompt: str, copyright: str, clothing: str = "", gender: str = "") -> None:
        self.name = name
        self.prompt = [tag.strip().replace("_", " ") for tag in prompt.split(",") if tag.strip()]
        self.copyright = [tag.strip().replace("_", " ") for tag in copyright.split(",") if tag.strip()]
        self.clothing = [tag.strip().replace("_", " ") for tag in clothing.split(",") if tag.strip()]
        self.gender = gender.strip().replace("_", " ")

    def __str__(self) -> str:
        return f"{self.name}, [{', '.join(self.prompt)}], [{', '.join(self.copyright)}], [{', '.join(self.clothing)}], {self.gender}"


class CharacterDB:
    logger = Logger()

    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "web", "characters", "characters.db")
        self.custom_characters_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..",
            "web",
            "settings",
            "custom_characters.json",
        )
        self.visible_series_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..",
            "web",
            "settings",
            "visible_series.json",
        )

        self.CHAR_DELIMITER = "|"

        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)  # Allow multi-thread access
        self.cursor = self.conn.cursor()
        self.lock = threading.Lock()  # Add lock for thread-safety

        # Validate custom_characters.json structure on initialization
        is_valid, error_msg = self.validate_custom_characters_structure()
        if not is_valid:
            self.logger.log(f"Warning: custom_characters.json validation failed: {error_msg}", "WARNING")

    def build_char_string(self, names_only: bool, copyright: str, *tags: str) -> str:
        """
        Builds a character string by joining the processed copyright and tags with the character delimiter.
        """
        if names_only:
            return self.process_tag(tags[-1]) if tags else self.process_tag(copyright)

        processed_parts = [self.process_tag(copyright)] + [self.process_tag(tag) for tag in tags]
        return self.CHAR_DELIMITER.join(processed_parts)

    def process_tag(self, name: str) -> str:
        return name.replace("_", " ")

    def get_character_names(self, include_default=True, names_only=False) -> list[str]:
        characters = []
        if include_default:
            characters.extend(self.get_default_character_names(names_only=names_only))
        characters.extend(self.get_custom_character_names(names_only=names_only))
        return characters

    def get_character_by_name(self, name: str) -> Character | None:
        if not name:
            return None

        normalized = name.strip().lower()
        if not normalized:
            return None

        custom_character = self._get_custom_character_by_name(normalized)
        if custom_character:
            return custom_character

        return self._get_default_character_by_name(normalized)

    def _get_custom_character_by_name(self, normalized_name: str) -> Character | None:
        if not os.path.exists(self.custom_characters_path):
            return None

        try:
            with open(self.custom_characters_path, "r", encoding="utf-8") as f:
                custom_list = json.load(f)
        except (json.JSONDecodeError, IOError):
            return None

        for char in custom_list:
            raw_name = str(char.get("name", "")).strip()
            if raw_name.lower() != normalized_name:
                continue
            return Character(
                name=raw_name,
                prompt=str(char.get("prompt", "")),
                copyright=str(char.get("copyright", "")),
                clothing=str(char.get("clothing", "")),
                gender=str(char.get("gender", "")),
            )

        return None

    def _get_default_character_by_name(self, normalized_name: str) -> Character | None:
        with self.lock:
            self.cursor.execute(
                """
                SELECT name, prompt, copyright, clothing_tags, gender
                FROM characters
                WHERE lower(name) = ?
                   OR lower(replace(name, '_', ' ')) = ?
                LIMIT 1
                """,
                (normalized_name, normalized_name),
            )
            row = self.cursor.fetchone()

        if not row:
            return None

        db_name, prompt, copyright_text, clothing, gender = row
        return Character(
            name=self.process_tag(db_name),
            prompt=prompt or "",
            copyright=copyright_text or "",
            clothing=clothing or "",
            gender=gender or "",
        )

    def get_custom_character_names(self, names_only=False) -> list[str]:
        if not os.path.exists(self.custom_characters_path):
            return []

        characters = []
        try:
            with open(self.custom_characters_path, "r", encoding="utf-8") as f:
                custom_list = json.load(f)
                for char in custom_list:
                    name = char.get("name", "").strip().lower()
                    copyright = char.get("copyright", "custom").strip().lower()

                    if name:
                        characters.append(self.build_char_string(names_only, copyright, name))
        except (json.JSONDecodeError, IOError):
            return []

        return characters

    def validate_custom_characters_structure(self) -> tuple[bool, str]:
        """
        Validates the structure of custom_characters.json.
        Returns (True, "") if valid, else (False, error_message).
        """
        if not os.path.exists(self.custom_characters_path):
            return False, "File does not exist"

        try:
            with open(self.custom_characters_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON: {e}"
        except IOError as e:
            return False, f"IO Error: {e}"

        if not isinstance(data, list):
            return False, "Root must be a list of objects"

        for i, item in enumerate(data):
            if not isinstance(item, dict):
                return False, f"Item {i} is not a dictionary"

            required_keys = ["name", "prompt", "copyright"]
            for key in required_keys:
                if key not in item:
                    return False, f"Item {i} missing required key '{key}'"
                if not isinstance(item[key], str):
                    return False, f"Item {i} key '{key}' must be a string"

        return True, ""

    @staticmethod
    def _build_copyright_picker(all_characters: list[tuple[int, str, str]]):
        copyright_counts = {}
        for _, _, copyright_text in all_characters:
            if not copyright_text:
                continue
            for part in copyright_text.split(","):
                token = part.strip().lower()
                if not token:
                    continue
                copyright_counts[token] = copyright_counts.get(token, 0) + 1

        def pick_popular_copyright(copyright_text: str) -> str:
            if not copyright_text:
                return ""
            candidates = []
            for part in copyright_text.split(","):
                token = part.strip().lower()
                if token:
                    candidates.append(token)
            if not candidates:
                return ""
            candidates.sort(key=lambda item: (-copyright_counts.get(item, 0), item))
            return candidates[0]

        return pick_popular_copyright

    def load_visible_series(self) -> set[str] | None:
        """
        Load the list of visible series from visible_series.json.
        Returns None if file doesn't exist (meaning show all).
        Returns empty set if file exists but is empty (meaning show none).
        """
        if not os.path.exists(self.visible_series_path):
            return None

        try:
            with open(self.visible_series_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, list):
                return None
            return {s.strip().lower() for s in data if isinstance(s, str) and s.strip()}
        except (json.JSONDecodeError, IOError):
            return None

    def get_visible_series(self) -> list[str] | None:
        """
        Get the current list of visible series.
        Returns None if all series are visible (no filter applied).
        """
        visible = self.load_visible_series()
        if visible is None:
            return None
        return sorted(visible)

    def set_visible_series(self, series_list: list[str] | None) -> bool:
        """
        Set the list of visible series.
        Pass None or empty list to show all series (removes the filter file).
        Returns True on success, False on failure.
        """
        if series_list is None or len(series_list) == 0:
            # Delete the file to show all series
            if os.path.exists(self.visible_series_path):
                try:
                    os.remove(self.visible_series_path)
                    return True
                except IOError:
                    return False
            return True

        try:
            normalized = sorted(set(s.strip().lower() for s in series_list if s.strip()))
            with open(self.visible_series_path, "w", encoding="utf-8") as f:
                json.dump(normalized, f, indent=2)
            return True
        except IOError:
            return False

    def get_default_character_names(self, names_only=False) -> list[str]:
        with self.lock:
            # Load visible series filter early
            visible_series = self.load_visible_series()

            # Fetch all characters once
            self.cursor.execute("SELECT id, name, copyright FROM characters")
            all_characters = self.cursor.fetchall()
            pick_popular_copyright = self._build_copyright_picker(all_characters)

            # Fetch all parent-child relationships in one query
            self.cursor.execute(
                """
                SELECT r.related_tag_id, c.id, c.name
                FROM character_relationships r
                INNER JOIN characters c ON r.tag_id = c.id
                WHERE r.relation_type = 'parent'
                """
            )
            relationship_rows = self.cursor.fetchall()

            # Build a map: parent_id -> list of (child_id, child_name)
            children_map = {}
            child_ids = set()
            for parent_id, child_id, child_name in relationship_rows:
                children_map.setdefault(parent_id, []).append((child_id, child_name))
                child_ids.add(child_id)

            # Process all characters, skipping those that are children (not roots)
            formatted = []
            for char_id, name, copyright_text in all_characters:
                if char_id in child_ids:
                    continue  # This is a child, not a root character

                selected_copyright = pick_popular_copyright(copyright_text)
                if not selected_copyright:
                    continue

                # Filter by visible series if filter is active
                if visible_series is not None and selected_copyright not in visible_series:
                    continue

                children = children_map.get(char_id, [])

                if children:
                    for _, child_name in children:
                        formatted.append(self.build_char_string(names_only, selected_copyright, name, child_name))
                else:
                    formatted.append(self.build_char_string(names_only, selected_copyright, name))

            return formatted

    def get_all_series(self) -> list[SeriesInfo]:
        with self.lock:
            self.cursor.execute("SELECT id, name, copyright FROM characters")
            all_characters = self.cursor.fetchall()
            pick_popular_copyright = self._build_copyright_picker(all_characters)

            series_map = {}
            for _, name, copyright_text in all_characters:
                selected_copyright = pick_popular_copyright(copyright_text)
                if not selected_copyright:
                    continue
                series_map.setdefault(selected_copyright, []).append(self.process_tag(name))

            return [{"series": series_name, "characters": characters} for series_name, characters in sorted(series_map.items())]

    def get_random_character(self, valid_characters: list[str] | None = None) -> Character | None:
        """
        Get a random character from the available characters.
        Optionally, provide a list of valid character strings to choose from.
        The valid_characters should be in the format returned by get_character_names().
        Returns a Character object or None if no characters are available.
        """
        names = self.get_character_names(include_default=True, names_only=True)
        if valid_characters is not None:
            names = [n for n in names if n in valid_characters]
        if not names:
            return None
        selected = random.choice(names)
        return self.get_character_by_name(selected)


class CharacterSelectNode:
    """
    Node that lets a user select a character and then returns the character and character prompt
    """

    cached_default_character_setting = ConfigReader.get_setting("sn0w.CharacterSettings.DisableDefaultCharacters", False)
    character_dict = {}
    last_character = ""
    logger = Logger()
    db = CharacterDB()

    @classmethod
    def get_base_dir(cls):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        if os.path.basename(dir_path) == "src":
            dir_path = os.path.dirname(dir_path)
        return dir_path

    @classmethod
    def INPUT_TYPES(cls):
        filtered_character_names = cls.db.get_character_names(
            include_default=not ConfigReader.get_setting("sn0w.CharacterSettings.DisableDefaultCharacters", False),
        )
        character_names = ["None"] + filtered_character_names + ["SN0W_CHARACTER_SELECTOR"]
        return {
            "required": {
                "character": (character_names,),
                "character_strength": (
                    "FLOAT",
                    {"default": 1.0, "min": 0.0, "max": 100.0, "step": 0.05, "round": 0.01},
                ),
                "random_character": ("BOOLEAN", {"default": False}),
            },
        }

    @classmethod
    def VALIDATE_INPUTS(cls, **kwargs):
        character_strength = kwargs.get("character_strength")

        if character_strength is not None:
            try:
                strength_value = float(character_strength)
                if not (0.0 <= strength_value <= 100.0):
                    return False, "Character Strength must be between 0.0 and 100.0"
            except ValueError:
                return False, "Character Strength must be a valid number"

        return True

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        if kwargs["random_character"]:
            return float("NaN")

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("CHARACTER NAME", "CHARACTER PROMPT")
    FUNCTION = "find_character"
    CATEGORY = "sn0w"

    def escape_parentheses(self, text: str) -> str:
        """
        Escapes parentheses with a single backslash in the resulting string.
        """
        return text.replace("(", "\\(").replace(")", "\\)")

    def find_character(self, character, character_strength, random_character):
        if random_character:
            char_item = self.select_random_character()
        elif character == "None" or character == "SN0W_CHARACTER_SELECTOR":
            return ("", "")
        else:
            char_item = self.db.get_character_by_name(character)

        self.last_character = char_item.name if char_item else ""
        character_name = ""
        prompt = ""

        if char_item:
            character_name = self.escape_parentheses(f"{char_item.name}, {', '.join(char_item.copyright)}")
            prompt = char_item.prompt
            strength_part = f":{character_strength}" if character_strength != 1 else None

            if character_name:
                if strength_part is not None:
                    character_name = f"({character_name}{strength_part})"
                else:
                    character_name = f"{character_name}"

        return (character_name, self.escape_parentheses(", ".join(prompt)))

    def select_random_character(self):
        # Fetching the exclusion settings
        exclude_characters = ConfigReader.get_setting("sn0w.CharacterSettings.ExcludedRandomCharacters", False)
        if exclude_characters is False:
            char_item = self.db.get_random_character()
            self.logger.log("Random Character: " + str(char_item.name), "INFORMATIONAL")
            return char_item

        favourite_characters: list[str] = ConfigReader.get_setting("SyntaxHighlighting.favorites", [])
        if favourite_characters == []:
            self.logger.log("No valid characters found based on the specified criteria.", "WARNING")
            return None

        # Choosing a random character from the filtered list
        if favourite_characters:
            if len(favourite_characters) == 1:
                char_item = self.db.get_random_character(favourite_characters)
            else:
                tries = 0
                while tries < 10:  # Avoid infinite loop, try up to 10 times to find a different character
                    tries += 1
                    char_item = self.db.get_random_character(favourite_characters)
                    if char_item.name != self.last_character:
                        break

            # Logging the chosen character's name
            self.logger.log("Random Character: " + str(char_item.name), "INFORMATIONAL")
            return char_item

        # Handling the case where no characters meet the criteria
        self.logger.log("No valid characters found based on the specified criteria.", "WARNING")
        return None
