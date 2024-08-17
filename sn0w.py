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

    DEFAULT_PATH = os.path.abspath(os.path.join(os.getcwd(), "user/default/comfy.settings.json"))
    PORTABLE_PATH = os.path.abspath(os.path.join(os.getcwd(), "ComfyUI/user/default/comfy.settings.json"))

    portable = None

    @classmethod
    def print_sn0w(cls, message, color="\033[0;35m"):
        """Print a message with a specific color prefix."""
        print(f"{color}[sn0w] \033[0m{message}")

    @classmethod
    def _get_path(cls):
        return ConfigReader.PORTABLE_PATH if ConfigReader.portable else ConfigReader.DEFAULT_PATH

    @classmethod
    def is_comfy_portable(cls):
        """Check if the application is running in portable mode."""
        if cls.portable is not None:
            return cls.portable

        # Check if default exists
        if os.path.isfile(cls.DEFAULT_PATH):
            cls.portable = False
            ConfigReader.print_sn0w("Running standalone comfy.")
            return False

        # Check if portable exists
        if os.path.isfile(cls.PORTABLE_PATH):
            cls.portable = True
            ConfigReader.print_sn0w("Running portable comfy.")
            return True

        # If neither exist
        ConfigReader.print_sn0w("Could not find comfy settings.")
        return None

    @staticmethod
    def get_setting(setting_id, default=None):
        """Retrieve a setting value from the configuration file."""
        # Determine the correct path based on the portable attribute
        if ConfigReader.portable is None:
            ConfigReader.print_sn0w(
                f"Local configuration file not found at either {ConfigReader.PORTABLE_PATH} or {ConfigReader.DEFAULT_PATH}.",
                "\033[0;33m",
            )
            return default

        path = ConfigReader._get_path()

        # Try to read the settings from the determined path
        try:
            with open(path, "r", encoding="utf-8") as file:
                settings = json.load(file)
            return settings.get(setting_id, default)
        except FileNotFoundError:
            ConfigReader.print_sn0w(f"Local configuration file not found at {path}.", "\033[0;33m")
        except json.JSONDecodeError:
            ConfigReader.print_sn0w(f"Error decoding JSON from {path}.", "\033[0;31m")

        return default

    @staticmethod
    def set_setting(setting_id: str, value):
        """Set a setting value in the configuration file."""
        # Determine the correct path based on the portable attribute
        if ConfigReader.portable is None:
            ConfigReader.print_sn0w(
                f"Local configuration file not found at either {ConfigReader.PORTABLE_PATH} or {ConfigReader.DEFAULT_PATH}.",
                "\033[0;33m",
            )
            return False

        path = ConfigReader._get_path()

        # Try to read the existing settings from the determined path
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
        }

        path = ConfigReader._get_path()
        with open(path, "r", encoding="utf-8") as file:
            settings = json.load(file)

        for setting in settings:
            if setting in conversion_map:
                setting_value = cls.get_setting(setting)
                if setting_value:
                    cls.set_setting(conversion_map[setting], setting_value)
                    cls.set_setting(setting, None)  # Remove the old setting


# Initialize portable check when the class is defined
ConfigReader.is_comfy_portable()
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
        workflow = data.get("workflow", {})
        nodes = workflow.get("nodes", [])

        for node in nodes:
            if int(node.get("id")) == int(node_id):
                for output in node.get("outputs", []):
                    if int(output["slot_index"]) == int(output_id):
                        return output
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

        return web.json_response({"message": f"Lora loaders: {new_unique_loaders} added successfully."})

    except json.JSONDecodeError:
        return web.json_response({"error": "Invalid JSON format."}, status=400)
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)
