from comfy_extras.nodes_custom_sampler import SplitSigmasDenoise, SplitSigmas

class CombineSchedulersNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
                "required": {
                    "sigmas_a": ("SIGMAS",),
                    "sigmas_b": ("SIGMAS",),
                    "split_at": ("INT", {"default": 10, "min": 10, "max": 10000}),
                    "denoise": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step":0.01, "round": 0.01}),
                },
            }
    
    RETURN_TYPES = ("SIGMAS", )
    RETURN_NAMES = ("SIGMAS", )

    FUNCTION = "get_combined_sigmas"

    CATEGORY = "sampling/custom_sampling"

    def get_combined_sigmas(self, sigmas_a, sigmas_b, split_at, denoise):
        split_sigmas_a = SplitSigmas.get_sigmas(self, sigmas_a, split_at)
        split_sigmas_b = SplitSigmas.get_sigmas(self, sigmas_b, split_at)

        sigmas = split_sigmas_a[0] + split_sigmas_b[1]
        sigmas = self.get_denoised_sigmas(sigmas, denoise)

        return (sigmas,)
    
    def get_denoised_sigmas(self, sigmas, denoise):
        if denoise == 1:
            return (None, sigmas, )
        
        return SplitSigmasDenoise.get_sigmas(self, sigmas, denoise)