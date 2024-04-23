import re
from .src.dynamic_lora_loader import generate_lora_node_class
from .src.sn0w import ConfigReader, Logger

from .src.find_resolution import FindResolutionNode
from .src.lora_selector import LoraSelectorNode
from .src.lora_tester_xl import LoraTestXLNode
from .src.lora_tester import LoraTestNode
from .src.character_select import CharacterSelectNode
from .src.prompt_combine import CombineStringNode
from .src.simple_sampler_xl import SimpleSamplerXlNode
from .src.simple_sampler import SimpleSamplerNode
from .src.lora_stacker import LoraStackerNode
from .src.load_lora_xl import LoraLoraXLNode
from .src.load_lora_15 import LoraLora15Node
from .src.load_lora_character import LoadLoraCharacterNode
from .src.get_font_size import GetFontSizeNode
from .src.get_all_styles import GetStylesNode
from .src.prompt_selector import PromptSelectNode
from .src.load_lora_concept import LoadLoraConceptNode
from .src.perlin_noise import FilmGrain
from .src.upscale_with_model_by import UpscaleImageBy
from .src.custom_hires import CustomHires

NODE_CLASS_MAPPINGS = {
    "Find SDXL Resolution": FindResolutionNode,
    "Lora Selector": LoraSelectorNode,
    "Lora Tester XL": LoraTestXLNode,
    "Lora Tester": LoraTestNode,
    "Character Selector": CharacterSelectNode,
    "Prompt Combine": CombineStringNode,
    "Simple Sampler XL": SimpleSamplerXlNode,
    "Simple Sampler": SimpleSamplerNode,
    "Lora Stacker": LoraStackerNode,
    "Load Lora XL": LoraLoraXLNode,
    "Load Lora 1.5": LoraLora15Node,
    "Load Lora Character": LoadLoraCharacterNode,
    "Get Font Size": GetFontSizeNode,
    "Get All Styles": GetStylesNode,
    "Prompt Selector": PromptSelectNode,
    "Load Lora Concept": LoadLoraConceptNode,
    "Colored Film Grain": FilmGrain,
    "Upscale Image With Model By": UpscaleImageBy,
    "Sn0w Custom Hires": CustomHires,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Find SDXL Resolution": "Find SDXL Resolution",
    "Lora Selector": "Lora Selector",
    "Lora Tester XL": "Lora Tester XL",
    "Lora Tester": "Lora Tester",
    "Character Selector": "Character Selector",
    "Prompt Combine": "Prompt Combine",
    "Simple Sampler XL": "Simple Sampler XL",
    "Simple Sampler": "Simple Sampler",
    "Lora Stacker": "Lora Stacker",
    "Load Lora XL": "Load Lora XL",
    "Load Lora 1.5": "Load Lora 1.5",
    "Load Lora Character": "Load Lora Character",
    "Get Font Size": "Get Font Size",
    "Get All Styles": "Get All Styles",
    "Prompt Selector": "Prompt Selector",
    "Load Lora Concept": "Load Lora Concept",
    "Colored Film Grain": "Colored Film Grain",
    "Upscale Image With Model By": "Upscale Image With Model By",
    "Sn0w Custom Hires": "Sn0w Custom Hires",
}

current_unique_id = 0  # Global variable to track the unique ID
logger = Logger()

def parse_custom_lora_loaders(custom_lora_loaders):
    required_folders_with_names = []
    for name, folders_str in custom_lora_loaders.items():
        # Treat every value as a comma-separated list
        folders = [folder.strip() for folder in folders_str.split(',')]
        required_folders_with_names.append((name, folders))
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

generate_and_register_lora_node("loras_xl", "custom_lora_loaders_xl")
generate_and_register_lora_node("loras_15", "custom_lora_loaders")