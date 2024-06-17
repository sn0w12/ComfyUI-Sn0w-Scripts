import os
import requests
from urllib.parse import urlparse, parse_qs

class GetGelbooruTagsNode:
    dir_path = os.path.dirname(os.path.realpath(__file__))
    tags_path = '../web/settings/tags/'
    files = ['body_tags.txt']

    for file in files:
        with open(os.path.abspath(os.path.join(dir_path, f'{tags_path}{file}')), 'r') as text_file:
            valid_tags = {line.strip().lower() for line in text_file}

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "url": ("STRING", {"default": ""}),
                "separator": ("STRING", {"default": ", "}),
                "replace_underscore": ("BOOLEAN", {"default": True}),
                "characteristics_tags": ("BOOLEAN", {"default": True}),
                "scene_tags": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                "api_key (optional)": ("STRING", {"default": ""}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("PROMPT",)
    FUNCTION = "get_gelbooru_tags"
    CATEGORY = "sn0w"

    def filter_tags(self, input_string, separator, characteristics_tags, scene_tags):
        if (characteristics_tags and scene_tags):
            return input_string

        # Split the input string by the separator
        tags = input_string.split(separator)
        return_string = ""

        def add_tags_to_return_string(tag):
            nonlocal return_string
            if return_string:
                return_string += separator
            return_string += tag.strip()

        for tag in tags:
            processed_tag = tag.replace('\\', '').strip().replace(' ', '_').lower()

            if processed_tag in self.valid_tags:
                if (characteristics_tags):
                    add_tags_to_return_string(tag)
            else:
                if (scene_tags):
                    add_tags_to_return_string(tag)

        return return_string
        
    def get_gelbooru_tags(self, url, separator, replace_underscore, characteristics_tags, scene_tags, **kwargs):
        API_URL = "https://gelbooru.com/index.php?page=dapi&s=post&q=index&json=1"

        if (kwargs["api_key (optional)"]):
            api_key = kwargs["api_key (optional)"]
            if (api_key.startswith("&api_key=")):
                api_key[9:]

            API_URL = f"{API_URL}&api_key={api_key}"

        if url.startswith("http"):
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            id_value = query_params.get('id', [None])[0]
        else:
            id_value = url

        final_api_url = API_URL + f"&id={id_value}"

        r = requests.get(url = final_api_url)
        data = r.json()
        tags = data['post'][0]['tags']
        tags = tags.replace(" ", separator)
        if (replace_underscore):
            tags = tags.replace("_", " ")

        tags = self.filter_tags(tags, separator, characteristics_tags, scene_tags)
        return (tags,)
