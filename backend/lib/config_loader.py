import configparser
import os
from typing import Any


class ConfigLoader:
    """
    OOP Configuration Loader responsible for parsing and providing access
    to application parameters defined in config.properties.
    """

    def __init__(self, config_file_path: str = "lib/config.properties"):
        self.config_file_path = config_file_path
        self.config = configparser.ConfigParser()
        self._load_config()

    def _load_config(self) -> None:
        """Loads and parses the config.properties file."""
        if not os.path.exists(self.config_file_path):
            # Fallback path if run from backend subdirectory or root
            alt_path = os.path.join(os.path.dirname(__file__), "config.properties")
            if os.path.exists(alt_path):
                self.config_file_path = alt_path
            else:
                raise FileNotFoundError(f"Configuration file not found at {self.config_file_path}")

        self.config.read(self.config_file_path)

    def get(self, section: str, key: str, default: Any = None) -> str:
        """Retrieves a configuration value by section and key."""
        try:
            return self.config.get(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return default

    def get_int(self, section: str, key: str, default: int = 0) -> int:
        """Retrieves an integer configuration value."""
        try:
            return self.config.getint(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return default

    @property
    def database_url(self) -> str:
        """Generates the SQLAlchemy async/sync database connection URL."""
        user = self.get("DATABASE", "db_user", "postgres")
        password = self.get("DATABASE", "db_password", "postgres")
        host = self.get("DATABASE", "db_host", "localhost")
        port = self.get("DATABASE", "db_port", "5432")
        db_name = self.get("DATABASE", "db_name", "cs_command_center")
        return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db_name}"


# Global singleton instance for easy import across modules
config_loader = ConfigLoader()
