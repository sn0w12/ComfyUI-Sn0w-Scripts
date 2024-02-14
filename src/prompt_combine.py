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
        
        # Prepare a list to keep track of final tags to maintain order
        final_tags = []
        
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
                    continue  # Skip this tag
            
            # Include the tag if it hasn't been marked redundant or incompatible
            if tag not in tag_map and tag not in final_tags:
                final_tags.append(tag)
            elif tag in tag_map and tag_map[tag] not in final_tags:
                final_tags.append(tag_map[tag])

        # Join the final list of tags back into a string
        simplified_tags_string = ', '.join(final_tags)
        return simplified_tags_string

    def combine_string(self, string_a, string_b, string_c, string_d, separator):
        strings = [string_a, string_b, string_c, string_d]
        combined = []
        all_words = set()

        for string in strings:
            if string != "None" and isinstance(string, str):  # Ensure string is a non-None str
                string = string.strip()  # Remove leading/trailing whitespace

                # Remove separator at the end if it exists
                if string.endswith(separator.strip()):
                    string = string[:-len(separator.strip())]

                # Skip empty strings after processing and check for duplicates
                if string and string not in combined:
                    final_string = ""
                    words = string.split(", ")
                    # Remove duplicate words
                    for word in words:
                        if word not in all_words:
                            all_words.add(word)
                            final_string += (word + ", ")
                    # Remove the last separator and space if final_string is not empty
                    if final_string:
                        final_string = final_string[:-2]
                    combined.append(final_string) 

        # Join all parts with the separator and return as a tuple
        final_tags = self.simplify_tags(separator.join(combined))
        return (final_tags,)
