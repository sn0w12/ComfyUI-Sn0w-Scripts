"""
Module for handling configuration, logging, and various utility functions for the ComfyUI-Sn0w-Scripts project.

Classes:
    ConfigReader: Handles reading and managing configuration settings.
    Logger: Logs messages with different severity levels and colors.
    Utility: Provides static methods for common operations.
    MessageHolder: Manages communication between the JavaScript frontend and Python backend.
"""

import os
import json
import time
import torch
import sqlite3
import threading

from server import PromptServer
from aiohttp import web

import folder_paths


class ConfigReader:
    """
    Handles reading and managing configuration settings for ComfyUI without using the API.

    Methods:
    get_setting(setting_id, default)
        Retrieve a setting value from the configuration file.

    is_comfy_portable()
        Check if comfy is running in portable mode.
    """

    user_directory = folder_paths.get_user_directory()
    SETTINGS_PATH = os.path.join(user_directory, "default/comfy.settings.json")

    @classmethod
    def print_sn0w(cls, message, color="\033[0;35m"):
        """Print a message with a specific color prefix."""
        print(f"{color}[sn0w] \033[0m{message}")

    @staticmethod
    def get_setting(setting_id, default=None):
        """Retrieve a setting value from the configuration file."""
        # Try to read the settings from the determined path
        try:
            with open(ConfigReader.SETTINGS_PATH, "r", encoding="utf-8") as file:
                settings = json.load(file)
            return settings.get(setting_id, default)
        except FileNotFoundError:
            ConfigReader.print_sn0w(
                f"Local configuration file not found at {ConfigReader.SETTINGS_PATH}.", "\033[0;33m"
            )
        except json.JSONDecodeError:
            ConfigReader.print_sn0w(f"Error decoding JSON from {ConfigReader.SETTINGS_PATH}.", "\033[0;31m")

        return default

    @staticmethod
    def set_setting(setting_id: str, value):
        """Set a setting value in the configuration file."""
        # Try to read the existing settings from the determined path
        path = ConfigReader.SETTINGS_PATH

        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as file:
                    settings = json.load(file)
            else:
                settings = {}  # If the file doesn't exist, start with an empty dict

            # If value is None, remove the setting if it exists
            if value is None:
                if setting_id in settings:
                    del settings[setting_id]
            else:
                # Update the setting value
                settings[setting_id] = value

            # Write the updated settings back to the file
            with open(path, "w", encoding="utf-8") as file:
                json.dump(settings, file, indent=4)

            return True

        except FileNotFoundError:
            ConfigReader.print_sn0w(f"Local configuration file not found at {path}.", "\033[0;33m")
        except json.JSONDecodeError:
            ConfigReader.print_sn0w(f"Error decoding JSON from {path}.", "\033[0;31m")
        except IOError as e:
            ConfigReader.print_sn0w(f"Error writing to {path}: {e}", "\033[0;31m")

        return False

    @classmethod
    def validate_settings(cls):
        """Update to new settings values after frontend update."""
        conversion_map = {
            "sn0w.CustomLoraLoaders1.5": "sn0w.CustomLoraLoaders",
            "sn0w.CustomLoraLoadersXL": "sn0w.CustomLoraLoaders.XL",
            "sn0w.CustomLoraLoaders3": "sn0w.CustomLoraLoaders.3",
            "sn0w.TextboxColors": "sn0w.TextboxSettings",
            "sn0w.TextboxGradientColors": "sn0w.TextboxSettings.GradientColors",
            "sn0w.SortLorasBy": "sn0w.LoraSettings.SortLorasBy",
            "sn0w.RemoveLoraPath": "sn0w.LoraSettings.RemoveLoraPath",
            "sn0w.LoraFolderMinDistance": "sn0w.LoraSettings.LoraFolderMinDistance",
            "sn0w.DisableDefaultCharacters": "sn0w.CharacterSettings.DisableDefaultCharacters",
            "sn0w.ExcludedRandomCharacters": "sn0w.CharacterSettings.ExcludedRandomCharacters",
            "sn0w.SortCharactersBy": "sn0w.CharacterSettings.SortCharactersBy",
            "sn0w.TextboxSettings": "SyntaxHighlighting.textbox-colors",
        }

        path = ConfigReader.SETTINGS_PATH
        with open(path, "r", encoding="utf-8") as file:
            settings = json.load(file)

        # Handle favorites migration
        favorite_loras = cls.get_setting("sn0w.FavouriteLoras", [])
        favorite_chars = cls.get_setting("sn0w.FavouriteCharacters", [])

        if favorite_loras or favorite_chars:
            combined_favorites = list(set(favorite_loras + favorite_chars))  # Merge and remove duplicates
            cls.set_setting("SyntaxHighlighting.favorites", combined_favorites)
            cls.set_setting("sn0w.FavouriteLoras", None)  # Remove old setting
            cls.set_setting("sn0w.FavouriteCharacters", None)  # Remove old setting

        # Handle other setting migrations
        for setting in settings:
            if setting in conversion_map:
                setting_value = cls.get_setting(setting)
                if setting_value:
                    cls.set_setting(conversion_map[setting], setting_value)
                    cls.set_setting(setting, None)  # Remove the old setting


# Initialize portable check when the class is defined
ConfigReader.validate_settings()


class Logger:
    """
    Logger class for printing messages with different severity levels and colors.

    Logger levels:
        - EMERGENCY
        - ALERT
        - CRITICAL
        - ERROR
        - WARNING
        - INFORMATIONAL
        - DEBUG

    Methods:
    log(message, level)
        Log a message with a specified severity level.

    print_sigmas_differences(name, sigmas)
        Prints sigmas to terminal.
    """

    PURPLE_TEXT = "\033[0;35m"
    RED_TEXT = "\033[0;31m"
    YELLOW_TEXT = "\033[0;33m"
    GREEN_TEXT = "\033[0;32m"
    RESET_TEXT = "\033[0m"
    PREFIX = "[sn0w] "
    ALWAYS_LOG = ["EMERGENCY", "ALERT", "CRITICAL", "ERROR"]

    enabled_levels = ConfigReader.get_setting("sn0w.LoggingLevel", ["INFORMATIONAL", "WARNING"])

    @classmethod
    def reload_config(cls):
        """Reload the logger configuration settings."""
        cls.enabled_levels = ConfigReader.get_setting("sn0w.LoggingLevel", ["INFORMATIONAL", "WARNING"])

    @classmethod
    def _print_sn0w(cls, message, color):
        """Print a message with a specific color prefix."""
        print(f"{color}{cls.PREFIX}{cls.RESET_TEXT}{message}")

    def log(self, message, level="ERROR"):
        """Log a message with a specified severity level."""
        # Determine the color based on the type of message
        if level.upper() in self.ALWAYS_LOG:
            color = self.RED_TEXT
        elif level.upper() == "WARNING":
            color = self.YELLOW_TEXT
        else:
            color = self.PURPLE_TEXT  # Default color

        # Check if the message's level is in the enabled log levels
        if level.upper() in self.enabled_levels or level.upper() in self.ALWAYS_LOG:
            self._print_sn0w(message, color)

    def print_sigmas_differences(self, name, sigmas):
        """
        Takes a tensor of sigmas and prints each sigma along with the difference to the next sigma
        and the percentage difference to the next sigma.

        Args:
        sigmas (torch.Tensor): A 1D tensor of sigmas with a zero appended at the end.
        """
        if "DEBUG" in self.enabled_levels:
            self._print_sn0w(f"Scheduler: {name}", self.PURPLE_TEXT)
            print("Index | Sigma Value | Difference to Next | % Difference")
            print("-" * 65)

            # Compute the differences
            differences = sigmas[1:] - sigmas[:-1]

            # Iterate over sigmas and differences
            for i in range(len(sigmas) - 1):
                if sigmas[i] != 0:
                    percent_diff = (differences[i] / sigmas[i]) * 100
                else:
                    percent_diff = float("inf")  # To handle division by zero in a meaningful way
                print(f"{i:<5} | {sigmas[i]:<11.4f} | {differences[i]:<18.4f} | {percent_diff:<12.2f}")

            # Print the last sigma value without a difference (since it's the appended zero)
            print(f"{len(sigmas) - 1:<5} | {sigmas[-1]:<11.4f} | {'N/A':<18} | {'N/A':<12}")


class Utility:
    """
    Utility class providing various static methods for common operations.

    Methods:
    levenshtein_distance(s1, s2):
        Calculate the Levenshtein distance between two strings.

    image_batch(**kwargs):
        Concatenate and batch multiple image tensors.

    get_model_type(model_patcher):
        Retrieve the type of the model from the model patcher.

    get_model_type_simple(model_patcher):
        Retrieve a standardized model type from the model patcher.

    put_favourite_on_top(setting, arr):
        Prioritize favorite items in a list based on a setting.

    create_setting_entry(setting_type, setting_value):
        Create a setting entry based on the type and value.

    get_node_output(data, node_id, output_id):
        Get the output of a node from the workflow data.
    """

    logger = Logger()
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

    @staticmethod
    def levenshtein_distance(s1, s2):
        """Calculate the Levenshtein distance between two strings."""
        if len(s1) < len(s2):
            return Utility.levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    @staticmethod
    def _check_image_dimensions(tensors, names):
        """Check if the dimensions of the provided image tensors match."""
        reference_dimensions = tensors[0].shape[1:]  # Ignore batch dimension
        mismatched_images = [names[i] for i, tensor in enumerate(tensors) if tensor.shape[1:] != reference_dimensions]

        if mismatched_images:
            raise ValueError(f"Input image dimensions do not match for images: {mismatched_images}")

    @staticmethod
    def image_batch(**kwargs):
        """Concatenate and batch multiple image tensors."""
        batched_tensors = [tensor for key, tensor in kwargs.items() if tensor is not None]
        image_names = [key for key, tensor in kwargs.items() if tensor is not None]

        if not batched_tensors:
            raise ValueError("At least one input image must be provided.")

        Utility._check_image_dimensions(batched_tensors, image_names)
        batched_tensors = torch.cat(batched_tensors, dim=0)
        return batched_tensors

    @staticmethod
    def get_model_type(model_patcher):
        """Retrieve the type of the model from the model patcher."""
        return model_patcher.model.__class__.__name__

    @staticmethod
    def get_model_type_simple(model_patcher):
        """Retrieve a standardized model type from the model patcher."""
        model_type = Utility.get_model_type(model_patcher)

        if model_type == "BaseModel":
            return "SD15"

        return model_type

    @classmethod
    def put_favourite_on_top(cls, setting, arr):
        """Prioritize favorite items in a list based on a setting."""
        # Convert to a list if its a dictionary
        if isinstance(arr, dict):
            arr = list(arr.keys())

        favourites = ConfigReader.get_setting(setting, None)
        if favourites is None:
            return arr

        prioritized = []
        arr_copy = arr[:]

        # Iterate through the copied array
        for item in arr_copy:
            # Check for full match (case-insensitive) with any favorite
            if any(favourite.lower() in item.lower() for favourite in favourites):
                prioritized.append(item)
                arr.remove(item)

        # Append the remaining items to the prioritized list
        prioritized.extend(arr)
        return prioritized

    @classmethod
    def create_setting_entry(cls, setting_type, setting_value):
        """Create a setting entry based on the type and value."""
        if setting_type == "INT":
            return ("INT", {"default": setting_value[1], "min": setting_value[2], "max": setting_value[3]})
        if setting_type == "FLOAT":
            return (
                "FLOAT",
                {
                    "default": setting_value[1],
                    "min": setting_value[2],
                    "max": setting_value[3],
                    "step": setting_value[4],
                },
            )
        if setting_type == "STRING":
            return ("STRING", {"default": setting_value[1]})
        if setting_type == "BOOLEAN":
            return ("BOOLEAN", {"default": setting_value[1]})
        raise ValueError(f"Unsupported setting type: {setting_type}")

    @classmethod
    def get_node_output(cls, data, node_id, output_id):
        """Get the output of a node from the workflow data."""
        if not data:
            return None

        try:
            workflow = data.get("workflow", {})
            nodes = workflow.get("nodes", [])

            for node in nodes:
                if int(node.get("id")) == int(node_id):
                    for output in node.get("outputs", []):
                        if int(output["slot_index"]) == int(output_id):
                            return output
            return None
        except Exception as e:
            cls.logger.log(f"Error getting node output: {e}", "ERROR")
            return None


class AnyType(str):
    def __ne__(self, __value: object) -> bool:
        return False


class Cancelled(Exception):
    pass


class MessageHolder:
    """
    Communicate between the JavaScript frontend and Python backend.
    """

    stash = {}
    messages = {}
    cancelled = False
    routes = PromptServer.instance.routes
    API_PREFIX = "/api/sn0w"
    logger = Logger()

    @classmethod
    def addMessage(cls, id, message):
        """Add a message from the API."""
        if message == "__cancel__":
            cls.messages = {}
            cls.cancelled = True
        elif message == "__start__":
            cls.messages = {}
            cls.stash = {}
            cls.cancelled = False
        else:
            cls.messages[str(id)] = message

    @classmethod
    def waitForMessage(cls, id, period=0.1, asList=False):
        """Wait for a message from the API."""
        sid = str(id)
        while (sid not in cls.messages) and ("-1" not in cls.messages):
            if cls.cancelled:
                cls.cancelled = False
                raise Cancelled()
            time.sleep(period)
        if cls.cancelled:
            cls.cancelled = False
            raise Cancelled()
        message = cls.messages.pop(str(id), None) or cls.messages.pop("-1")
        try:
            if asList:
                return [int(x.strip()) for x in message.split(",")]

            return int(message.strip())
        except ValueError:
            cls.logger.log(
                f"failed to parse '{message}' as {'comma separated list of ints' if asList else 'int'}", "ERROR"
            )
            return [1] if asList else 1


class CharacterDBLoader:
    def __init__(self):
        start = time.perf_counter()
        self.logger = Logger()
        self.db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web", "characters", "characters.db")
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)  # Allow multi-thread access
        self.cursor = self.conn.cursor()
        self.lock = threading.Lock()  # Add lock for thread-safety
        self.logger.log(f"Connected to database at {self.db_path}", "DEBUG")
        self._ensure_table()
        self._custom_characters = self._load_custom_characters()
        duration = time.perf_counter() - start
        self.logger.log(f"CharacterDBLoader __init__ took {duration:.4f} seconds", "DEBUG")

    def _ensure_table(self):
        start = time.perf_counter()
        with self.lock:
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS characters (
                name TEXT PRIMARY KEY,
                gender TEXT,
                series TEXT,
                associated_string TEXT,
                prompt TEXT,
                clothing_tags TEXT,
                is_custom INTEGER DEFAULT 0
            )
            """)
            self.conn.commit()
        duration = time.perf_counter() - start
        self.logger.log(f"CharacterDBLoader _ensure_table took {duration:.4f} seconds", "DEBUG")

    def _load_custom_characters(self):
        """Load custom characters from JSON and return as dict."""
        start = time.perf_counter()
        base_dir = os.path.dirname(os.path.dirname(self.db_path))
        custom_json_path = os.path.join(base_dir, "settings/custom_characters.json")
        custom_dict = {}
        if os.path.exists(custom_json_path):
            try:
                with open(custom_json_path, "r", encoding="utf-8") as f:
                    custom_list = json.load(f)
                for char in custom_list:
                    name = char.get("name", "").lower()
                    if name:
                        series = char.get("series", "")
                        if not series:
                            series = self._extract_series_name(name).lower() or "custom"
                        custom_dict[name] = {
                            "gender": char.get("gender", ""),
                            "series": series,
                            "associated_string": char.get("associated_string", ""),
                            "prompt": char.get("prompt", ""),
                            "clothing_tags": char.get("clothing_tags", ""),
                            "is_custom": True,
                        }
                self.logger.log(f"Loaded {len(custom_dict)} custom characters", "DEBUG")
            except Exception as e:
                self.logger.log(f"Error loading custom characters: {e}", "ERROR")
        else:
            self.logger.log("Custom characters JSON file not found", "DEBUG")
        duration = time.perf_counter() - start
        self.logger.log(f"CharacterDBLoader _load_custom_characters took {duration:.4f} seconds", "DEBUG")
        return custom_dict

    def _extract_series_name(self, character_name):
        """Extract series name from character name."""
        if not character_name or "(" not in character_name:
            return ""
        last_open = character_name.rfind("(")
        last_close = character_name.rfind(")")
        if last_open != -1 and last_close > last_open:
            return character_name[last_open + 1 : last_close].strip()
        return ""

    def _get_db_characters(self):
        """Get characters from DB."""
        start = time.perf_counter()
        with self.lock:
            self.cursor.execute("SELECT * FROM characters")
            rows = self.cursor.fetchall()
        result = {
            row[0]: {
                "gender": row[1],
                "series": row[2],
                "associated_string": row[3],
                "prompt": row[4],
                "clothing_tags": row[5],
                "is_custom": bool(row[6]),
            }
            for row in rows
        }
        duration = time.perf_counter() - start
        self.logger.log(f"CharacterDBLoader _get_db_characters took {duration:.4f} seconds", "DEBUG")
        return result

    def get_all_characters(self):
        """Get all characters from DB and custom merged."""
        start = time.perf_counter()
        db_chars = self._get_db_characters()
        merged = db_chars.copy()
        for name, char in self._custom_characters.items():
            if name in merged:
                # Merge custom into existing
                existing = merged[name]
                existing["associated_string"] = ", ".join(
                    filter(None, [existing.get("associated_string", ""), char.get("associated_string", "")])
                )
                existing["prompt"] = ", ".join(filter(None, [existing.get("prompt", ""), char.get("prompt", "")]))
                existing["clothing_tags"] = ", ".join(
                    filter(None, [existing.get("clothing_tags", ""), char.get("clothing_tags", "")])
                )
                existing["is_custom"] = True
            else:
                merged[name] = char
        self.logger.log(
            f"Merged {len(db_chars)} DB characters with {len(self._custom_characters)} custom characters", "DEBUG"
        )
        duration = time.perf_counter() - start
        self.logger.log(f"CharacterDBLoader get_all_characters took {duration:.4f} seconds", "DEBUG")
        return merged

    def get_characters_by_series(self, series_name):
        """Get characters by series from merged data."""
        start = time.perf_counter()
        all_chars = self.get_all_characters()
        result = {name: char for name, char in all_chars.items() if char["series"] == series_name}
        duration = time.perf_counter() - start
        self.logger.log(f"CharacterDBLoader get_characters_by_series took {duration:.4f} seconds", "DEBUG")
        return result

    def get_all_series(self):
        """Get all series from merged data."""
        start = time.perf_counter()
        all_chars = self.get_all_characters()
        series_set = set(char["series"] for char in all_chars.values() if char["series"])
        result = sorted(series_set)
        duration = time.perf_counter() - start
        self.logger.log(f"CharacterDBLoader get_all_series took {duration:.4f} seconds", "DEBUG")
        return result

    def get_filtered_characters(self, visible_series=None):
        """Get filtered characters from merged data."""
        start = time.perf_counter()
        all_chars = self.get_all_characters()
        if visible_series:
            result = {
                name: char
                for name, char in all_chars.items()
                if char.get("is_custom") or char["series"] in visible_series
            }
        else:
            result = all_chars
        duration = time.perf_counter() - start
        self.logger.log(f"CharacterDBLoader get_filtered_characters took {duration:.4f} seconds", "DEBUG")
        return result

    def load_visible_series(self):
        """Load visible series from JSON file"""
        start = time.perf_counter()
        base_dir = os.path.dirname(os.path.dirname(self.db_path))
        visible_series_path = os.path.join(base_dir, "settings/visible_series.json")
        try:
            with open(visible_series_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    raise FileNotFoundError("File is empty")
                visible_series = json.loads(content)
                self.logger.log(f"Loaded {len(visible_series) if visible_series else 0} visible series", "DEBUG")
                result = set(visible_series) if visible_series else None
        except FileNotFoundError:
            self.logger.log(f"Visible series file not found or empty at: {visible_series_path}", "WARNING")
            all_series = self.get_all_series()
            os.makedirs(os.path.dirname(visible_series_path), exist_ok=True)
            with open(visible_series_path, "w", encoding="utf-8") as f:
                json.dump(all_series, f)
            result = set(all_series)
        except Exception as e:
            self.logger.log(f"Error reading visible series file: {e}", "ERROR")
            all_series = self.get_all_series()
            os.makedirs(os.path.dirname(visible_series_path), exist_ok=True)
            with open(visible_series_path, "w", encoding="utf-8") as f:
                json.dump(all_series, f)
            result = set(all_series)
        duration = time.perf_counter() - start
        self.logger.log(f"CharacterDBLoader load_visible_series took {duration:.4f} seconds", "DEBUG")
        return result

    def get_visible_characters(self, include_default=True):
        """Get characters filtered by visible series or only custom if include_default is False"""
        start = time.perf_counter()
        if not include_default:
            result = self._custom_characters
        else:
            visible_series = self.load_visible_series()
            result = self.get_filtered_characters(visible_series)
        duration = time.perf_counter() - start
        self.logger.log(f"CharacterDBLoader get_visible_characters took {duration:.4f} seconds", "DEBUG")
        return result

    def insert_character(self, name, gender, series="", associated_string="", prompt="", clothing_tags="", is_custom=0):
        start = time.perf_counter()
        # Only insert if not custom, or handle custom separately
        if is_custom:
            self.logger.log(f"Skipping insert for custom character: {name}", "DEBUG")
            # For custom, perhaps update the JSON, but since we're not modifying JSON, maybe just in memory
            # But for now, assume insert is for DB only
            pass
        else:
            self.logger.log(f"Inserting character into DB: {name}", "DEBUG")
            with self.lock:
                self.cursor.execute(
                    """
            INSERT OR REPLACE INTO characters (name, gender, series, associated_string, prompt, clothing_tags, is_custom)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                    (name, gender, series, associated_string, prompt, clothing_tags, is_custom),
                )
                self.conn.commit()
        duration = time.perf_counter() - start
        self.logger.log(f"CharacterDBLoader insert_character took {duration:.4f} seconds", "DEBUG")

    def close(self):
        start = time.perf_counter()
        self.logger.log("Closing database connection", "DEBUG")
        with self.lock:
            self.conn.close()
        duration = time.perf_counter() - start
        self.logger.log(f"CharacterDBLoader close took {duration:.4f} seconds", "DEBUG")


API_PREFIX = "/sn0w"


@PromptServer.instance.routes.get(f"{API_PREFIX}/loras")
async def get_loras(request):
    loras = folder_paths.get_filename_list("loras")
    return web.json_response(list(map(lambda a: os.path.splitext(a)[0], loras)))


@PromptServer.instance.routes.get(f"{API_PREFIX}/embeddings")
async def get_embeddings(request):
    embeddings = folder_paths.get_filename_list("embeddings")
    return web.json_response(list(map(lambda a: os.path.splitext(a)[0], embeddings)))


@PromptServer.instance.routes.get(f"{API_PREFIX}/update_logging_level")
async def update_logging_level(request):
    Logger.reload_config()
    return web.json_response("Success")


@PromptServer.instance.routes.post(f"{API_PREFIX}/add_lora_loaders")
async def add_lora_loaders(request):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    if os.path.basename(dir_path) == "src":
        dir_path = os.path.dirname(dir_path)
    json_path = os.path.join(dir_path, "web/settings/sn0w_settings.json")
    # Ensure the directory exists
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    try:
        # Parse the request body to get the new loaders
        new_loaders = await request.json()
        if not isinstance(new_loaders, list):
            return web.json_response({"error": "Invalid input, expected a list."}, status=400)

        # Read the existing JSON data from the file
        if os.path.exists(json_path):
            with open(json_path, "r") as file:
                data = json.load(file)
        else:
            data = {}

        # Initialize 'loraLoaders' if it doesn't exist in the JSON
        if "loraLoaders" not in data:
            data["loraLoaders"] = []

        # Add only new loaders that are not already in the list
        existing_loaders_set = set(tuple(loader) for loader in data["loraLoaders"])
        new_unique_loaders = [loader for loader in new_loaders if tuple(loader) not in existing_loaders_set]
        data["loraLoaders"].extend(new_unique_loaders)

        if len(new_unique_loaders) == 0:
            return web.json_response({"message": "No new lora loaders added."})

        # Write the updated JSON data back to the file
        with open(json_path, "w") as file:
            json.dump(data, file, indent=4)

        new_unique_loaders_str = "[" + ", ".join(str(loader) for loader in new_unique_loaders) + "]"
        return web.json_response({"message": f"Loaders added: {new_unique_loaders_str}"})

    except json.JSONDecodeError:
        return web.json_response({"error": "Invalid JSON format."}, status=400)
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)
