import os
import json
import torch

class ConfigReader:
    _config = None

    @classmethod
    def load_config(cls):
        if cls._config is None:
            # Get the directory of the current file
            current_file_path = os.path.realpath(__file__)
            # Navigate up to the parent directory of the current file
            parent_dir = os.path.dirname(os.path.dirname(current_file_path))
            # Construct the path to the 'config.json' file located in the parent directory
            config_path = os.path.join(parent_dir, 'config.json')
            
            try:
                with open(config_path, 'r') as file:
                    cls._config = json.load(file)
            except FileNotFoundError:
                print(f"Configuration file not found at {config_path}. Using default settings.")
                cls._config = {}  # Use an empty dict as a fallback
        return cls._config
    
    @staticmethod
    def get_setting(setting_id, default=None):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Construct the relative path
        relative_path = '../../../user/default/comfy.settings.json'
        # Combine paths and normalize it
        file_path = os.path.abspath(os.path.join(current_dir, relative_path))
        try:
            with open(file_path, 'r') as file:
                settings = json.load(file)
            return settings.get(setting_id, default)
        except FileNotFoundError:
            print(f"Local configuration file not found at {file_path}.")
            return default
        except json.JSONDecodeError:
            print(f"Error decoding JSON from {file_path}.")
            return default

class Logger:
    PURPLE_TEXT = "\033[0;35m"
    RED_TEXT = "\033[0;31m"
    YELLOW_TEXT = "\033[0;33m"
    RESET_TEXT = "\033[0m"
    PREFIX = "[sn0w] "

    def __init__(self):
        # Default to Informational level if not configured
        self.logging_level = ConfigReader.get_setting('sn0w.LoggingLevel', 'INFORMATIONAL')

    @classmethod
    def print_sn0w(cls, message, color):
        print(f"{color}{cls.PREFIX}{cls.RESET_TEXT}{message}")

    def log(self, message, level="ERROR"):
        # Map the high-level settings to specific log level thresholds
        settings_to_levels = {
            "ERRORS_ONLY": 3,         # Logs only Critical, Alert, Emergency, and Error
            "WARNINGS_ABOVE": 4,      # Logs Warning and higher severity
            "INFO_ABOVE": 6,          # Logs Informational and higher severity
            "ALL": 7                  # Logs everything including Debug
        }

        # Standard log levels with corresponding numeric values
        levels = {
            "EMERGENCY": 0,
            "ALERT": 1,
            "CRITICAL": 2,
            "ERROR": 3,
            "WARNING": 4,
            "NOTICE": 5,
            "INFORMATIONAL": 6,
            "DEBUG": 7
        }

        # Determine the minimum level to log based on configuration
        min_level_to_log = settings_to_levels.get(self.logging_level, 3)
        message_level = levels.get(level.upper(), 6)  # Default to "INFORMATIONAL" if level is unrecognized

        # Decide the color based on the type of message
        if level.upper() in ["EMERGENCY", "ALERT", "CRITICAL", "ERROR"]:
            color = self.RED_TEXT
        elif level.upper() == "WARNING":
            color = self.YELLOW_TEXT
        else:
            color = self.PURPLE_TEXT  # Default color

        # Log the message if the severity is greater than or equal to the configured threshold
        if message_level <= min_level_to_log:
            self.print_sn0w(message, color)

class Utility:
    @staticmethod
    def levenshtein_distance(s1, s2):
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
        reference_dimensions = tensors[0].shape[1:]  # Ignore batch dimension
        mismatched_images = [names[i] for i, tensor in enumerate(tensors) if tensor.shape[1:] != reference_dimensions]

        if mismatched_images:
            raise ValueError(f"Input image dimensions do not match for images: {mismatched_images}")

    @staticmethod
    def image_batch(**kwargs):
        batched_tensors = [kwargs[key] for key in kwargs if kwargs[key] is not None]
        image_names = [key for key in kwargs if kwargs[key] is not None]

        if not batched_tensors:
            raise ValueError("At least one input image must be provided.")

        Utility._check_image_dimensions(batched_tensors, image_names)
        batched_tensors = torch.cat(batched_tensors, dim=0)
        return batched_tensors