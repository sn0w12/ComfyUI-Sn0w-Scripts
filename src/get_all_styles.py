import folder_paths

class GetStylesNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "xl": ("BOOLEAN", {"default": False},),
                "lora_strength": ("FLOAT", {"default": 1.0, "min": -10.0, "max": 10.0, "step": 0.01}),
                "add_default_generation": ("BOOLEAN", {"default": False},),
            },
        }

    RETURN_TYPES = ("STRING", "INT",)
    RETURN_NAMES = ("LORA_INFO", "TOTAL_LORAS",)
    FUNCTION = "get_styles"
    CATEGORY = "sn0w"
        
    def get_styles(self, xl, lora_strength, add_default_generation):
        # Select the appropriate lora list based on 'xl'
        if xl:
            lora_paths = folder_paths.get_filename_list("loras_xl")
        else:
            lora_paths = folder_paths.get_filename_list("loras_15")

        loras = []
        for lora in lora_paths:
            if "style" in lora.lower():
                # Extract the lora string from the file path
                lora_string = lora.split('\\')[-1].replace('.safetensors', '')
                loras.append(f"<lora:{lora_string}:{lora_strength:.1f}>")

        total_loras = len(loras)
        if add_default_generation:
            total_loras += 1
            loras.append("Nothing")

        # Join the lora strings into a single string separated by semicolons
        lora_output = ';'.join(loras)

        return (lora_output, total_loras, )
