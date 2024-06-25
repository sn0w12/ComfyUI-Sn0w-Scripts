import importlib
import os
import folder_paths
from .src.dynamic_lora_loader import generate_lora_node_class
from .src.dynamic_scheduler_loader import generate_scheduler_node_class
from .src.check_folder_paths import check_lora_folders
from .sn0w import ConfigReader, Logger

from .src.lora_selector import LoraSelectorNode
from .src.lora_tester import LoraTestNode
from .src.character_select import CharacterSelectNode
from .src.prompt_combine import CombineStringNode
from .src.lora_stacker import LoraStackerNode
from .src.get_font_size import GetFontSizeNode
from .src.prompt_selector import PromptSelectNode
from .src.upscale_with_model_by import UpscaleImageBy
from .src.load_lora_from_folder import LoadLoraFolderNode
from .src.textbox import TextboxNode
from .src.simple_sampler_custom import SimpleSamplerCustom
from .src.filter_tags import FilterTags

NODE_CLASS_MAPPINGS = {
    "Lora Selector": LoraSelectorNode,
    "Lora Tester": LoraTestNode,
    "Character Selector": CharacterSelectNode,
    "Prompt Combine": CombineStringNode,
    "Sn0w Lora Stacker": LoraStackerNode,
    "Load Lora Sn0w": generate_lora_node_class("loras"),
    "Get Font Size": GetFontSizeNode,
    "Prompt Selector": PromptSelectNode,
    "Upscale Image With Model By": UpscaleImageBy,
    "Load Lora Folder": LoadLoraFolderNode,
    "Copy/Paste Textbox": TextboxNode,
    "Simple Sampler Custom": SimpleSamplerCustom,
    "Filter Tags": FilterTags,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Lora Selector": "Lora Selector",
    "Lora Tester": "Lora Tester",
    "Character Selector": "Character Selector",
    "Prompt Combine": "Prompt Combine",
    "Sn0w Lora Stacker": "Sn0w Lora Stacker",
    "Load Lora Sn0w": "Load Lora Sn0w",
    "Get Font Size": "Get Font Size",
    "Prompt Selector": "Prompt Selector",
    "Upscale Image With Model By": "Upscale Image With Model By",
    "Load Lora Folder": "Load Lora Folder",
    "Copy/Paste Textbox": "Textbox",
    "Simple Sampler Custom": "Simple Sampler Custom",
    "Filter Tags": "Filter Tags",
}

WEB_DIRECTORY = "./web"

check_lora_folders()

current_unique_id = 0  # Global variable to track the unique ID
logger = Logger()

def parse_custom_lora_loaders(custom_lora_loaders):
    required_folders_with_names = []
    # Split the input string by new lines to get each name-value pair
    entries = custom_lora_loaders.split('\n')
    for entry in entries:
        if entry.strip():  # Make sure the entry is not just whitespace
            name, _, remainder = entry.partition(':')
            if ':' in remainder:
                value, _, combos = remainder.partition(':')
            else:
                value = remainder
                combos = 1

            name = name.strip()
            value = value.strip()
            combos = int(combos)
            required_folders_with_names.append((name, value.split(','), combos))
    return required_folders_with_names

def generate_and_register_lora_node(lora_type, setting):
    global current_unique_id  # Use the global variable to keep track of IDs
    
    custom_lora_loaders = ConfigReader.get_setting(setting, None)
    if custom_lora_loaders is not None:
        required_folders_with_names = parse_custom_lora_loaders(custom_lora_loaders)

        for name, folders, combos in required_folders_with_names:
            current_unique_id += 1  # Increment the unique ID for each new class
            unique_id_with_name = str(f"{name}_{current_unique_id}")
            
            logger.log(f"Adding custom lora loader: {folders}, {unique_id_with_name}, {combos}", "INFORMATIONAL")
            DynamicLoraNode = generate_lora_node_class(lora_type, folders, combos)

            # Update NODE_CLASS_MAPPINGS and NODE_DISPLAY_NAME_MAPPINGS for each generated class
            if name in NODE_CLASS_MAPPINGS:
                NODE_CLASS_MAPPINGS[unique_id_with_name] = DynamicLoraNode
                NODE_DISPLAY_NAME_MAPPINGS[unique_id_with_name] = f"{name}"
            else:
                NODE_CLASS_MAPPINGS[name] = DynamicLoraNode
                NODE_DISPLAY_NAME_MAPPINGS[name] = f"{name}"

generate_and_register_lora_node("loras_xl", "sn0w.CustomLoraLoadersXL")
generate_and_register_lora_node("loras_15", "sn0w.CustomLoraLoaders1.5")
generate_and_register_lora_node("loras_3", "sn0w.CustomLoraLoaders3")

def import_and_register_scheduler_nodes():
    custom_schedulers_path = os.path.join(os.path.dirname(__file__), 'src', 'custom_schedulers')
    for filename in os.listdir(custom_schedulers_path):
        if filename.endswith('.py') and filename != 'custom_schedulers.py':
            file_path = os.path.join(custom_schedulers_path, filename)
            module_name = filename[:-3]  # Remove the .py extension

            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            settings = getattr(module, 'settings', None)
            get_sigmas_function = getattr(module, 'get_sigmas', None)

            if settings and get_sigmas_function:
                DynamicSchedulerNode = generate_scheduler_node_class(settings, get_sigmas_function)
                class_name = settings["name"].capitalize() + "Scheduler"
                
                NODE_CLASS_MAPPINGS[class_name] = DynamicSchedulerNode
                NODE_DISPLAY_NAME_MAPPINGS[class_name] = class_name

import_and_register_scheduler_nodes()
