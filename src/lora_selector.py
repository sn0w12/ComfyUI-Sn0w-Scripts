import os
import folder_paths

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

    RETURN_TYPES = ("STRING", "INT",)
    RETURN_NAMES = ("LORA_INFO", "TOTAL_LORAS",)
    FUNCTION = "process_lora_strength"
    CATEGORY = "sn0w/lora"
    OUTPUT_NODE = True

    def process_lora_strength(self, lora, lora_strength, highest_lora, total_loras, add_default_generation):
        # Get the list of lora filenames
        lora_filenames = folder_paths.get_filename_list("loras")
        lora_filenames = [os.path.basename(filename) for filename in lora_filenames]  # Extracting just the filename

        # Extract the lora string from the file path
        lora_string = os.path.splitext(os.path.basename(lora))[0]

        # Check if the lora_string contains a hyphen and split accordingly
        if '-' in lora_string:
            lora_name, lora_code = lora_string.rsplit('-', 1)
            initial_strength = int(lora_code.lstrip('0') or '0')  # Convert to int, handle leading zeros
        else:
            lora_name = lora_string
            lora_code = ''
            initial_strength = 0

        # Determine the range and increment for each lora strength
        strength_range = highest_lora - initial_strength
        strength_increment = max(1, round(strength_range / (total_loras - 1))) if total_loras > 1 else 0

        # Generate the lora strings
        lora_strings = []
        for i in range(total_loras):
            current_strength = min(initial_strength + i * strength_increment, highest_lora)
            lora_strength_string = str(current_strength).zfill(len(lora_code))
            full_lora_name = f"{lora_name}-{lora_strength_string}.safetensors"

            # Check if the lora exists in the folder paths, if not, check just lora_name
            if full_lora_name in lora_filenames:
                lora_strings.append(f"<lora:{lora_name}-{lora_strength_string}:{lora_strength:.1f}>")
            elif f"{lora_name}.safetensors" in lora_filenames:
                lora_strings.append(f"<lora:{lora_name}:{lora_strength:.1f}>")
            else:
                # Handle the case where the lora is not found
                lora_strings.append(f"<lora not found:{lora_name}-{lora_strength_string}>")

        # Handle additional generation if required
        if add_default_generation:
            total_loras += 1
            lora_strings.append("Nothing")

        # Join the lora strings into a single string separated by semicolons
        lora_output = ';'.join(lora_strings)

        return (lora_output, total_loras)
