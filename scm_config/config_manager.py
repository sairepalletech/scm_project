"""Configuration management utilities for SCM."""
import os
import json
import logging
from typing import Dict, Optional
from pathlib import Path

from scm_config import constants
from scm_config.defaults import SETTINGS_DATA
from scm_config.default_config import (
    read_json,
    create_def_directory,
    create_def_files,
    CONFIG_FILE_PATH
)


class ConfigManager:
    """Manages SCM configuration state and settings."""
    
    def __init__(self):
        """Initialize the configuration manager."""
        self._settings: Optional[Dict] = None
        self._config_file_path: str = CONFIG_FILE_PATH
    
    def initialize(self, config_file: Optional[str] = None) -> Dict:
        """
        Initialize SCM configuration by creating necessary files and directories.
        
        Args:
            config_file: Optional path to configuration file
            
        Returns:
            Dictionary containing the default settings
            
        Raises:
            typer.Exit: If initialization fails
        """
        if config_file:
            self._config_file_path = config_file
            
        # Create settings file
        with open(self._config_file_path, "w") as outfile:
            json.dump(SETTINGS_DATA, outfile, indent=4)
        
        # Read settings
        settings_data = read_json(self._config_file_path)
        self._settings = settings_data['default']
        
        # Set environment variable for Dynaconf
        config_dir = self._settings.get(
            constants.CONFIG_DIR_KEY,
            os.path.join(os.getcwd(), constants.DEFAULT_CONFIG_DIR)
        )
        os.environ[constants.ENV_ROOT_PATH] = config_dir
        
        # Create directories
        if not create_def_directory(self._settings):
            logging.error("Failed to create default directories")
            raise RuntimeError("Directory creation failed")
        
        # Create files
        if not create_def_files(self._settings):
            logging.error("Failed to create default files")
            raise RuntimeError("File creation failed")
        
        return self._settings
    
    def get_settings(self) -> Dict:
        """
        Get the current settings.
        
        Returns:
            Dictionary containing settings
            
        Raises:
            RuntimeError: If settings haven't been initialized
        """
        if self._settings is None:
            # Auto-initialize if not already done
            self.initialize()
        return self._settings
    
    def get_config_dir(self) -> str:
        """Get the configuration directory path."""
        settings = self.get_settings()
        return settings.get(constants.CONFIG_DIR_KEY, constants.DEFAULT_CONFIG_DIR)
    
    def get_hash_config_path(self) -> str:
        """Get the path to the hash configuration file."""
        settings = self.get_settings()
        return os.path.join(
            settings.get(constants.CONFIG_HASH_DIR_KEY, 'config_hash'),
            settings.get(constants.CONFIG_HASH_FILE_KEY, 'hash_config_md5.json')
        )
    
    def get_recipe_path(self, recipe: str) -> str:
        """
        Get the full path to a recipe file.
        
        Args:
            recipe: Name of the recipe
            
        Returns:
            Full path to the recipe file
        """
        config_dir = self.get_config_dir()
        return os.path.join(
            os.getcwd(),
            config_dir,
            f"{recipe}{constants.EXT_TOML}"
        )


# Global instance for use in CLI
_config_manager = ConfigManager()


def get_config_manager() -> ConfigManager:
    """Get the global configuration manager instance."""
    return _config_manager
