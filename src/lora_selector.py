import folder_paths
import json

class LoraSelectorNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "lora": (['None'] + folder_paths.get_filename_list("loras"), ),
                "lora_strength": ("FLOAT", {"default": 1.0, "min": -10.0, "max": 10.0, "step": 0.01}),
                "highest_lora": ("INT", {"default": 0, "min": 0}),
                "total_loras": ("INT", {"default": 0, "min": 0}),
                "add_default_generation": ("BOOLEAN", {"default": False},),
            },
        }

    RETURN_TYPES = ("STRING", "INT","BOOLEAN",)
    RETURN_NAMES = ("LORA_INFO", "TOTAL_LORAS","ADD_DEFAULT_GENERATION",)
    FUNCTION = "process_lora_strength"
    CATEGORY = "sn0w"
    OUTPUT_NODE = True

    def process_lora_strength(self, lora, lora_strength, highest_lora, total_loras, add_default_generation):
        # Extract the lora string from the file path
        lora_string = lora.split('\\')[-1].replace('.safetensors', '')

        # Extract the initial strength from the lora string
        lora_name, lora_code = lora_string.split('-')
        initial_strength = int(lora_code.lstrip('0') or '0')  # Convert to int, handle leading zeros

        # Determine the range and increment for each lora strength
        strength_range = highest_lora - initial_strength
        strength_increment = max(1, round(strength_range / (total_loras - 1))) if total_loras > 1 else 0

        # Generate the lora strings
        lora_strings = []
        for i in range(total_loras):
            current_strength = min(initial_strength + i * strength_increment, highest_lora)
            lora_strength_string = str(current_strength).zfill(len(lora_code))
            lora_strings.append(f"<lora:{lora_name}-{lora_strength_string}:{lora_strength:.1f}>")

        # Handle additional generation if required
        if add_default_generation:
            total_loras += 1
            lora_strings.append("Nothing")
                
        # Join the lora strings into a single string separated by semicolons
        lora_output = ';'.join(lora_strings)

        return (lora_output, total_loras, add_default_generation,)

