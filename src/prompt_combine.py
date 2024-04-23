import re
from .sn0w import ConfigReader

class CombineStringNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "separator": ("STRING", {"default": ", "}),
                "simplify": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                "string_a": ("STRING", {"default": ""}),
                "string_b": ("STRING", {"default": ""}),
                "string_c": ("STRING", {"default": ""}),
                "string_d": ("STRING", {"default": ""}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING",)
    RETURN_NAMES = ("PROMPT", "REMOVED_TAGS",)
    FUNCTION = "combine_string"
    CATEGORY = "sn0w"

    def simplify_tags(self, tags_string, separator):
        # dictionary defines categories with specific rules for removing or keeping tags.
        # remove contains phrases that, if found in a prompt, suggest the tag should be removed.
        # keep contains phrases that, if found in a prompt, indicate the tag should be kept.
        # if a remove tag is found and no keep tag is found, it will remove all mentions of the category except the tags found in remove.
        # keep always takes priority over remove, if any tag in keep is found nothing will be removed
        special_phrases = {
            'eye': {
                'remove': ['covering eyes', 'over eyes', 'covered eyes', 'covering face', 'covering own eyes', 'facing away', 'blindfold', 'head out of frame'],
                'keep': ['looking at viewer']
            },
            'sclera': {
                'remove': ['covering eyes', 'over eyes', 'covered eyes', 'covering face', 'covering own eyes', 'facing away', 'blindfold', 'head out of frame'],
                'keep': ['looking at viewer']
            },
            'mouth': {
                'remove': ['facing away'],
                'keep': ['looking at viewer']
            },
            'teeth': {
                'remove': ['facing away'],
                'keep': ['looking at viewer']
            },
        }

        # Compile regex patterns outside of loops
        parenthesized_pattern = re.compile(r'\([^()]*\)')
        numeric_tag_pattern = re.compile(r'\b\d+\+?(girls?|boys?)\b')
        
        # Extract parenthesized parts
        parenthesized_parts = []
        def extract_parenthesized(match):
            parenthesized_parts.append(match.group())
            return f"\0{len(parenthesized_parts)-1}\0"
        
        modified_tags_string = re.sub(parenthesized_pattern, extract_parenthesized, tags_string)

        tags = [tag.strip() for tag in modified_tags_string.split(separator)]
        final_tags = []
        removed_tags = set()
        tag_map = {}

        for tag in tags:
            for potential_superior in tags:
                if tag in potential_superior and tag != potential_superior:
                    tag_map[tag] = potential_superior

        global_keep_conditions = {
            keyword: any(keep_phrase in tags_string for keep_phrase in conditions['keep'])
            for keyword, conditions in special_phrases.items()
        }

        non_removable_tags = {
            tag
            for tag in tags
            for keyword, conditions in special_phrases.items()
            if any(remove_phrase in tag for remove_phrase in conditions['remove'])
        }

        for tag in tags:
            superior_tag = tag_map.get(tag)
            if superior_tag and superior_tag not in final_tags:
                removed_tags.add(tag)
                continue

            should_remove_tag = False
            for keyword, conditions in special_phrases.items():
                if keyword in tag and not global_keep_conditions[keyword] and any(remove_phrase in tags_string for remove_phrase in conditions['remove']) and tag not in non_removable_tags:
                    should_remove_tag = True
                    break

            if should_remove_tag:
                removed_tags.add(tag)
            else:
                # Avoid adding duplicates
                if tag not in final_tags:
                    final_tags.append(tag)

        # Reinsert parenthesized parts and handle removed tags
        final_tags_with_parentheses = []
        for tag in final_tags:
            while "\0" in tag:
                index = int(tag[tag.find("\0")+1:tag.rfind("\0")])
                tag = tag.replace(f"\0{index}\0", parenthesized_parts[index], 1)
            final_tags_with_parentheses.append(tag)

        animagine_formatting = ConfigReader.get_setting('sn0w.PromptFormat', False)

        if animagine_formatting:
            numeric_tags = [tag for tag in final_tags_with_parentheses if numeric_tag_pattern.match(tag)]
            non_numeric_tags = [tag for tag in final_tags_with_parentheses if not numeric_tag_pattern.match(tag)]

            prioritized_final_tags = numeric_tags + non_numeric_tags
        else:
            prioritized_final_tags = final_tags_with_parentheses

        simplified_tags_string = separator.join(prioritized_final_tags).strip(separator)
        removed_tags_string = separator.join(removed_tags).strip(separator)

        return simplified_tags_string, removed_tags_string

    def combine_string(self, separator, simplify, **kwargs):
        # Collect strings that are not None and strip them
        strings = [s.strip() for s in (kwargs.get(f"string_{char}") for char in ['a', 'b', 'c', 'd']) if s]
        removed_tags = ""

        all_words = set()
        combined = []

        for string in strings:
            if string != "None" and isinstance(string, str):
                string = string.strip()
                if string.endswith(separator.strip()):
                    string = string[:-len(separator.strip())]
                if string and string not in combined:
                    final_string = ""
                    words = string.split(separator)
                    for word in words:
                        if word not in all_words:
                            all_words.add(word)
                            final_string += (word + separator)
                    if final_string:
                        final_string = final_string[:-len(separator)]
                    combined.append(final_string)

        if simplify:
            final_tags, removed_tags = self.simplify_tags(separator.join(combined), separator)
        else:
            final_tags = separator.join(combined)

        return (final_tags, removed_tags,)