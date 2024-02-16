import os
import json
import re
import folder_paths
from nodes import LoraLoader
from .print_sn0w import print_sn0w

class LoadLoraConceptNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": ("MODEL",),
                "clip": ("CLIP", ),
                "prompt": ("STRING", {"default": ""}),
                "xl": ("BOOLEAN", {"default": False},),
                "lora_strength": ("FLOAT", {"default": 1.0, "min": -10.0, "max": 10.0, "step": 0.01}),
                "separator": ("STRING", {"default": ", "}),
            },
        }

    RETURN_TYPES = ("MODEL", "CLIP",)
    RETURN_NAMES = ("MODEL", "CLIP",)
    FUNCTION = "find_and_apply_lora"
    CATEGORY = "sn0w"

    def clean_string(self, input_string):
        cleaned_string = re.sub(r'[\\()]', '', input_string)
        cleaned_string = re.sub(r':\d+(\.\d+)?', '', cleaned_string)
        cleaned_string = re.sub(r',$', '', cleaned_string.strip())
        return cleaned_string.lower()
    
    def similarity_ratio(self, str1, str2):
        """
        Calculates a basic similarity ratio between two strings based on the length
        of the longest common subsequence. This is a simplified and less accurate
        approach compared to algorithms like Levenshtein distance.

        Args:
        - str1: First string.
        - str2: Second string.

        Returns:
        - A percentage representing the similarity between the two strings.
        """
        def longest_common_subsequence(s1, s2):
            m, n = len(s1), len(s2)
            dp = [[0] * (n + 1) for _ in range(m + 1)]

            for i in range(1, m + 1):
                for j in range(1, n + 1):
                    if s1[i - 1] == s2[j - 1]:
                        dp[i][j] = dp[i - 1][j - 1] + 1
                    else:
                        dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
            
            return dp[m][n]

        # Normalize and prepare strings (remove file extension, replace underscores)
        normalized_str1 = str1.replace(".safetensors", "").replace("_", " ").lower()
        normalized_str2 = str2.replace(".safetensors", "").replace("_", " ").lower()

        # Calculate the length of the longest common subsequence
        lcs_len = longest_common_subsequence(normalized_str1, normalized_str2)
        max_len = max(len(normalized_str1), len(normalized_str2))

        # Return the similarity ratio
        return (lcs_len / max_len) * 100 if max_len > 0 else 0
        
    def find_and_apply_lora(self, model, clip, prompt, xl, lora_strength, separator):
        if prompt is None:
            prompt = ''
        prompt_parts = [self.clean_string(part) for part in prompt.split(separator)]

        # Retrieve the full list of lora paths
        full_lora_paths = folder_paths.get_filename_list("loras")
        lora_paths = folder_paths.get_filename_list("loras_xl" if xl else "loras_15")
        # lora_paths = [path for path in filtered_lora_paths if "concept" in path.lower()]

        found_full_lora_paths = []

        for prompt_part in prompt_parts:
            for lora_path in lora_paths:
                lora_filename = os.path.split(lora_path)[-1].lower()
                # Remove file extension and replace underscores with spaces for comparison
                processed_lora_filename = lora_filename.replace(".safetensors", "").replace("_", " ")
                # Calculate similarity ratio
                similarity_ratio = self.similarity_ratio(prompt_part, processed_lora_filename)
                if similarity_ratio >= 85:
                    # Find the full path from the full_lora_paths list
                    for full_path in full_lora_paths:
                        if lora_filename in full_path.lower():
                            found_full_lora_paths.append(full_path)
                            break

        # Print and apply found lora paths
        for path in found_full_lora_paths:
            print_sn0w(path)
            model, clip = LoraLoader().load_lora(model, clip, path, lora_strength, lora_strength)

        return (model, clip, )