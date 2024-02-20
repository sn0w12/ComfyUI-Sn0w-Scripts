import re

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

    def simplify_tags(self, tags_string):
        # Configuration for special phrases
        special_phrases = {
            'eye': {
                'remove': ['covering eyes', 'over eyes', 'covered eyes', 'covering face', 'covering own eyes', 'facing away'],
                'keep': ['looking at viewer']
            },
            'sclera': {
                'remove': ['covering eyes', 'over eyes', 'covered eyes', 'covering face', 'covering own eyes', 'facing away'],
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

        # Regular expression to match parenthesized parts
        parenthesized_pattern = re.compile(r'\([^()]*\)')
        parenthesized_parts = []

        # Extract and temporarily remove parenthesized parts, storing their positions
        def extract_parenthesized(match):
            parenthesized_parts.append(match.group(0))
            return "\0"  # Use a unique placeholder to mark the position

        modified_tags_string = re.sub(parenthesized_pattern, extract_parenthesized, tags_string)

        tags = [tag.strip() for tag in modified_tags_string.split(',')]
        final_tags = []
        removed_tags = []
        tag_map = {}

        # Mapping non-superior tags to their superior counterparts
        for tag in tags:
            for potential_superior in tags:
                if tag != potential_superior and tag in potential_superior:
                    tag_parts = set(tag.split(' '))
                    superior_parts = set(potential_superior.split(' '))
                    if tag_parts.issubset(superior_parts) and tag_parts != superior_parts:
                        tag_map[tag] = potential_superior

        # Check for 'keep' conditions globally
        global_keep_conditions = {keyword: any(keep_phrase in tags_string for keep_phrase in conditions['keep']) for keyword, conditions in special_phrases.items()}

        # Identify tags that should not be removed because they are contained in 'remove' phrases
        non_removable_tags = set()
        for tag in tags:
            for keyword, conditions in special_phrases.items():
                if any(remove_phrase in tag for remove_phrase in conditions['remove']):
                    non_removable_tags.add(tag)

        for tag in tags:
            if tag in tag_map:
                # Append non-superior tags to removed_tags if their superior counterparts are not already included
                if tag_map[tag] not in final_tags:
                    removed_tags.append(tag)
                continue

            should_remove_tag = False
            for keyword, conditions in special_phrases.items():
                if keyword in tag:
                    if not global_keep_conditions[keyword] and any(remove_phrase in tags_string for remove_phrase in conditions['remove']) and tag not in non_removable_tags:
                        should_remove_tag = True
                        break

            if should_remove_tag:
                removed_tags.append(tag)
            else:
                final_tags.append(tag)

        # Ensure tags explicitly listed in "remove" are not removed
        for keyword, conditions in special_phrases.items():
            for remove_tag in conditions['remove']:
                if remove_tag in removed_tags:
                    removed_tags.remove(remove_tag)
                    final_tags.append(remove_tag)

        # Remove duplicates in the removed_tags list by converting it to a set and back to a list
        removed_tags = list(set(removed_tags))

        # Reinsert parenthesized parts back into their original positions
        final_tags_list = modified_tags_string.split(',')
        final_tags_with_parentheses = []
        for tag in final_tags_list:
            if "\0" in tag:  # If placeholder is found, replace it with the original parenthesized part
                tag = tag.replace("\0", parenthesized_parts.pop(0), 1)
            final_tags_with_parentheses.append(tag.strip())
        
        simplified_tags_string = ', '.join(final_tags_with_parentheses)

        return simplified_tags_string, removed_tags

    def combine_string(self, separator, simplify, **kwargs):
        strings = [kwargs.get(f"string_{char}") for char in ['a', 'b', 'c', 'd'] if kwargs.get(f"string_{char}") is not None]
        combined = []
        all_words = set()
        removed_tags = ""

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
            final_tags, removed_tags = self.simplify_tags(separator.join(combined))
        else:
            final_tags = separator.join(combined)
        return (final_tags, removed_tags,)