import os
import json

class ConfigReader:
    _config = None

    @classmethod
    def load_config(cls):
        if cls._config is None:
            dir_path = os.path.dirname(os.path.realpath(__file__))
            config_path = os.path.join(dir_path, 'config.json')
            try:
                with open(config_path, 'r') as file:
                    cls._config = json.load(file)
            except FileNotFoundError:
                Logger.print_sn0w(f"Configuration file not found at {config_path}. Using default settings.")
                cls._config = {}  # Use an empty dict as a fallback
        return cls._config

    @classmethod
    def get_setting(cls, setting_key, default=None):
        config = cls.load_config()
        return config.get(setting_key, default)

class Logger:
    RED_TEXT = "\033[0;35m"
    RESET_TEXT = "\033[0m"
    PREFIX = "[sn0w] "

    def __init__(self):
        self.logging_level = ConfigReader.get_setting('logging_level', 'NONE')

    @classmethod
    def print_sn0w(cls, message):
        print(f"{cls.RED_TEXT}{cls.PREFIX}{cls.RESET_TEXT}{message}")

    def log(self, message, level="GENERAL"):
        levels = {"NONE": 0, "GENERAL": 1, "ALL": 2}
        if levels.get(level, 0) <= levels.get(self.logging_level, 0):
            self.print_sn0w(message)

class Utility:
    @staticmethod
    def levenshtein_distance(s1, s2):
        if len(s1) < len(s2):
            return Utility.levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]