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
    GREEN_TEXT = "\033[0;32m"
    RESET_TEXT = "\033[0m"
    PREFIX = "[sn0w] "

    enabled_levels = ConfigReader.get_setting('sn0w.LoggingLevel', ["INFORMATIONAL", "WARNING"])

    @classmethod
    def reload_config(cls):
        cls.enabled_levels = ConfigReader.get_setting('sn0w.LoggingLevel', ["INFORMATIONAL", "WARNING"])


    @classmethod
    def print_sn0w(cls, message, color):
        print(f"{color}{cls.PREFIX}{cls.RESET_TEXT}{message}")

    def log(self, message, level="ERROR"):
        # Determine the color based on the type of message
        if level.upper() in ["EMERGENCY", "ALERT", "CRITICAL", "ERROR"]:
            color = self.RED_TEXT
        elif level.upper() == "WARNING":
            color = self.YELLOW_TEXT
        else:
            color = self.PURPLE_TEXT  # Default color

        # Check if the message's level is in the enabled log levels
        if level.upper() in self.enabled_levels:
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
API_PREFIX = '/sn0w'

@routes.post(f'{API_PREFIX}/textbox_string')
async def handle_textbox_string(request):
    data = await request.json()  # Parse JSON from request
    MessageHolder.addMessage(data.get("node_id"), data.get("outputs"))
    return web.json_response({"status": "ok"})

@routes.post(f'{API_PREFIX}/logging_level')
async def handle_textbox_string(request):
    Logger.reload_config()
    return web.json_response({"status": "ok"})