class SplitStringNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {"default": ""}),
                "separator": ("STRING", {"default": ";"}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING",)
    RETURN_NAMES = ("STRING_A", "STRING_B", "STRING_C", "STRING_D",)
    FUNCTION = "split_string"
    CATEGORY = "sn0w"

    def split_string(self, text, separator):
        # Split the text by the separator
        parts = text.split(separator)
        
        # Ensure there are exactly four parts
        # If not enough parts, extend with empty strings
        parts.extend([""] * (4 - len(parts)))
        
        # Return the first four parts
        return tuple(parts[:4])
