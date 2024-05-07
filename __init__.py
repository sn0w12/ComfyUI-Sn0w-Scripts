from .src.dynamic_lora_loader import generate_lora_node_class
from .sn0w import ConfigReader, Logger

from .src.find_resolution import FindResolutionNode
from .src.lora_selector import LoraSelectorNode
from .src.lora_tester import LoraTestNode
from .src.character_select import CharacterSelectNode
from .src.prompt_combine import CombineStringNode
from .src.lora_stacker import LoraStackerNode
from .src.get_font_size import GetFontSizeNode
from .src.prompt_selector import PromptSelectNode
from .src.perlin_noise import FilmGrain
from .src.upscale_with_model_by import UpscaleImageBy
from .src.load_lora_from_folder import LoadLoraFolderNode
from .src.textbox import TextboxNode
from .src.simple_sampler_custom import SimpleSamplerCustom

NODE_CLASS_MAPPINGS = {
    "Find SDXL Resolution": FindResolutionNode,
    "Lora Selector": LoraSelectorNode,
    "Lora Tester": LoraTestNode,
    "Character Selector": CharacterSelectNode,
    "Prompt Combine": CombineStringNode,
    "Sn0w Lora Stacker": LoraStackerNode,
    "Load Lora XL": generate_lora_node_class("loras_xl"),
    "Load Lora 1.5": generate_lora_node_class("loras_15"),
    "Get Font Size": GetFontSizeNode,
    "Prompt Selector": PromptSelectNode,
    "Colored Film Grain": FilmGrain,
    "Upscale Image With Model By": UpscaleImageBy,
    "Load Lora Folder": LoadLoraFolderNode,
    "Copy/Paste Textbox": TextboxNode,
    "Simple Sampler Custom": SimpleSamplerCustom,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Find SDXL Resolution": "Find SDXL Resolution",
    "Lora Selector": "Lora Selector",
    "Lora Tester": "Lora Tester",
    "Character Selector": "Character Selector",
    "Prompt Combine": "Prompt Combine",
    "Sn0w Lora Stacker": "Sn0w Lora Stacker",
    "Load Lora XL": "Load Lora XL",
    "Load Lora 1.5": "Load Lora 1.5",
    "Get Font Size": "Get Font Size",
    "Prompt Selector": "Prompt Selector",
    "Colored Film Grain": "Colored Film Grain",
    "Upscale Image With Model By": "Upscale Image With Model By",
    "Load Lora Folder": "Load Lora Folder",
    "Copy/Paste Textbox": "Textbox",
    "Simple Sampler Custom": "Simple Sampler Custom",
}

WEB_DIRECTORY = "./web"

current_unique_id = 0  # Global variable to track the unique ID
logger = Logger()

def parse_custom_lora_loaders(custom_lora_loaders):
    required_folders_with_names = []
    # Split the input string by new lines to get each name-value pair
    entries = custom_lora_loaders.split('\n')
    for entry in entries:
        if entry.strip():  # Make sure the entry is not just whitespace
            name, _, value = entry.partition(':')
            name = name.strip()
            value = value.strip()
            required_folders_with_names.append((name, value.split(',')))  # Assuming values are comma-separated
    return required_folders_with_names

def generate_and_register_lora_node(lora_type, setting):
    global current_unique_id  # Use the global variable to keep track of IDs
    
    custom_lora_loaders = ConfigReader.get_setting(setting, None)
    if custom_lora_loaders is not None:
        required_folders_with_names = parse_custom_lora_loaders(custom_lora_loaders)

        for name, folders in required_folders_with_names:
            current_unique_id += 1  # Increment the unique ID for each new class
            unique_id_with_name = str(f"{name}_{current_unique_id}")
            
            logger.log(f"Adding custom lora loader: {folders}, {unique_id_with_name}", "ALL")
            DynamicLoraNode = generate_lora_node_class(lora_type, folders)

            # Update NODE_CLASS_MAPPINGS and NODE_DISPLAY_NAME_MAPPINGS for each generated class
            if name in NODE_CLASS_MAPPINGS:
                NODE_CLASS_MAPPINGS[unique_id_with_name] = DynamicLoraNode
                NODE_DISPLAY_NAME_MAPPINGS[unique_id_with_name] = f"{name}"
            else:
                NODE_CLASS_MAPPINGS[name] = DynamicLoraNode
                NODE_DISPLAY_NAME_MAPPINGS[name] = f"{name}"

generate_and_register_lora_node("loras_xl", "sn0w.CustomLoraLoadersXL")
generate_and_register_lora_node("loras_15", "sn0w.CustomLoraLoaders1.5")