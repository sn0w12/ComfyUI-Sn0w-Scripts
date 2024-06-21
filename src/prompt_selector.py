import os
import json

class PromptSelectNode:
    positive_prompts = {}
    negative_prompts = {}

    @classmethod
    def load_prompts(cls):
        # Determine the base directory path without the src subdirectory
        dir_path = os.path.dirname(os.path.realpath(__file__))
        if os.sep + "src" in dir_path:
            dir_path = dir_path.replace(os.sep + "src", "")

        # Define the path to the JSON file containing prompts
        json_path = os.path.join(dir_path, 'prompts.json')

        # Load prompts from the JSON file
        with open(json_path, 'r') as file:
            prompts = json.load(file)
        
        # Separate positive and negative prompts into dictionaries
        cls.positive_prompts = {item['name']: item['prompt'] for item in prompts[0]['positive']}
        cls.negative_prompts = {item['name']: item['prompt'] for item in prompts[0]['negative']}

    @classmethod
    def INPUT_TYPES(cls):
        cls.load_prompts()
        # Generate input types dynamically from the loaded prompts
        positive_prompt_names = ['None'] + list(cls.positive_prompts.keys())
        negative_prompt_names = ['None'] + list(cls.negative_prompts.keys())
        return {
            "required": {
                "positive": (positive_prompt_names, ),
                "negative": (negative_prompt_names, ),
            },
        }

    # Define static properties for the class
    RETURN_TYPES = ("STRING", "STRING",)
    RETURN_NAMES = ("POSITIVE", "NEGATIVE",)
    FUNCTION = "find_chosen_prompts"
    CATEGORY = "sn0w"
        
    def find_chosen_prompts(self, positive, negative):
        # Lookup the prompt name in both positive and negative dictionaries and return the associated strings
        positive_prompt = self.positive_prompts.get(positive, "")
        negative_prompt = self.negative_prompts.get(negative, "")
        return (positive_prompt, negative_prompt,)
