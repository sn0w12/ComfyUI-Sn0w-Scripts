import folder_paths
import json
import os

from ..sn0w import Logger

def check_lora_folders():
    logger = Logger()
    custom_paths = ["loras_15", "loras_xl", "loras_3"]
    existing_paths = []

    dir_path = os.path.dirname(os.path.realpath(__file__))
    if os.path.basename(dir_path) == "src":
        dir_path = os.path.dirname(dir_path)
    json_path = os.path.join(dir_path, 'web/settings/sn0w_settings.json')
    # Ensure the directory exists
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    
    for path in custom_paths:
        try:
            lora_path = folder_paths.get_filename_list(path)
            if lora_path:
                existing_paths.append(path)
        except Exception as e:
            logger.log(f"{path} doesn't exist: {e}", "WARNING")
    
    print(existing_paths)
    # Write the result to a JSON file in /web/settings
    data = {"loaders_enabled": existing_paths}
    with open(json_path, "w") as json_file:
        json.dump(data, json_file, indent=4)

    return existing_paths