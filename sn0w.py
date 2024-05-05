import os
import json
import time
import torch

from server import PromptServer
from aiohttp import web

class ConfigReader:
    @staticmethod
    def get_setting(setting_id, default=None):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Construct the relative path
        relative_path = '../../user/default/comfy.settings.json'
        # Combine paths and normalize it
        file_path = os.path.abspath(os.path.join(current_dir, relative_path))
        try:
            with open(file_path, 'r') as file:
                settings = json.load(file)
            return settings.get(setting_id, default)
        except FileNotFoundError:
            Logger.print_sn0w(f"Local configuration file not found at {file_path}.", "\033[0;33m")
            return default
        except json.JSONDecodeError:
            Logger.print_sn0w(f"Error decoding JSON from {file_path}.", "\033[0;31m")
            return default

class Logger:
    PURPLE_TEXT = "\033[0;35m"
    RED_TEXT = "\033[0;31m"
    YELLOW_TEXT = "\033[0;33m"
    RESET_TEXT = "\033[0m"
    PREFIX = "[sn0w] "

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
        min_level_to_log = settings_to_levels.get(ConfigReader.get_setting('sn0w.LoggingLevel', 'INFORMATIONAL'), 3)
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
    logger = Logger()
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

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
    
    @staticmethod
    def initialize_state():
        # Default values
        default_state = {
            'character': "None"
        }

        state_path = os.path.join(Utility.ROOT_DIR, 'state.json')

        # Check if state.json exists; if not, create it with default values
        if not os.path.exists(state_path):
            with open(state_path, 'w') as f:
                json.dump(default_state, f)
            Utility.logger.log("Initialized state file with default values at the root.", "DEBUG")
        else:
            # Ensure all default keys exist in the file, if file exists
            with open(state_path, 'r') as f:
                state = json.load(f)
            # Update the file with any missing default values
            state_updated = False
            for key, value in default_state.items():
                if key not in state:
                    state[key] = value
                    state_updated = True
            if state_updated:
                with open(state_path, 'w') as f:
                    json.dump(state, f)
            Utility.logger.log("State file checked and updated with any missing default values at the root.", "DEBUG")
    
    @staticmethod
    def save_state(name, value):
        state_path = os.path.join(Utility.ROOT_DIR, 'state.json')
        state = {}
        if os.path.exists(state_path):
            with open(state_path, 'r') as f:
                state = json.load(f)
        state[name] = value
        with open(state_path, 'w') as f:
            json.dump(state, f)

    @staticmethod
    def load_state(name):
        state_path = os.path.join(Utility.ROOT_DIR, 'state.json')
        try:
            with open(state_path, 'r') as f:
                state = json.load(f)
                return state.get(name, None)
        except FileNotFoundError:
            Utility.logger.log("State file not found at the root. Creating new state file.", "ERROR")
            # Create a new state.json with default values or empty
            with open(state_path, 'w') as f:
                json.dump({}, f)
            return None
        
class MessageHolder:
    messages = {}

    @classmethod
    def addMessage(self, id, message):
        self.messages[str(id)] = message
        Utility.logger.log(f"Adding message for ID: {id}, Message: {message}", "DEBUG")

    @classmethod
    def waitForMessage(self, id, period = 0.1):
        sid = str(id)

        while not (sid in self.messages):
            time.sleep(period)

        message = self.messages.pop(str(id),None)
        return message
    
routes = PromptServer.instance.routes
@routes.post('/textbox_string')
async def handle_textbox_string(request):
    data = await request.json()  # Parse JSON from request
    MessageHolder.addMessage(data.get("node_id"), data.get("outputs"))
    return web.json_response({"status": "ok"})