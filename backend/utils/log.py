import logging
import os
import sys
from typing import Optional


class AppLogger:
    """
    OOP Logger Manager providing a centralized, structured logging setup
    that outputs to both console and log/app.log file.
    """

    def __init__(self, name: str = "CommandCenter", log_dir: str = "log", log_file: str = "app.log", level: str = "INFO"):
        self.name = name
        self.log_dir = log_dir
        self.log_file = log_file
        self.level_str = level
        self.logger = logging.getLogger(self.name)
        self._setup_logger()

    def _setup_logger(self) -> None:
        """Configures logger handlers, formatters, and file outputs."""
        log_level = getattr(logging, self.level_str.upper(), logging.INFO)
        self.logger.setLevel(log_level)

        # Avoid adding duplicate handlers if already configured
        if self.logger.handlers:
            return

        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s] [%(filename)s:%(lineno)d] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # 1. Console Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(log_level)
        self.logger.addHandler(console_handler)

        # 2. File Handler
        try:
            # Ensure log directory exists
            if not os.path.exists(self.log_dir):
                os.makedirs(self.log_dir, exist_ok=True)

            log_path = os.path.join(self.log_dir, self.log_file)
            file_handler = logging.FileHandler(log_path, encoding="utf-8")
            file_handler.setFormatter(formatter)
            file_handler.setLevel(log_level)
            self.logger.addHandler(file_handler)
        except Exception as e:
            self.logger.warning(f"Could not initialize log file handler: {e}")

    def get_logger(self) -> logging.Logger:
        """Returns the configured Python logger instance."""
        return self.logger


# Global logger instance helper
default_logger_manager = AppLogger()
logger = default_logger_manager.get_logger()
