import os
import folder_paths


class LoraStackerNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "lora_a": (["None"] + folder_paths.get_filename_list("loras"),),
                "lora_strength_a": ("FLOAT", {"default": 1.0, "min": -10.0, "max": 10.0, "step": 0.01}),
                "lora_b": (["None"] + folder_paths.get_filename_list("loras"),),
                "lora_strength_b": ("FLOAT", {"default": 1.0, "min": -10.0, "max": 10.0, "step": 0.01}),
                "lora_c": (["None"] + folder_paths.get_filename_list("loras"),),
                "lora_strength_c": ("FLOAT", {"default": 1.0, "min": -10.0, "max": 10.0, "step": 0.01}),
                "lora_d": (["None"] + folder_paths.get_filename_list("loras"),),
                "lora_strength_d": ("FLOAT", {"default": 1.0, "min": -10.0, "max": 10.0, "step": 0.01}),
                "add_default_generation": ("BOOLEAN", {"default": False}),
            },
        }

    RETURN_TYPES = ("STRING", "INT")
    RETURN_NAMES = ("LORA_INFO", "TOTAL_LORAS")
    FUNCTION = "process_loras"
    CATEGORY = "sn0w/lora"
    OUTPUT_NODE = True

    def process_loras(
        self, lora_a, lora_strength_a, lora_b, lora_strength_b, lora_c, lora_strength_c, lora_d, lora_strength_d, add_default_generation
    ):
        # Function to extract lora string and format with strength
        def format_lora(lora, strength):
            if lora.lower() == "none":  # Skip "None" loras
                return None
            lora_string = os.path.splitext(os.path.basename(lora))[0]
            return f"<lora:{lora_string}:{strength:.1f}>"

        # Process each lora and its strength, filtering out "None"
        loras = [
            format_lora(lora_a, lora_strength_a),
            format_lora(lora_b, lora_strength_b),
            format_lora(lora_c, lora_strength_c),
            format_lora(lora_d, lora_strength_d),
        ]

        # Filter out None values from the loras list
        loras = [lora for lora in loras if lora is not None]

        # Initialize total_loras count based on filtered loras
        total_loras = len(loras)

        # Handle additional generation if required
        if add_default_generation:
            total_loras += 1
            loras.append("Nothing")

        # Join the lora strings into a single string separated by semicolons
        lora_output = ";".join(loras)

        return (lora_output, total_loras)
