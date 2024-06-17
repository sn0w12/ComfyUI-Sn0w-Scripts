import os
import re

class GetFaceTags:
    dir_path = os.path.dirname(os.path.realpath(__file__))
    head_tags_path = os.path.abspath(os.path.join(dir_path, '../web/settings/tags/head_tags.txt'))

    # Read the head tags
    with open(head_tags_path, 'r') as file:
        valid_tags = {line.strip().lower() for line in file}

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input_string": ("STRING", {"default": ""}),
                "separator": ("STRING", {"default": ", "}),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("tags",)
    FUNCTION = "process_tags"
    CATEGORY = "sn0w"
        
    def process_tags(self, input_string, separator):
        # Split the input string by the separator
        tags = input_string.split(separator)

        # Initialize the return string
        return_string = ""

        # Process each tag
        for tag in tags:
            # Remove the :number.number) part if it exists
            tag = re.sub(r':\d+\.\d+\)', '', tag)

            # Remove the leading ( if it exists
            if tag.startswith('('):
                tag = tag[1:]

            # Remove backslashes, trim trailing spaces, and replace spaces with underscores
            processed_tag = tag.replace('\\', '').strip().replace(' ', '_').lower()

            # Check if the tag is in the list of valid tags
            if processed_tag in self.valid_tags:
                # Add the original tag (trimmed) to the return string
                if return_string:
                    return_string += separator
                return_string += tag.strip()

        return (return_string,)
