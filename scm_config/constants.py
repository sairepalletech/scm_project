"""Constants used throughout the SCM application."""

# Resource types
RESOURCE_SERVICE = "SERVICE"
RESOURCE_FILE = "FILE"
RESOURCE_DIRECTORY = "DIRECTORY"
RESOURCE_FIREWALL = "FIREWALL"

# Service actions
ACTION_INSTALL = "install"
ACTION_REMOVE = "remove"
ACTION_STOP = "stop"
ACTION_START = "start"
ACTION_RESTART = "restart"
ACTION_RELOAD = "reload"
ACTION_DISABLE = "disable"
ACTION_ENABLE = "enable"

# File and directory actions
ACTION_CREATE = "create"

# Firewall actions
ACTION_ALLOW = "allow"

# Resource attributes
ATTR_NAME = "name"
ATTR_ACTION = "action"
ATTR_PARAMS = "params"
ATTR_NOTIFIES = "notifies"
ATTR_CONTENT = "content"
ATTR_OVERRIDE = "override"

# File operation modes
FILE_MODE_APPEND = ">>"
FILE_MODE_WRITE = ">"

# Command prefixes
CMD_SUDO = "sudo"
CMD_APT_GET = "apt-get"
CMD_SYSTEMCTL = "systemctl"
CMD_MKDIR = "mkdir"
CMD_CHOWN = "chown"
CMD_ECHO = "echo"
CMD_UFW = "ufw"

# Configuration keys
CONFIG_DIR_KEY = "CONFIG_DIR"
CONFIG_DEF_FILE_KEY = "CONFIG_DEF_FILE"
CONFIG_HASH_DIR_KEY = "CONFIG_HASH_DIR"
CONFIG_HASH_FILE_KEY = "CONFIG_HASH_FILE"

# Environment variables
ENV_ROOT_PATH = "ROOT_PATH_FOR_DYNACONF"

# File extensions
EXT_TOML = ".toml"
EXT_JSON = ".json"

# Default values
DEFAULT_CONFIG_DIR = "config"
DEFAULT_SETTINGS_FILE = "settings.json"
