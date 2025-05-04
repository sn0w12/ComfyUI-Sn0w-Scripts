import os
import json
import comfy.samplers
import numpy as np
from PIL import Image
from nodes import VAEDecode
from ..sn0w import Logger
from .character_select import CharacterSelectNode
from .simple_ksampler import SimpleSamplerCustom

# File paths
IMAGES_FILE_PATH = "web/images/images.json"


class GenerateCharactersNode:
    logger = Logger()
    character_select = CharacterSelectNode()
    base_dir = character_select.get_base_dir()
    json_path = os.path.join(base_dir, "..", "ComfyUI-Syntax-Highlight", IMAGES_FILE_PATH)
    characters_dir = os.path.join(os.path.dirname(json_path), "characters")

    @classmethod
    def initialize(cls):
        cls.character_select.check_initialize()
        os.makedirs(cls.characters_dir, exist_ok=True)
        return cls.character_select.final_character_dict

    @classmethod
    def get_all_characters(cls):
        return cls.initialize()

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": ("MODEL",),
                "clip": ("CLIP",),
                "vae": ("VAE",),
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
        character_dict = self.get_all_characters()
        existing_filenames = self.load_existing_images()

        orig_positive = kwargs.get("positive", "")

        images = []
        for character_name in character_dict:
            cleaned_name = character_name.split("(")[0].strip().lower()
            cleaned_name = cleaned_name.replace(" ", "_")

            # Skip if image already exists
            if cleaned_name in existing_filenames:
                self.logger.log(f"Skipping {cleaned_name} - image already exists", "INFO")
                continue

            self.logger.log(f"Generating image for character: {character_name}", "INFO")

            # Get character details and update positive prompt
            char_item = character_dict[character_name]
            char_string = f"({char_item['associated_string']}:1.1), "
            char_prompt = char_item["prompt"]

            positive = f"{char_string}{char_prompt}, {orig_positive}".strip(", ")
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
                            "path": f"extensions\\ComfyUI-Sn0w-Scripts\\images\\characters\\{cleaned_name}.png",
                        }
                    )
                    data["count"] = len(data["images"])
                    f.seek(0)
                    json.dump(data, f, indent=2)
                    f.truncate()

        return (images,)
