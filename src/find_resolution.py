class FindResolutionNode:
    resolutions = {
            "1024 x 1024 1:1": [
                1024,
                1024
            ],
            "1152 x 896 9:7": [
                1152,
                896
            ],
            "1216 x 832 19:13": [
                1216,
                832
            ],
            "1344 x 768 7:4": [
                1344,
                768
            ],
            "1536 x 640 12:5": [
                1536,
                640
            ]
        }

    @classmethod
    def INPUT_TYPES(cls):
        resolution_names = sorted(cls.resolutions.keys())
        return {
            "required": {
                "resolution": (resolution_names, ),
                "flip": ("BOOLEAN", {"default": False},),
            },
        }

    RETURN_TYPES = ("INT", "INT",)
    RETURN_NAMES = ("WIDTH", "HEIGHT")
    FUNCTION = "get_resolution"
    CATEGORY = "sn0w"

    def get_resolution(self, resolution, flip):
        resolutions = self.resolutions
        return (resolutions[resolution][1], resolutions[resolution][0]) if flip else (resolutions[resolution][0], resolutions[resolution][1])
    