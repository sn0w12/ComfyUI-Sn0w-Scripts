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

        initial_font_size = 16
        tolerance = 50
        font_size = initial_font_size
        estimated_char_width = font_size * 0.6

        while True:
            estimated_text_width = text_length * estimated_char_width
            width_difference = abs(estimated_text_width - width)

            if width_difference <= tolerance:
                break
            elif estimated_text_width < width - tolerance:
                font_size += 1
            elif estimated_text_width > width + tolerance:
                font_size -= 1

            estimated_char_width = font_size * 0.6

        return (font_size,)
