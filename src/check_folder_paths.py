import json
import os
import folder_paths

from ..sn0w import Logger


def check_lora_folders():
    logger = Logger()
    custom_paths = ["loras_15", "loras_xl", "loras_3"]
    custom_path_map = {
        "loras_15": "SD1.5",
        "loras_xl": "SDXL",
        "loras_3": "SD3"
    }
    existing_paths = []

    dir_path = os.path.dirname(os.path.realpath(__file__))
    if os.path.basename(dir_path) == "src":
        dir_path = os.path.dirname(dir_path)
    json_path = os.path.join(dir_path, "web/settings/sn0w_settings.json")
    # Ensure the directory exists
    os.makedirs(os.path.dirname(json_path), exist_ok=True)

    for path in custom_paths:
        try:
            lora_path = folder_paths.get_filename_list(path)
            if lora_path:
                existing_paths.append(path)
        except Exception as e:
            exception_path = str(e)[1:-1]
            if exception_path not in custom_path_map:
                logger.log(f"Extra model path doesn't exist: {e}, add it to extra_model_paths.yaml if you want {e} custom lora loaders to work.", "WARNING")
            else:
                logger.log(f"Extra model path doesn't exist: {e}, add it to extra_model_paths.yaml if you want {custom_path_map[exception_path]} custom lora loaders to work.", "WARNING")

    # Write the result to a JSON file in /web/settings
    data = {"loaders_enabled": existing_paths}
    with open(json_path, "w", encoding="utf-8") as json_file:
        json.dump(data, json_file, indent=4)

    return existing_paths
