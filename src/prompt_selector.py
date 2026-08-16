import os
import json


class PromptSelectNode:
    prompts = {}
    classifier = None

    @classmethod
    def load_prompts(cls):
        # Determine the base directory path without the src subdirectory
        dir_path = os.path.dirname(os.path.realpath(__file__))
        if os.sep + "src" in dir_path:
            dir_path = dir_path.replace(os.sep + "src", "")

        json_path = os.path.join(dir_path, "prompts.json")
        with open(json_path, "r", encoding="utf-8") as file:
            cls.prompts = json.load(file)

    @classmethod
    def INPUT_TYPES(cls):
        cls.load_prompts()
        model_names = list(cls.prompts.keys())
        return {
            "required": {
                "prompt": ("STRING", {"default": ""}),
                "model": (model_names,),
                "separator": ("STRING", {"default": ", "}),
            },
        }

    NSFW_WORDS = [
        "uncensored",
        "penis",
        "sex",
        "completely nude",
        "genitals",
        "vagina",
        "pussy",
        "dick",
        "cock",
        "asshole",
        "masturbat",
        "orgasm",
        "ejaculat",
        "threesome",
        "gangbang",
        "orgy",
        "incest",
        "squirt",
        "creampie",
        "futanari",
        "erection",
        "dildo",
        "vibrator",
        "pegging",
    ]

    def is_nsfw(self, prompt):
        return any(word.lower() in prompt.lower() for word in self.NSFW_WORDS if word)

    # Define static properties for the class
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("POSITIVE", "NEGATIVE")
    FUNCTION = "find_chosen_prompts"
    CATEGORY = "sn0w"

    def find_chosen_prompts(self, prompt, model, separator: str):
        positive_prompt = self.prompts.get(model, {}).get("positive", "")
        negative_prompt = self.prompts.get(model, {}).get("negative", "")

        is_nsfw = self.is_nsfw(prompt)
        if is_nsfw:
            if "uncensored" not in prompt:
                positive_prompt = positive_prompt + separator + "uncensored"
            negative_prompt = (
                negative_prompt
                + separator
                + separator.join(["censored", "bar censor", "blur censor", "mosaic censoring"])
            )

        return (positive_prompt, negative_prompt)
