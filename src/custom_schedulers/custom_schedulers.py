import json
import os
import glob
import importlib.util
import torch

class CustomSchedulers:
    def __init__(self):
        self.schedulers = self.load_schedulers()
        self.scheduler_settings = self.load_scheduler_settings()
        self.scheduler_defaults = self.get_default_scheduler_settings()
        self.export_scheduler_settings_to_js()

    @staticmethod
    def append_zero(x):
        return torch.cat([x, x.new_zeros([1])])

    def load_schedulers(self):
        schedulers = {}
        scheduler_files = glob.glob(os.path.dirname(__file__) + "/*.py")
        for file_path in scheduler_files:
            module_name = os.path.basename(file_path)[:-3]
            if module_name != "__init__" and module_name != "custom_schedulers":
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                schedulers[module_name] = module
        return schedulers

    def load_scheduler_settings(self):
        settings = {}
        for module in self.schedulers.values():
            if hasattr(module, 'settings'):
                scheduler_name = module.settings['name']
                # Extract only the setting names
                settings[scheduler_name] = list(module.settings['settings'].keys())
        return settings

    def get_default_scheduler_settings(self):
        defaults = {}
        for module in self.schedulers.values():
            if hasattr(module, 'settings'):
                scheduler_name = module.settings['name']
                setting_defaults = {}
                for setting, details in module.settings['settings'].items():
                    setting_defaults[setting] = details
                defaults[scheduler_name] = setting_defaults
        return defaults

    def get_scheduler_settings(self):
        return self.scheduler_settings

    def get_scheduler_defaults(self):
        return self.scheduler_defaults

    def get_sigmas(self, name, *args, **kwargs):
        # Look for a module that has the same 'name' in its settings
        for module in self.schedulers.values():
            if hasattr(module, 'settings') and module.settings['name'] == name:
                if hasattr(module, 'get_sigmas'):
                    sigmas = self.append_zero(module.get_sigmas(*args, **kwargs))
                    return (sigmas, )
        raise ValueError(f"No scheduler found with the name {name}")
    
    def export_scheduler_settings_to_js(self):
        # Go settings directory
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        target_dir = os.path.join(base_path, 'web', 'settings')
        os.makedirs(target_dir, exist_ok=True)
        filepath = os.path.join(target_dir, 'scheduler_settings.js')
        
        # Initialize the JavaScript content with default settings
        js_content = "const widgets = {\n"
        js_content += """    "polyexponential": {
        "sigma_max_poly": ["FLOAT", 14.614642, 0.0, 5000.0, 0.01, false],
        "sigma_min_poly": ["FLOAT", 0.0291675, 0.0, 5000.0, 0.01, false],
        "rho": ["FLOAT", 1.0, 0.0, 100.0, 0.01, false]
    },
    "vp": {
        "beta_d": ["FLOAT", 14.0, 0.0, 5000.0, 0.01, false],
        "beta_min": ["FLOAT", 0.05, 0.0, 5000.0, 0.01, false],
        "eps_s": ["FLOAT", 0.075, 0.0, 1.0, 0.0001, false]
    },"""
        
        # Convert the Python dictionary to a JavaScript object
        for name, settings in self.scheduler_defaults.items():
            if name in ["polyexponential", "vp"]:  # Merge with defaults
                js_content += f"    \"{name}\": {{\n"
                for setting, details in settings.items():
                    js_content += f"        \"{setting}\": {json.dumps(details)},\n"
                js_content += "    },\n"
            else:
                # Add new entries if not already covered by defaults
                js_content += f"\n    \"{name}\": {{\n"
                for setting, details in settings.items():
                    if isinstance(details, list) and len(details) == 6 and details[0] == "FLOAT":
                        js_content += f"        \"{setting}\": {json.dumps(details)},\n"
                    else:
                        print(f"Skipping setting {setting} due to unexpected format: {details}")
                js_content += "    },\n"
        js_content += "};\n\nexport { widgets };\n"
        
        # Write the JavaScript content to the file
        with open(filepath, 'w') as js_file:
            js_file.write(js_content)