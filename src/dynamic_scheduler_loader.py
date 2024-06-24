from .custom_schedulers.custom_schedulers import CustomSchedulers

def generate_scheduler_node_class(settings, get_sigmas_function):
    class DynamicSchedulerNode:

        @classmethod
        def create_setting_entry(cls, setting_type, setting_value):
            if setting_type == "INT":
                return ("INT", {"default": setting_value[1], "min": setting_value[2], "max": setting_value[3]})
            elif setting_type == "FLOAT":
                return ("FLOAT", {"default": setting_value[1], "min": setting_value[2], "max": setting_value[3], "step": setting_value[4]})
            elif setting_type == "STRING":
                return ("STRING", {"default": setting_value[1]})
            elif setting_type == "BOOLEAN":
                return ("BOOLEAN", {"default": setting_value[1]})
            else:
                raise ValueError(f"Unsupported setting type: {setting_type}")

        @classmethod
        def INPUT_TYPES(cls):
            inputs = {
                "required": {
                    "steps": ("INT", {"default": 20, "min": 1, "max": 10000}),
                    **{
                        key: cls.create_setting_entry(value[0], value)
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