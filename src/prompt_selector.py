import os
import json
from transformers import pipeline


class PromptSelectNode:
    prompts = {}

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
                "skip_classification": ("BOOLEAN", {"default": False}),
            },
        }

    # Define static properties for the class
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("POSITIVE", "NEGATIVE")
    FUNCTION = "find_chosen_prompts"
    CATEGORY = "sn0w"

    def find_chosen_prompts(self, prompt, model, skip_classification):
        if skip_classification:
            positive_prompt = self.prompts.get(model, {}).get("positive", "")
            negative_prompt = self.prompts.get(model, {}).get("negative", "")
            return (positive_prompt, negative_prompt)

        classifier = pipeline("sentiment-analysis", model="michellejieli/NSFW_text_classifier")
        result = classifier(prompt)

        is_nsfw = result[0]["label"] == "NSFW"
        if is_nsfw:
            positive_prompt = self.prompts.get(model, {}).get("positive_nsfw", "")
            negative_prompt = self.prompts.get(model, {}).get("negative", "")
        else:
            positive_prompt = self.prompts.get(model, {}).get("positive", "")
            negative_prompt = self.prompts.get(model, {}).get("negative_sfw", "")

        return (positive_prompt, negative_prompt)
