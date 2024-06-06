import sys
from typing import Any
import os
import json

from loguru import logger

PROGRAM_NAME = "agcl"


def get_program_folder() -> str:
    return os.path.join(os.path.expanduser("~"), ".config", PROGRAM_NAME)


class ConfigManager:
    _instance = None  # singleton
    CONFIG_FILE = os.path.join(get_program_folder(), "config.json")

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._load_config()
            cls._instance.set_logging()
            logger.debug(f"Loading config from {cls._instance.CONFIG_FILE}")
        return cls._instance

    def _load_config(self):
        os.makedirs(os.path.dirname(self.CONFIG_FILE), exist_ok=True)
        if not os.path.exists(self.CONFIG_FILE):
            self.config = {}
            self._save_config()
        else:
            with open(self.CONFIG_FILE, "r") as f:
                self.config = json.load(f)

    def _save_config(self):
        with open(self.CONFIG_FILE, "w") as f:
            json.dump(self.config, f, indent=4)

    def get(self, key: str, default: Any = None):
        return self.config.get(key, default)

    def set(self, key: str, value: Any):
        self.config[key] = value
        self._save_config()
        return value

    def get_log_file(self) -> str:
        logfile = self.get("log_path")
        if not logfile:
            logfile = self.set(
                "log_path", os.path.join(get_program_folder(), "user_program.log")
            )
            logger.info(f"Log file not set, setting to {logfile}")
        return logfile

    def set_logging(self, level=""):
        if not level:
            # level = self.get("log_level", "WARNING")
            level = self.get("log_level", "DEBUG")
        logger.remove()
        logger.add(sys.stderr, level=level)
        self.set("log_level", level)
