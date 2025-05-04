from .upscale_with_model_by import UpscaleImageBy
import torch
import math
import comfy.utils
import asyncio
import numpy as np
from PIL import Image
import comfy.samplers
from nodes import KSampler, VAEEncode, VAEDecode, CLIPTextEncode
from .wd14.tagger import tag as wd14_tag, wait_for_async
from ..sn0w import Logger


class AutoTaggedTiledUpscaler:
    logger = Logger()

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "upscale_by": ("FLOAT", {"default": 2.0, "min": 0.0, "max": 100.0, "step": 0.1, "round": 0.01}),
                "upscale_model": ("UPSCALE_MODEL",),
                "split_parts": ("INT", {"default": 4, "min": 1, "max": 128, "step": 1}),
                "overlap_pixels": ("INT", {"default": 64, "min": 0, "max": 512, "step": 8}),
                # Standard KSampler parameters - required when split_parts > 1
                "model": ("MODEL",),
                "vae": ("VAE",),
                "clip": ("CLIP",),
                "positive": ("STRING", {"default": ""}),
                "negative": ("CONDITIONING",),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xFFFFFFFFFFFFFFFF}),
                "steps": ("INT", {"default": 10, "min": 1, "max": 10000}),
                "cfg": ("FLOAT", {"default": 8.0, "min": 0.0, "max": 100.0, "step": 0.1, "round": 0.01}),
                "sampler_name": (comfy.samplers.KSampler.SAMPLERS,),
                "scheduler": (comfy.samplers.KSampler.SCHEDULERS,),
                "denoise": ("FLOAT", {"default": 0.4, "min": 0.0, "max": 1.0, "step": 0.01, "round": 0.01}),
                # WD14 tagger parameters for auto-tagging
                "tagger_model": (
                    [
                        "wd-v1-4-moat-tagger-v2",
                        "wd-v1-4-convnextv2-tagger-v2",
                        "wd-v1-4-convnext-tagger-v2",
                        "wd-v1-4-vit-tagger-v2",
                    ],
                    {"default": "wd-v1-4-moat-tagger-v2"},
                ),
                "tag_threshold": ("FLOAT", {"default": 0.35, "min": 0.0, "max": 1.0, "step": 0.05}),
                "character_threshold": ("FLOAT", {"default": 0.85, "min": 0.0, "max": 1.0, "step": 0.05}),
                "exclude_tags": ("STRING", {"default": ""}),
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("IMAGE",)
    FUNCTION = "upscale"

    CATEGORY = "image/upscaling"

    # Minimum dimensions for split parts in latent space
    # Each latent pixel corresponds to 8x8 pixels in pixel space
    MIN_LATENT_SIZE = 16

    def upscale(
        self,
        image,
        upscale_by,
        upscale_model,
        split_parts=1,
        overlap_pixels=128,
        model=None,
        vae=None,
        clip=None,
        positive="",
        negative=None,
        seed=0,
        steps=10,
        cfg=8.0,
        sampler_name=None,
        scheduler=None,
        denoise=0.4,
        tagger_model="wd-v1-4-moat-tagger-v2",
        tag_threshold=0.35,
        character_threshold=0.85,
        exclude_tags="",
        prompt=None,
        extra_pnginfo=None,
    ):
        upscaler = UpscaleImageBy()
        upscaled_image = upscaler.upscale(image, upscale_by, upscale_model)[0]

        batch_size, height, width, channels = upscaled_image.shape

        # If no splitting is requested, return upscaled image as is
        if split_parts <= 1:
            return (upscaled_image,)

        # Check the image dimensions to determine max number of splits
        batch_size, height, width, channels = upscaled_image.shape  # Images in ComfyUI are [B,H,W,C]

        # The latent space is usually 8x smaller in each dimension
        # Calculate max parts based on minimum latent size requirements
        latent_height = height // 8  # VAE downsampling factor
        latent_width = width // 8

        max_rows = max(1, latent_height // self.MIN_LATENT_SIZE)
        max_cols = max(1, latent_width // self.MIN_LATENT_SIZE)
        max_parts = max_rows * max_cols

        # Adjust split_parts if needed to avoid parts that are too small
        if split_parts > max_parts:
            # Log warning and adjust split_parts
            self.logger.log(
                f"Reduced split_parts from {split_parts} to {max_parts} to maintain minimum latent size", "WARNING"
            )
            split_parts = max_parts

        # Ensure split_parts is at least 1
        split_parts = max(1, split_parts)

        grid_size = math.ceil(math.sqrt(split_parts))
        rows = grid_size
        cols = math.ceil(split_parts / rows)
        self.logger.log(f"Grid: {rows}x{cols}, {split_parts} parts, overlap: {overlap_pixels}px", "DEBUG")

        # Split the upscaled image with overlap
        split_info = self.split_image(upscaled_image, split_parts, overlap_pixels)

        # Process each split with standard KSampler
        processed_splits = []
        k_sampler = KSampler()
        vae_encode = VAEEncode()
        vae_decode = VAEDecode()
        text_encode = CLIPTextEncode()

        for i, part_data in enumerate(split_info):
            split_image = part_data["image"]  # Extract the actual image tensor
            b, h, w, c = split_image.shape

            self.logger.log(f"Part {i + 1}/{len(split_info)}: {w}x{h}", "DEBUG")

            # First, we need to tag the split image using WD14Tagger
            # Convert the tensor to a PIL Image for tagging
            img_for_tagging = self.tensor_to_pil(split_image)

            # Tag the image using the WD14Tagger
            auto_tags = wait_for_async(
                lambda: wd14_tag(
                    img_for_tagging,
                    tagger_model,
                    threshold=tag_threshold,
                    character_threshold=character_threshold,
                    exclude_tags=exclude_tags,
                    replace_underscore=True,
                )
            )

            # Combine auto tags with user provided prompt if any
            combined_prompt = auto_tags
            if positive and isinstance(positive, str) and positive.strip():
                combined_prompt = f"{auto_tags}, {positive.strip()}"

            # Encode the combined prompt with CLIP
            positive_conditioning = text_encode.encode(clip, combined_prompt)[0]
            latent = vae_encode.encode(vae, split_image)[0]

            # Process the latent with KSampler using the auto-tagged positive conditioning
            processed_latent = k_sampler.sample(
                model=model,
                seed=seed,
                steps=steps,
                cfg=cfg,
                sampler_name=sampler_name,
                scheduler=scheduler,
                positive=positive_conditioning,
                negative=negative,
                latent_image=latent,
                denoise=denoise,
            )[0]

            # Decode back to image
            processed_image = vae_decode.decode(vae, processed_latent)[0]
            processed_splits.append(processed_image)

        # Stitch the processed images back together with fade effect
        result = self.stitch_images(processed_splits, batch_size, channels, height, width, split_parts, overlap_pixels)
        return (result,)

    def tensor_to_pil(self, tensor):
        """Convert a ComfyUI tensor to a PIL Image for tagging"""
        # ComfyUI tensors are in the range [0, 1], so scale to [0, 255]
        img_array = (tensor[0].cpu().numpy() * 255).astype(np.uint8)
        return Image.fromarray(img_array)

    def split_image(self, image, num_parts, overlap_pixels):
        batch_size, height, width, channels = image.shape  # Use proper BHWC format
        result_images = []

        # Calculate grid dimensions (trying to make it as square as possible)
        grid_size = math.ceil(math.sqrt(num_parts))
        rows = grid_size
        cols = math.ceil(num_parts / rows)

        # Calculate part dimensions
        part_height = height // rows
        part_width = width // cols
        self.logger.log(f"Original Upscaled: {width}x{height}, part size: {part_width}x{part_height}", "INFORMATIONAL")

        # Extract parts with proper handling of edges and corners
        parts_created = 0
        for r in range(rows):
            if parts_created >= num_parts:
                break

            for c in range(cols):
                if parts_created >= num_parts:
                    break

                # Base coordinates for this part
                base_y_start = r * part_height
                base_y_end = min((r + 1) * part_height, height)
                base_x_start = c * part_width
                base_x_end = min((c + 1) * part_width, width)

                # Add overlap only where appropriate (don't go beyond borders)
                # Top edge - only add overlap if not first row
                y_start = base_y_start
                if r > 0:
                    y_start = max(0, base_y_start - overlap_pixels)

                # Bottom edge - only add overlap if not last row
                y_end = base_y_end
                if r < rows - 1:
                    y_end = min(height, base_y_end + overlap_pixels)

                # Left edge - only add overlap if not first column
                x_start = base_x_start
                if c > 0:
                    x_start = max(0, base_x_start - overlap_pixels)

                # Right edge - only add overlap if not last column
                x_end = base_x_end
                if c < cols - 1:
                    x_end = min(width, base_x_end + overlap_pixels)

                # Extract part - making sure to keep all channels
                # ComfyUI uses BHWC format [batch, height, width, channels]
                part = image[:, y_start:y_end, x_start:x_end, :]

                actual_width = x_end - x_start
                actual_height = y_end - y_start
                self.logger.log(f"Part {parts_created + 1}: [{c},{r}], {actual_width}x{actual_height}", "DEBUG")

                # Store the part along with its position info for stitching
                result_images.append(
                    {
                        "image": part,
                        "base_coords": (base_y_start, base_y_end, base_x_start, base_x_end),
                        "full_coords": (y_start, y_end, x_start, x_end),
                    }
                )

                parts_created += 1
                if parts_created >= num_parts:
                    break

        return result_images

    def stitch_images(self, processed_images, batch_size, channels, orig_height, orig_width, num_parts, overlap_pixels):
        # Create empty result tensor and weight mask for blending
        result = torch.zeros(
            (batch_size, orig_height, orig_width, channels),
            dtype=processed_images[0].dtype,
            device=processed_images[0].device,
        )

        # Weight mask to track contribution of each pixel (for proper blending)
        weights = torch.zeros(
            (batch_size, orig_height, orig_width, 1), dtype=torch.float32, device=processed_images[0].device
        )

        # Calculate grid dimensions
        grid_size = math.ceil(math.sqrt(num_parts))
        rows = grid_size
        cols = math.ceil(num_parts / rows)

        # Calculate base part dimensions (non-overlapping)
        part_height = orig_height // rows
        part_width = orig_width // cols

        # Need to reconstruct the split part coordinates
        parts_info = []
        part_idx = 0

        for r in range(rows):
            if part_idx >= num_parts:
                break

            for c in range(cols):
                if part_idx >= num_parts:
                    break

                # Base coordinates (non-overlapping part)
                base_y_start = r * part_height
                base_y_end = min((r + 1) * part_height, orig_height)
                base_x_start = c * part_width
                base_x_end = min((c + 1) * part_width, orig_width)

                # Full coordinates (with overlap)
                # Top edge - only add overlap if not first row
                y_start = base_y_start
                if r > 0:
                    y_start = max(0, base_y_start - overlap_pixels)

                # Bottom edge - only add overlap if not last row
                y_end = base_y_end
                if r < rows - 1:
                    y_end = min(orig_height, base_y_end + overlap_pixels)

                # Left edge - only add overlap if not first column
                x_start = base_x_start
                if c > 0:
                    x_start = max(0, base_x_start - overlap_pixels)

                # Right edge - only add overlap if not last column
                x_end = base_x_end
                if c < cols - 1:
                    x_end = min(orig_width, base_x_end + overlap_pixels)

                # Store position information for this part
                parts_info.append(
                    {
                        "index": part_idx,
                        "base": (base_y_start, base_y_end, base_x_start, base_x_end),
                        "full": (y_start, y_end, x_start, x_end),
                    }
                )

                part_idx += 1

        # Helper function for smoother blending using cosine^2 fade
        def smooth_fade(x):
            """
            Creates an even smoother transition using cosine^2
            x should be between 0 and 1
            Returns a value between 0 and 1
            """
            cosine_val = 0.5 * (1 - math.cos(math.pi * x))
            # Square it for an even smoother transition
            return cosine_val * cosine_val

        # Now place each part with proper weight masks for blending
        for part_info in parts_info:
            idx = part_info["index"]
            if idx >= len(processed_images):
                continue

            processed_img = processed_images[idx]

            # Get the coordinates
            y_start, y_end, x_start, x_end = part_info["full"]
            base_y_start, base_y_end, base_x_start, base_x_end = part_info["base"]

            # Create weight mask for fading
            h_size = y_end - y_start
            w_size = x_end - x_start

            # Handle possible size mismatches between processed image and the expected section area
            effective_h = min(h_size, processed_img.shape[1])
            effective_w = min(w_size, processed_img.shape[2])

            # Create weight mask starting with all 1s (full weight)
            weight_mask = torch.ones((effective_h, effective_w, 1), device=processed_img.device)

            # Create coordinate grids for more precise blending
            y_coords = (
                torch.arange(effective_h, device=processed_img.device).reshape(-1, 1, 1).repeat(1, effective_w, 1)
            )
            x_coords = (
                torch.arange(effective_w, device=processed_img.device).reshape(1, -1, 1).repeat(effective_h, 1, 1)
            )

            # Apply blending on all sides where there's overlap
            # Left edge fade
            if x_start < base_x_start:
                fade_width = base_x_start - x_start
                left_mask = x_coords.float() / fade_width
                left_mask = torch.clamp(left_mask, 0.0, 1.0)
                # Apply smooth fade function to each position
                for x in range(min(fade_width, effective_w)):
                    mask_val = smooth_fade(left_mask[0, x, 0].item())
                    weight_mask[:, x : x + 1, :] *= mask_val

            # Right edge fade
            if x_end > base_x_end:
                fade_width = x_end - base_x_end
                right_edge = effective_w - 1
                right_offset = base_x_end - x_start
                if right_offset < 0:
                    right_offset = 0

                for x in range(min(fade_width, effective_w)):
                    if right_offset + x < effective_w:
                        pos = right_offset + x
                        # Create reverse fade (1 to 0)
                        mask_val = smooth_fade(1.0 - (x / fade_width))
                        weight_mask[:, pos : pos + 1, :] *= mask_val

            # Top edge fade
            if y_start < base_y_start:
                fade_height = base_y_start - y_start
                top_mask = y_coords.float() / fade_height
                top_mask = torch.clamp(top_mask, 0.0, 1.0)
                # Apply smooth fade function to each position
                for y in range(min(fade_height, effective_h)):
                    mask_val = smooth_fade(top_mask[y, 0, 0].item())
                    weight_mask[y : y + 1, :, :] *= mask_val

            # Bottom edge fade
            if y_end > base_y_end:
                fade_height = y_end - base_y_end
                bottom_offset = base_y_end - y_start
                if bottom_offset < 0:
                    bottom_offset = 0

                for y in range(min(fade_height, effective_h)):
                    if bottom_offset + y < effective_h:
                        pos = bottom_offset + y
                        # Create reverse fade (1 to 0)
                        mask_val = smooth_fade(1.0 - (y / fade_height))
                        weight_mask[pos : pos + 1, :, :] *= mask_val

            # Apply special handling for corners where two fades would multiply
            # This prevents too much darkening in corners
            if x_start < base_x_start and y_start < base_y_start:
                # Top-left corner: use max of individual fades rather than multiplication
                corner_width = base_x_start - x_start
                corner_height = base_y_start - y_start
                for y in range(min(corner_height, effective_h)):
                    for x in range(min(corner_width, effective_w)):
                        # Get fade values for both directions
                        y_fade = smooth_fade(y / corner_height)
                        x_fade = smooth_fade(x / corner_width)
                        # Use the stronger fade value (max) rather than multiplying them
                        corner_fade = max(y_fade, x_fade)
                        weight_mask[y, x, :] = corner_fade

            # Extract the actual image slice to use
            img_slice = processed_img[0, :effective_h, :effective_w, :]

            # Expand the weight mask to match the number of channels
            expanded_weight = weight_mask.expand(-1, -1, channels)

            # Apply weighted contribution to result
            result[0, y_start : y_start + effective_h, x_start : x_start + effective_w, :] += (
                img_slice * expanded_weight
            )
            weights[0, y_start : y_start + effective_h, x_start : x_start + effective_w, :] += weight_mask

        # Normalize by weights to get the final result (avoid division by zero)
        epsilon = 1e-10
        weights = weights.expand(-1, -1, -1, channels)  # Expand weights to match channels
        normalized_result = result / (weights + epsilon)

        return normalized_result
