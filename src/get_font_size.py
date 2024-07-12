class GetFontSizeNode:
    """
    Estimate the font size needed to fit text over an image.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "text": ("STRING", {"default": ""}),
            },
        }

    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("FONT_SIZE",)
    FUNCTION = "estimate_font_size"
    CATEGORY = "sn0w"

    def estimate_font_size(self, image, text):
        text = text.split(";")
        longest_string = max(text, key=len)
        text_length = len(longest_string)

        tolerance = 50

        def estimated_char_width(font_size):
            return font_size * 0.5

        # Attempt to determine if the image is a batch or a single image
        try:
            # Assume image is a batch and try to get the width of the first image
            width = image[0].shape[1]  # Image batch format: [N, C, H, W]
        except TypeError:
            # If it's not a batch, get the width as a single image
            width = image.shape[1]  # Single image format: [C, H, W]
        # Start with a guess that is proportionate to the width
        font_size = width // (text_length * 0.5)
        step_size = max(1, font_size // 2)  # Start with a larger step size

        while True:
            estimated_text_width = text_length * estimated_char_width(font_size)
            width_difference = abs(estimated_text_width - width)

            if width_difference <= tolerance:
                break
            if estimated_text_width < width - tolerance:
                font_size += step_size
            else:
                font_size -= step_size

            # Reduce the step size as we get closer to the target width
            if step_size > 1 and width_difference < width * 0.1:
                step_size //= 2

        return (int(font_size),)
