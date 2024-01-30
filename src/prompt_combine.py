class CombineStringNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "string_a": ("STRING", {"default": ""}),
                "string_b": ("STRING", {"default": ""}),
                "string_c": ("STRING", {"default": ""}),
                "string_d": ("STRING", {"default": ""}),
                "separator": ("STRING", {"default": ", "}),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("PROMPT",)
    FUNCTION = "combine_string"
    CATEGORY = "sn0w"

    def combine_string(self, string_a, string_b, string_c, string_d, separator):
        strings = [string_a, string_b, string_c, string_d]
        combined = []

        for string in strings:
            if string is not None and isinstance(string, str):  # Ensure string is a non-None str
                string = string.strip()  # Remove leading/trailing whitespace

                # Remove separator at the end if it exists
                if string.endswith(separator.strip()):
                    string = string[:-len(separator)]

                # Skip empty strings after processing
                if string:
                    combined.append(string)

        # Join all parts with the separator and return as a tuple
        return (separator.join(combined),)
