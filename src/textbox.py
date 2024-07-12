class TextboxNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {"text": ("STRING", {"default": "", "multiline": True})},
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "run"

    CATEGORY = "utils"

    def run(self, text):
        return (text,)
