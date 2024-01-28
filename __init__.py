from .find_resolution import FindResolutionNode
from .split_string import SplitStringNode
from .lora_selector import LoraSelectorNode
from .lora_tester_xl import LoraTestXLNode

NODE_CLASS_MAPPINGS = {
    "Find SDXL Resolution": FindResolutionNode,
    "Split String": SplitStringNode,
    "Lora Selector": LoraSelectorNode,
    "Lora Tester XL": LoraTestXLNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Find SDXL Resolution": "Find SDXL Resolution",
    "Split String": "Split string into 4",
    "Lora Selector": "Lora Selector",
    "Lora Tester XL": "Lora Tester XL",
}
