import os
import json
import time
import torch
import uuid

from server import PromptServer
from aiohttp import web

class ConfigReader:
    DEFAULT_PATH = os.path.abspath(os.path.join(os.getcwd(), 'user/default/comfy.settings.json'))
    PORTABLE_PATH = os.path.abspath(os.path.join(os.getcwd(), 'ComfyUI/user/default/comfy.settings.json'))

    portable = None

    @classmethod
    def print_sn0w(cls, message, color):
        print(f"{color}[sn0w] \033[0m{message}")
    
    @classmethod
    def is_comfy_portable(cls):
        if cls.portable != None:
            return cls.portable
        
        # Check if default exists
        if os.path.isfile(cls.DEFAULT_PATH):
            cls.portable = False
            return False
        
        # Check if portable exists
        if os.path.isfile(cls.PORTABLE_PATH):
            cls.portable = True
            return True
        
        # If neither exist, 
        return None

    @staticmethod
    def get_setting(setting_id, default=None):
        # Check if the user is using portable or default ComfyUI
        is_portable = ConfigReader.is_comfy_portable()

        if is_portable:
            path = ConfigReader.PORTABLE_PATH
        elif not is_portable:
            path = ConfigReader.DEFAULT_PATH
        else:
            ConfigReader.print_sn0w(f"Local configuration file not found at either {ConfigReader.PORTABLE_PATH} or {ConfigReader.DEFAULT_PATH}.", "\033[0;33m")
            return default

        try:
            with open(path, 'r') as file:
                settings = json.load(file)
            return settings.get(setting_id, default)
        except FileNotFoundError:
            ConfigReader.print_sn0w(f"Local configuration file not found at {path}.", "\033[0;33m")
            return default
        except json.JSONDecodeError:
            ConfigReader.print_sn0w(f"Error decoding JSON from {path}.", "\033[0;31m")
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
        if level.upper() in self.enabled_levels or level.upper() in ["EMERGENCY", "ALERT", "CRITICAL", "ERROR"]:
            self.print_sn0w(message, color)

    def print_sigmas_differences(self, name, sigmas):
        """
        Takes a tensor of sigmas and prints each sigma along with the difference to the next sigma
        and the percentage difference to the next sigma.
        
        Args:
        sigmas (torch.Tensor): A 1D tensor of sigmas with a zero appended at the end.
        """
        if ("DEBUG" in self.enabled_levels):
            self.print_sn0w(f"Scheduler: {name}", self.PURPLE_TEXT)
            print("Index | Sigma Value | Difference to Next | % Difference")
            print("-" * 65)
            
            # Compute the differences
            differences = sigmas[1:] - sigmas[:-1]
            
            # Iterate over sigmas and differences
            for i in range(len(sigmas) - 1):
                if sigmas[i] != 0:
                    percent_diff = (differences[i] / sigmas[i]) * 100
                else:
                    percent_diff = float('inf')  # To handle division by zero in a meaningful way
                print(f"{i:<5} | {sigmas[i]:<11.4f} | {differences[i]:<18.4f} | {percent_diff:<12.2f}")
            
            # Print the last sigma value without a difference (since it's the appended zero)
            print(f"{len(sigmas) - 1:<5} | {sigmas[-1]:<11.4f} | {'N/A':<18} | {'N/A':<12}")

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
    def generate_uuid():
        return str(uuid.uuid4())
    
    @staticmethod
    def get_model_type(model_patcher):
        return model_patcher.model.__class__.__name__
    
    @classmethod
    def put_favourite_on_top(cls, setting, arr):
        # Convert to a list if its a dictionary
        if type(arr) == dict:
            arr = list(arr.keys())

        favourites = ConfigReader.get_setting(setting, [])
        if favourites == None:
            return arr
        
        # Create an empty list to store the prioritized list
        prioritized = []

        # Iterate through filtered loras
        for item in arr:
            # Check for partial match (case-insensitive) with any favorite lora
            if any(favourite.lower() in item.lower() for favourite in favourites):
                # Add the matching lora to the prioritized list
                prioritized.append(item)
                # Remove the matching lora from filtered_sorted_loras to avoid duplicates
                arr.remove(item)

        # Append the remaining filtered loras to the prioritized list
        prioritized.extend(arr)
        return prioritized
    
class AnyType(str):
    def __ne__(self, __value: object) -> bool:
        return False
        
class MessageHolder:
    messages = {}

    @classmethod
    def addMessage(self, id, message):
        self.messages[str(id)] = message

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
    data = await request.json()
    MessageHolder.addMessage(data.get("node_id"), data.get("outputs"))
    return web.json_response({"status": "ok"})

@routes.post(f'{API_PREFIX}/update_sorting')
async def handle_update_sorting(request):
    Logger.reload_config()
    return web.json_response({"status": "ok"})

@routes.post(f'{API_PREFIX}/widget_values')
async def handle_widget_values(request):
    data = await request.json()
    MessageHolder.addMessage(data.get("node_id"), data.get("outputs"))
    return web.json_response({"status": "ok"})

@routes.post(f'{API_PREFIX}/should_decode_image')
async def handle_should_decode_image(request):
    data = await request.json()
    MessageHolder.addMessage(data.get("node_id"), data.get("outputs"))
    return web.json_response({"status": "ok"})

@routes.post(f'{API_PREFIX}/get_sigmas')
async def handle_get_sigmas(request):
    data = await request.json()
    MessageHolder.addMessage(data.get("node_id"), data.get("outputs"))
    return web.json_response({"status": "ok"})