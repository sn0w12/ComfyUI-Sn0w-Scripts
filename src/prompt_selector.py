import os
import json

class PromptSelectNode:
    # Compute the directory path, ensuring cross-platform compatibility
    dir_path = os.path.dirname(os.path.realpath(__file__))
    if os.sep + "src" in dir_path:
        dir_path = dir_path.replace(os.sep + "src", "")
    json_path = os.path.join(dir_path, 'prompts.json')
    
    # Load prompt data from JSON file
    with open(json_path, 'r') as file:
        prompt_data = json.load(file)
    prompt_dict = {prompt['name']: prompt for prompt in prompt_data}

    @classmethod
    def INPUT_TYPES(cls):
        # Generate input types dynamically from the loaded prompts
        prompt_names = ['None'] + list(cls.prompt_dict.keys())
        return {
            "required": {
                "prompt": (prompt_names, ),
            },
        }

    # Define static properties for the class
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("PROMPT",)
    FUNCTION = "find_associated_string"
    CATEGORY = "sn0w"
        
    def find_associated_string(self, prompt):
        # Lookup the prompt and return the associated string
        char_item = self.prompt_dict.get(prompt)
        if char_item:
            prompt_string = char_item['prompt']
            if prompt_string:
                return (prompt_string, )
        return ("", )
