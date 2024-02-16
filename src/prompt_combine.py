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
        # Broad categories for directionally sensitive visibility
        incompatible_categories = {
            'from behind': {'eyes', 'face', 'mouth', 'teeth', 'front'},
        }

        # Attempt to identify the direction the subject is facing
        facing_direction = None
        for direction in incompatible_categories.keys():
            if direction in tags_string:
                facing_direction = direction
                break

        # Split the input string into a list of tags
        tags = tags_string.split(',')
        
        # Remove leading and trailing whitespaces in each tag
        tags = [tag.strip() for tag in tags]
        
        # Prepare lists to keep track of final tags to maintain order and removed tags
        final_tags = []
        removed_tags = []  # New list to track removed tags
        
        # Use a dictionary to map each tag to a more descriptive version if it exists
        tag_map = {}
        
        for tag in tags:
            for potential_superior in tags:
                if tag != potential_superior and tag in potential_superior:
                    tag_parts = set(tag.split(' '))
                    superior_parts = set(potential_superior.split(' '))
                    if tag_parts.issubset(superior_parts) and not tag_parts == superior_parts:
                        tag_map[tag] = potential_superior
                        break
        
        for tag in tags:
            # Skip tags based on facing direction and general categories
            if facing_direction:
                # Check if the tag or its descriptive version falls into any incompatible category
                if any(category in tag for category in incompatible_categories[facing_direction]):
                    removed_tags.append(tag)  # Track removed tag
                    continue  # Skip this tag
            
            # Include the tag if it hasn't been marked redundant or incompatible
            if tag not in tag_map and tag not in final_tags:
                final_tags.append(tag)
            elif tag in tag_map:
                if tag_map[tag] not in final_tags:
                    final_tags.append(tag_map[tag])
                if tag not in final_tags:  # If the original tag is not included in the final list, it's removed
                    removed_tags.append(tag)
                    
        # Remove duplicates in the removed_tags list by converting it to a set and back to a list
        removed_tags = list(set(removed_tags))

        # Join the final list of tags back into a string
        simplified_tags_string = ', '.join(final_tags)
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