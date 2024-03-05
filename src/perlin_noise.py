import os
import numpy as np
import torch
from PIL import Image

class FilmGrain:
    def __init__(self):
        self.noise_cache = {}
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.noise_img_dir = os.path.join(script_dir, 'img', 'noise')

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
                "intensity": ("FLOAT", {
                    "default": 0.2,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.01
                }),
                "scale": ("FLOAT", {
                    "default": 10,
                    "min": 1,
                    "max": 100,
                    "step": 1
                }),
                "cache": ("BOOLEAN", {"default": False},),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "film_grain"

    CATEGORY = "sn0w"

    def film_grain(self, image: torch.Tensor, intensity: float, scale: float, cache: bool):
        batch_size, height, width, channels = image.shape
        assert channels == 3, "Image must have 3 channels for RGB"

        result = torch.zeros_like(image)

        for b in range(batch_size):
            tensor_image = image[b].numpy()

            grain_image = np.zeros_like(tensor_image)
            for channel in range(3):
                noise = self.get_noise_image(height, width, scale, channel) if cache else self.generate_perlin_noise((height, width), scale)
                noise = (noise - noise.min()) / (noise.max() - noise.min())  # Normalize
                noise = (noise * 2 - 1) * intensity  # Apply intensity
                grain_image[:, :, channel] = np.clip(tensor_image[:, :, channel] + noise, 0, 1)

            tensor = torch.from_numpy(grain_image).unsqueeze(0)
            result[b] = tensor

        return (result,)

    def generate_perlin_noise(self, shape, scale, octaves=4, persistence=0.5, lacunarity=2):
        def smoothstep(t):
            return t * t * (3.0 - 2.0 * t)

        def lerp(t, a, b):
            return a + t * (b - a)

        def gradient(h, x, y):
            vectors = np.array([[1, 1], [-1, 1], [1, -1], [-1, -1]])
            g = vectors[h % 4]
            return g[:, :, 0] * x + g[:, :, 1] * y

        height, width = shape
        noise = np.zeros(shape)

        for octave in range(octaves):
            octave_scale = scale * lacunarity ** octave
            x = np.linspace(0, 1, width, endpoint=False)
            y = np.linspace(0, 1, height, endpoint=False)
            X, Y = np.meshgrid(x, y)
            X, Y = X * octave_scale, Y * octave_scale

            xi = X.astype(int)
            yi = Y.astype(int)

            xf = X - xi
            yf = Y - yi

            u = smoothstep(xf)
            v = smoothstep(yf)

            n00 = gradient(np.random.randint(0, 4, (height, width)), xf, yf)
            n01 = gradient(np.random.randint(0, 4, (height, width)), xf, yf - 1)
            n10 = gradient(np.random.randint(0, 4, (height, width)), xf - 1, yf)
            n11 = gradient(np.random.randint(0, 4, (height, width)), xf - 1, yf - 1)

            x1 = lerp(u, n00, n10)
            x2 = lerp(u, n01, n11)
            y1 = lerp(v, x1, x2)

            noise += y1 * persistence ** octave

        return noise / (1 - persistence ** octaves)

    def get_noise_image(self, height, width, scale, channel):
        key = (height, width)
        if key in self.noise_cache and self.noise_cache[key][channel] is not None:
            return self.noise_cache[key][channel]
        else:
            noise = self.generate_perlin_noise((height, width), scale)
            if key not in self.noise_cache:
                self.noise_cache[key] = [None, None, None]
            self.noise_cache[key][channel] = noise
            return noise