import importlib
import os
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
from .src.simple_ksampler import SimpleSamplerCustom
from .src.filter_tags import FilterTags

# Constants
WEB_DIRECTORY = "./web"
CURRENT_UNIQUE_ID = 0  # Global variable to track the unique ID
logger = Logger()

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
    "Sn0w KSampler": SimpleSamplerCustom,
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
    "Sn0w KSampler": "Sn0w KSampler",
    "Filter Tags": "Filter Tags",
}

# Function to check required folder paths
check_lora_folders()


def parse_custom_lora_loaders(custom_lora_loaders):
    """
    Parse a string of custom Lora loaders into a list of tuples containing
    the name, required folders, and the number of combinations.
    """
    required_folders_with_names = []
    entries = custom_lora_loaders.split("\n")
    for entry in entries:
        if entry.strip():
            name, _, remainder = entry.partition(":")
            if ":" in remainder:
                value, _, combos = remainder.partition(":")
            else:
                value = remainder
                combos = 1
            required_folders_with_names.append((name.strip(), value.strip().split(","), int(combos)))
    return required_folders_with_names


def generate_and_register_lora_node(lora_type, setting):
    """Generate and register the users custom lora loaders"""
    global CURRENT_UNIQUE_ID

    custom_lora_loaders = ConfigReader.get_setting(setting, None)
    if custom_lora_loaders is not None:
        required_folders_with_names = parse_custom_lora_loaders(custom_lora_loaders)
        for name, folders, combos in required_folders_with_names:
            CURRENT_UNIQUE_ID += 1
            unique_id_with_name = f"{name}_{CURRENT_UNIQUE_ID}"

            logger.log(f"Adding custom lora loader. Path: {folders}, Name: {name}, Inputs: {combos}", "INFORMATIONAL")
            DynamicLoraNode = generate_lora_node_class(lora_type, folders, combos)
            if DynamicLoraNode:
                if name in NODE_CLASS_MAPPINGS:
                    NODE_CLASS_MAPPINGS[unique_id_with_name] = DynamicLoraNode
                    NODE_DISPLAY_NAME_MAPPINGS[unique_id_with_name] = f"{name}"
                else:
                    NODE_CLASS_MAPPINGS[name] = DynamicLoraNode
                    NODE_DISPLAY_NAME_MAPPINGS[name] = f"{name}"


def generate_and_register_all_lora_nodes():
    """Generate and register all custom lora nodes."""
    lora_types = [
        ("loras_xl", "sn0w.CustomLoraLoaders.XL"),
        ("loras_15", "sn0w.CustomLoraLoaders"),
        ("loras_3", "sn0w.CustomLoraLoaders.3"),
    ]
    for lora_type, setting in lora_types:
        generate_and_register_lora_node(lora_type, setting)


def import_and_register_scheduler_nodes():
    """
    Import and register custom scheduler nodes from Python files in the
    'src/custom_schedulers' directory.
    """
    custom_schedulers_path = os.path.join(os.path.dirname(__file__), "src", "custom_schedulers")
    for filename in os.listdir(custom_schedulers_path):
        if filename.endswith(".py") and filename != "custom_schedulers.py":
            module_name = filename[:-3]
            module = import_module_from_path(module_name, os.path.join(custom_schedulers_path, filename))
            register_scheduler_node(module)


def import_module_from_path(module_name, file_path):
    """Helper function to import a module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def register_scheduler_node(module):
    """Register a scheduler node if it contains settings and a get_sigmas function."""
    settings = getattr(module, "settings", None)
    get_sigmas_function = getattr(module, "get_sigmas", None)
    if settings and get_sigmas_function:
        DynamicSchedulerNode = generate_scheduler_node_class(settings, get_sigmas_function)
        class_name = settings.get("name", "default").capitalize() + "Scheduler"
        NODE_CLASS_MAPPINGS[class_name] = DynamicSchedulerNode
        NODE_DISPLAY_NAME_MAPPINGS[class_name] = class_name


# Register custom nodes
generate_and_register_all_lora_nodes()
import_and_register_scheduler_nodes()
