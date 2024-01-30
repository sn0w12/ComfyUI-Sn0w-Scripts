class GetFontSizeNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "width": ("INT", {"default": 0, "min": 0}),
                "lora_info": ("STRING", {"default": ""}),
            },
        }

    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("FONT_SIZE",)
    FUNCTION = "estimate_font_size"
    CATEGORY = "sn0w"
        
    def estimate_font_size(self, width, lora_info):
        loras = lora_info.split(";")
        longest_string = max(loras, key=len)
        text_length = len(longest_string)

        tolerance = 50
        estimated_char_width = lambda font_size: font_size * 0.5

        # Start with a guess that is proportionate to the width
        font_size = width // (text_length * 0.5)
        step_size = max(1, font_size // 2)  # Start with a larger step size

        while True:
            estimated_text_width = text_length * estimated_char_width(font_size)
            width_difference = abs(estimated_text_width - width)

            if width_difference <= tolerance:
                break
            elif estimated_text_width < width - tolerance:
                font_size += step_size
            else:
                font_size -= step_size

            # Reduce the step size as we get closer to the target width
            if step_size > 1 and width_difference < width * 0.1:
                step_size //= 2

        return (int(font_size),)
