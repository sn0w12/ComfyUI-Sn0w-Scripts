import folder_paths

class LoraSelectorNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "lora": (['None'] + folder_paths.get_filename_list("loras"), ),
                "strength_increase": ("INT", {"default": 0, "min": 0}),
                "lora_strength": ("FLOAT", {"default": 1.0, "min": -10.0, "max": 10.0, "step": 0.01}),
                "total_loras": ("INT", {"default": 0, "min": 0}),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("LORA_INFO",)
    FUNCTION = "process_lora_strength"
    CATEGORY = "sn0w"

    def process_lora_strength(self, lora, strength_increase, lora_strength, total_loras):
        # Assuming `lora` is a file object with a .name attribute or similar
        lora_string = lora.split('\\')[-1].replace('.safetensors', '')

        # Split the string by "-"
        lora_name, lora_code = lora_string.split('-')
        initial_strength = int(lora_code.lstrip('0') or '0')  # Convert to int, handle leading zeros

        # Append the lora strings with incremented strength
        lora_strings = [
            f"<lora:{lora_name}-{str(initial_strength + i * strength_increase).zfill(len(lora_code))}:{lora_strength:.1f}>"
            for i in range(total_loras)  # Adjust the range to generate four Lora strings
        ]

        # Join the lora strings into a single string separated by semicolons
        lora_output = ';'.join(lora_strings)

        return (lora_output,)

