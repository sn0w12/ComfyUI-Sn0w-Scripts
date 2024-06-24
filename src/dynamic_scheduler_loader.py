from .custom_schedulers.custom_schedulers import CustomSchedulers

def generate_scheduler_node_class(settings, get_sigmas_function):
    class DynamicSchedulerNode:
        @classmethod
        def INPUT_TYPES(cls):
            inputs = {
                "required": {
                    "steps": ("INT", {"default": 20, "min": 1, "max": 10000}),
                    **{
                        key: ("FLOAT", {"default": value[1], "min": value[2], "max": value[3], "step": value[4]})
                        for key, value in settings['settings'].items()
                    }
                }
            }
            return inputs

        RETURN_TYPES = ("SIGMAS",)
        RETURN_NAMES = ("SIGMAS",)
        FUNCTION = "get_sigmas"
        CATEGORY = "sn0w/schedulers"
        OUTPUT_NODE = True

        def get_sigmas(self, steps, **kwargs):
            return (CustomSchedulers.append_zero(
                get_sigmas_function(steps, **kwargs)
            ), )

    return DynamicSchedulerNode