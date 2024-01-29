class FindResolutionNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "width": ("INT", {"default": 0, "min": 0}),
                "height": ("INT", {"default": 0, "min": 0}),
                "flip": ("BOOLEAN", {"default": False},),
            },
        }

    RETURN_TYPES = ("INT", "INT",)
    RETURN_NAMES = ("WIDTH", "HEIGHT")
    FUNCTION = "find_closest_resolution"
    CATEGORY = "sn0w"

    def find_closest_resolution(self, width, height, flip):
        resolutions = [
            512, 576, 640, 704, 768, 832, 896, 960, 1024, 1088, 1152, 1216, 1280, 1344, 1408, 1472, 1536, 1600, 1664, 1728, 1792, 1856, 1920, 1984, 2048
        ]
        if flip:
            width, height = height, width

        closest_width = self._find_closest_value(width, resolutions)
        closest_height = self._find_closest_value(height, resolutions)
        
        return closest_width, closest_height

    @staticmethod
    def _find_closest_value(input_value, resolutions):
        closest = resolutions[0]
        smallest_difference = abs(input_value - closest)

        for resolution in resolutions:
            difference = abs(input_value - resolution)
            if difference < smallest_difference:
                closest = resolution
                smallest_difference = difference

        return closest
    