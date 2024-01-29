import folder_paths
import json

class LoraStackerNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "lora_a": (['None'] + folder_paths.get_filename_list("loras"), ),
                "lora_strength_a": ("FLOAT", {"default": 1.0, "min": -10.0, "max": 10.0, "step": 0.01}),
                "lora_b": (['None'] + folder_paths.get_filename_list("loras"), ),
                "lora_strength_b": ("FLOAT", {"default": 1.0, "min": -10.0, "max": 10.0, "step": 0.01}),
                "lora_c": (['None'] + folder_paths.get_filename_list("loras"), ),
                "lora_strength_c": ("FLOAT", {"default": 1.0, "min": -10.0, "max": 10.0, "step": 0.01}),
                "lora_d": (['None'] + folder_paths.get_filename_list("loras"), ),
                "lora_strength_d": ("FLOAT", {"default": 1.0, "min": -10.0, "max": 10.0, "step": 0.01}),
                "add_default_generation": ("BOOLEAN", {"default": False},),
            },
        }

    RETURN_TYPES = ("STRING", "INT","BOOLEAN",)
    RETURN_NAMES = ("LORA_INFO", "TOTAL_LORAS","ADD_DEFAULT_GENERATION",)
    FUNCTION = "process_lora_strength"
    CATEGORY = "sn0w"
    OUTPUT_NODE = True

    def process_lora_strength(self, lora_a, lora_strength_a, lora_b, lora_strength_b, lora_c, lora_strength_c, lora_d, lora_strength_d, add_default_generation):
        # Function to extract lora string and format with strength
        def format_lora(lora, strength):
            lora_string = lora.split('\\')[-1].replace('.safetensors', '')
            return f"<lora:{lora_string}:{strength:.1f}>"

        # Process each lora and its strength
        loras = [
            format_lora(lora_a, lora_strength_a),
            format_lora(lora_b, lora_strength_b),
            format_lora(lora_c, lora_strength_c),
            format_lora(lora_d, lora_strength_d)
        ]

        # Initialize total_loras count
        total_loras = 4

        # Handle additional generation if required
        if add_default_generation:
            total_loras += 1
            loras.append("Nothing")

        # Join the lora strings into a single string separated by semicolons
        lora_output = ';'.join(loras)

        return (lora_output, total_loras, add_default_generation, )

