from pathlib import Path
import folder_paths
import re

# Import ComfyUI files
import comfy.sd
import comfy.utils

from . import LoraTagLoader

class LoraTestNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "lora_string": ("STRING", {"default": ""}),
                "strength_increase": ("INT", {"default": 0, "min": 0}),
                "lora_strength": ("FLOAT", {"default": 0.0, "min": 0.0}),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("LORA_INFO",)
    FUNCTION = "process_lora_strength"
    CATEGORY = "sn0w"

    def process_lora_strength(self, lora_string, strength_increase, lora_strength):
        # Split the string by "-"
        lora_name, lora_code = lora_string.split('-')
        initial_strength = int(lora_code.lstrip('0') or '0')  # Convert to int, handle leading zeros

        # Append the lora strings with incremented strength
        lora_strings = [
            f"<lora:{lora_name}-{str(initial_strength + i * strength_increase).zfill(len(lora_code))}:{lora_strength:.1f}>"
            for i in range(4)  # Adjust the range to generate four Lora strings
        ]

        # Join the lora strings into a single string separated by semicolons
        lora_output = ';'.join(lora_strings)

        return (lora_output,)
