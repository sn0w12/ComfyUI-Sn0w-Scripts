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
            if string:  # Skip empty strings
                # Add the string to the combined list, appending separator if needed
                if not string.endswith(separator):
                    string += separator
                combined.append(string)

        # Join all parts and return as a tuple
        return (''.join(combined),)
