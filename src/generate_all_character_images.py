import os
import json
import re
import comfy.samplers
import comfy.utils
import numpy as np
from PIL import Image
from nodes import VAEDecode
from ..sn0w import CharacterLoader, Logger
from .simple_ksampler import SimpleSamplerCustom

# File paths
IMAGES_FILE_PATH = "web/images/images.json"
CHARACTER_FILE_PATH = "web/settings/characters.csv"
CUSTOM_CHARACTER_FILE_PATH = "web/settings/custom_characters.json"


class GenerateCharactersNode:
    logger = Logger()
    character_dict = {}
    series_list = []

    @classmethod
    def get_base_dir(cls):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        if os.path.basename(dir_path) == "src":
            dir_path = os.path.dirname(dir_path)
        return dir_path

    @classmethod
    def load_characters(cls):
        base_dir = cls.get_base_dir()
        cls.character_dict = CharacterLoader.get_filtered_character_dict(base_dir, include_default=True)

        # Build series list with counts from filtered characters
        series_counter = {}
        for character in cls.character_dict.values():
            series = CharacterLoader.get_character_series(character)
            if series:
                series_counter[series] = series_counter.get(series, 0) + 1

        series_list_with_counts = []
        for series in sorted(series_counter.keys()):
            count = series_counter[series]
            if series:
                series_list_with_counts.append(f"{series} ({count})")

        cls.series_list = ["All"] + series_list_with_counts
        return cls.character_dict

    @classmethod
    def initialize(cls):
        base_dir = cls.get_base_dir()
        cls.json_path = os.path.join(base_dir, "..", "ComfyUI-Syntax-Highlight", IMAGES_FILE_PATH)
        cls.characters_dir = os.path.join(os.path.dirname(cls.json_path), "characters")
        os.makedirs(cls.characters_dir, exist_ok=True)
        return cls.load_characters()

    @classmethod
    def INPUT_TYPES(cls):
        cls.initialize()
        return {
            "required": {
                "model": ("MODEL",),
                "clip": ("CLIP",),
                "vae": ("VAE",),
                "series_filter": (cls.series_list, {"default": "All"}),
                "include_clothing": ("BOOLEAN", {"default": True}),
                "add_noise": ("BOOLEAN", {"default": True}),
                "noise_seed": ("INT", {"default": 0, "min": 0, "max": 0xFFFFFFFFFFFFFFFF}),
                "steps": ("INT", {"default": 20, "min": 1, "max": 10000}),
                "cfg": ("FLOAT", {"default": 8.0, "min": 0.0, "max": 100.0, "step": 0.1, "round": 0.01}),
                "sampler_name": (comfy.samplers.KSampler.SAMPLERS,),
                "scheduler_name": (comfy.samplers.KSampler.SCHEDULERS,),
                "denoise": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01, "round": 0.01}),
                "width": ("INT", {"default": 0, "min": 0, "step": 64}),
                "height": ("INT", {"default": 0, "min": 0, "step": 64}),
            },
            "optional": {
                "positive": ("STRING", {"default": ""}),
                "negative": ("STRING", {"default": ""}),
            },
            "hidden": {
                "extra_info": "EXTRA_PNGINFO",
                "id": "UNIQUE_ID",
            },
        }

    @classmethod
    def VALIDATE_INPUTS(cls, input_types):
        return True

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("IMAGES",)
    FUNCTION = "generate"
    CATEGORY = "sn0w"

    @classmethod
    def load_existing_images(cls):
        try:
            with open(cls.json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [img["filename"] for img in data.get("images", [])]
        except Exception as e:
            cls.logger.log(f"Error loading images.json: {str(e)}", "WARNING")
            return []

    def generate(
        self,
        model,
        clip,
        vae,
        series_filter,
        include_clothing,
        add_noise,
        noise_seed,
        steps,
        cfg,
        sampler_name,
        scheduler_name,
        denoise,
        width,
        height,
        **kwargs,
    ):
        simple_sampler = SimpleSamplerCustom()
        vae_decode = VAEDecode()
        character_dict = self.character_dict
        existing_filenames = self.load_existing_images()

        orig_positive = kwargs.get("positive", "")

        # Filter characters by series if not "All"
        if series_filter != "All":
            match = re.match(r"^(.*?)\s*\(\d+\)$", series_filter)
            if match:
                selected_series = match.group(1).strip()
            else:
                selected_series = series_filter
            character_dict = {
                name: char for name, char in character_dict.items() if char.get("series", "") == selected_series
            }

        characters_to_process = {}
        for character_name, char_item in character_dict.items():
            cleaned_name = character_name.split("(")[0].strip().lower()
            cleaned_name = cleaned_name.replace(" ", "_")

            if cleaned_name not in existing_filenames:
                characters_to_process[character_name] = char_item
            else:
                self.logger.log(f"Skipping {cleaned_name} - image already exists", "INFO")

        total_characters = len(characters_to_process)
        if total_characters == 0:
            self.logger.log("No new characters to process", "INFO")
            return ([],)

        pbar = comfy.utils.ProgressBar(total_characters)
        self.logger.log(f"Processing {total_characters} characters", "INFO")

        images = []
        for character_name, char_item in characters_to_process.items():
            cleaned_name = character_name.split("(")[0].strip().lower()
            cleaned_name = cleaned_name.replace(" ", "_")

            # Skip if image already exists
            if cleaned_name in existing_filenames:
                self.logger.log(f"Skipping {cleaned_name} - image already exists", "INFO")
                continue

            self.logger.log(f"Generating image for character: {character_name}", "INFO")

            # Build prompt components
            char_string = f"({char_item['associated_string']}:1.1), "
            char_prompt = char_item["prompt"]
            clothing_prompt = char_item.get("clothing_tags", "") if include_clothing else ""

            # Combine prompts
            prompt_parts = [part for part in [char_string, char_prompt, clothing_prompt, orig_positive] if part.strip()]
            positive = ", ".join(prompt_parts).strip(", ")
            kwargs["positive"] = positive

            (image, samples, positive_prompt, negative_prompt) = simple_sampler.sample(
                model,
                clip,
                vae,
                add_noise,
                noise_seed,
                steps,
                cfg,
                sampler_name,
                scheduler_name,
                denoise,
                width,
                height,
                **kwargs,
            )

            if samples is not None:
                # Decode the tensor into an image using VAE
                decoded_image = vae_decode.decode(vae, samples)[0]
                images.append(decoded_image[0])

                image_path = os.path.join(self.characters_dir, f"{cleaned_name}.png")

                # Convert to PIL image and save
                i = 255.0 * decoded_image[0].cpu().numpy()
                img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
                img.save(image_path)

                # Add to images.json
                with open(self.json_path, "r+", encoding="utf-8") as f:
                    data = json.load(f)
                    data["images"].append(
                        {
                            "filename": cleaned_name,
                            "path": f"extensions\\ComfyUI-Syntax-Highlight\\images\\characters\\{cleaned_name}.png",
                        }
                    )
                    data["count"] = len(data["images"])
                    f.seek(0)
                    json.dump(data, f, indent=2)
                    f.truncate()
            pbar.update(1)

        return (images,)
