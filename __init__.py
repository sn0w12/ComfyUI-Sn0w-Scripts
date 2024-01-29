from .src.find_resolution import FindResolutionNode
from .src.split_string import SplitStringNode
from .src.lora_selector import LoraSelectorNode
from .src.lora_tester_xl import LoraTestXLNode
from .src.lora_tester import LoraTestNode
from .src.character_select import CharacterSelectNode
from .src.prompt_combine import CombineStringNode

NODE_CLASS_MAPPINGS = {
    "Find SDXL Resolution": FindResolutionNode,
    "Split String": SplitStringNode,
    "Lora Selector": LoraSelectorNode,
    "Lora Tester XL": LoraTestXLNode,
    "Lora Tester": LoraTestNode,
    "Character Selector": CharacterSelectNode,
    "Prompt Combine": CombineStringNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Find SDXL Resolution": "Find SDXL Resolution",
    "Split String": "Split string into 4",
    "Lora Selector": "Lora Selector",
    "Lora Tester XL": "Lora Tester XL",
    "Lora Tester": "Lora Tester",
    "Character Selector": "Character Selector",
    "Prompt Combine": "Prompt Combine",
}
