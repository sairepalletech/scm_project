"""Default configuration settings for the dynaconf"""
# scm/defaults_config.py
import os
import logging
from typing import List, Set, Dict, Optional
from dynaconf import Dynaconf
from dynaconf.utils.boxing import DynaBox
from ordered_set import OrderedSet
import json
import shlex 
from deepdiff import DeepDiff
from json.decoder import JSONDecodeError
from pathlib import Path

from scm_config import defaults
from scm_config.defaults import JSON_DIFF_ATTR
from scm_config import constants
from subprocess import STDOUT, check_call, CalledProcessError
from scm_config import (
    DIR_ERROR,
    FILE_ERROR,
    SUCCESS,
    __app_name__
)

CONFIG_DIR = OrderedSet(['CONFIG_DIR', 'CONFIG_HASH_DIR'])
CONFIG_FILES = OrderedSet(['CONFIG_DEF_FILE', 'CONFIG_HASH_FILE'])
CONFIG_DIR_PATH = os.getcwd()
CONFIG_FILE_PATH = os.path.join(
    CONFIG_DIR_PATH,
    "settings.json")


def read_json(filename: str) -> Optional[Dict]:
    """
    Read and parse a JSON configuration file.
    
    Args:
        filename: Path to the JSON file to read
        
    Returns:
        Dictionary containing the parsed JSON, or FILE_ERROR on failure
    """
    try:
        with open(filename) as config_file:
            logging.info(f"Reading the JSON configuration {filename}")
            try:
                return dict(json.load(config_file))
            except JSONDecodeError:
                logging.warning(f"Invalid JSON file {filename}")
                return FILE_ERROR
    except FileNotFoundError:
        logging.error(f"File {filename} not found")
        return FILE_ERROR


def create_def_directory(user_dict: Dict) -> bool:
    """
    Create default directories for SCM configuration.
    
    Args:
        user_dict: Dictionary containing directory configuration
        
    Returns:
        True if all directories were created successfully, False otherwise
    """
    for dir_key in CONFIG_DIR:
        logging.info(f"Creating directory {dir_key}")
        dir_path = user_dict.get(dir_key)
        if dir_path:
            if not os.path.exists(dir_path):
                os.mkdir(dir_path)
            else:
                logging.info(f"{dir_key} directory already exists")
        else:
            logging.warning(f"Missing {dir_key} value to create the directories")
            return False
    return True


def create_def_files(user_dict: Dict) -> bool:
    """
    Create default configuration files for SCM.
    
    Args:
        user_dict: Dictionary containing file configuration
        
    Returns:
        True if all files were created successfully, False otherwise
    """
    for file_key in CONFIG_FILES:
        logging.info(f"Creating files {file_key}")
        file_name = user_dict.get(file_key)
        
        if not file_name:
            logging.warning(f"Missing {file_key} value to create the files")
            return False
            
        if os.path.exists(file_name):
            logging.info(f"{file_key} file already exists")
            continue
            
        if file_key == constants.CONFIG_DEF_FILE_KEY:
            # Create default TOML file
            file_path = os.path.join(
                user_dict[constants.CONFIG_DIR_KEY],
                file_name
            )
            Path(file_path).touch()
        else:
            # Create hash configuration file with empty JSON
            hash_file_path = os.path.join(
                user_dict[constants.CONFIG_HASH_DIR_KEY],
                file_name
            )
            if not os.path.exists(hash_file_path):
                Path(hash_file_path).touch()
                # Write empty JSON object
                with open(hash_file_path, "w") as outfile:
                    json.dump({}, outfile, indent=4)

    return True


def check_if_recipe_exists(recipe: str) -> bool:
    """
    Check if a recipe configuration file exists.
    
    Args:
        recipe: Name of the recipe to check
        
    Returns:
        True if the recipe file exists, False otherwise
    """
    recipe_path = os.path.join(
        os.getcwd(),
        os.environ[constants.ENV_ROOT_PATH],
        f"{recipe}{constants.EXT_TOML}"
    )
    return os.path.exists(recipe_path)


def del_recipe_file(recipe: str) -> None:
    """
    Delete a recipe configuration file.
    
    Args:
        recipe: Name of the recipe to delete
    """
    recipe_path = os.path.join(
        os.getcwd(),
        os.environ[constants.ENV_ROOT_PATH],
        f"{recipe}{constants.EXT_TOML}"
    )
    os.remove(recipe_path)


def get_user_settings(recipe: str, validator=None, environments: bool = True) -> Dict:
    """
    Load user settings from a recipe configuration file.
    
    Args:
        recipe: Name of the recipe to load
        validator: Optional validator for the settings
        environments: Whether to enable environment support
        
    Returns:
        Dictionary containing the user settings
    """
    return Dynaconf(
        settings_files=[f"{recipe}{constants.EXT_TOML}"],
        validators=validator
    )


def get_user_defined_resources(settings: Dict) -> Set:
    """
    Extract user-defined resources from settings, excluding Dynaconf parameters.
    
    Args:
        settings: Settings dictionary to parse
        
    Returns:
        Set of user-defined resource names
    """
    return OrderedSet([*settings]) - defaults.DEFAULT_PARAMTERS


def validate_unsupported_resources(user_resources: Set) -> Set:
    """
    Identify any unsupported resources in the user configuration.
    
    Args:
        user_resources: Set of user-defined resources
        
    Returns:
        Set of unsupported resource names
    """
    unsupported = (
        {*user_resources} - defaults.DEFAULT_PARAMTERS
    ) - defaults.SUPP_RES
    return unsupported


def gen_command(
        settings_dict: Dict,
        resource_type: str,
        output: Dict) -> None:
    """
    Generate OS commands from configuration settings.
    
    Args:
        settings_dict: Dictionary containing resource configurations
        resource_type: Type of resource (SERVICE, FILE, DIRECTORY, FIREWALL)
        output: Dictionary to store generated commands (modified in-place)
    """
    if resource_type.upper() == constants.RESOURCE_SERVICE:
        for resource_id, resource_config in settings_dict[resource_type].items():
            output[f"{resource_type}.{resource_id}"] = []
            
            if isinstance(resource_config, DynaBox) and resource_id != constants.ATTR_PARAMS:
                for service_name in resource_config[constants.ATTR_NAME]:
                    for action in resource_config[constants.ATTR_ACTION]:
                        if action in defaults.SERVICE_SETUP_ACTIONS:
                            output[f"{resource_type}.{resource_id}"].append(
                                f"{constants.CMD_SUDO} {constants.CMD_APT_GET} update -y"
                            )
                            output[f"{resource_type}.{resource_id}"].append(
                                f"{constants.CMD_SUDO} {constants.CMD_APT_GET} {action} {service_name} -y"
                            )
                        elif action in defaults.SERVICE_OP_ACTIONS:
                            output[f"{resource_type}.{resource_id}"].append(
                                f"{constants.CMD_SYSTEMCTL} {action} {service_name}"
                            )

                               
    if resource_type.upper() in [constants.RESOURCE_DIRECTORY, constants.RESOURCE_FILE]:
        for resource_id, resource_config in settings_dict[resource_type].items():
            output[f"{resource_type}.{resource_id}"] = []
            
            for target_name in resource_config[constants.ATTR_NAME]:
                for action in resource_config[constants.ATTR_ACTION]:
                    # Handle file content creation
                    if action == constants.ACTION_CREATE and resource_config.get(constants.ATTR_CONTENT):
                        for content_line in resource_config[constants.ATTR_CONTENT]:
                            mode = constants.FILE_MODE_WRITE if resource_config.get(constants.ATTR_OVERRIDE) else constants.FILE_MODE_APPEND
                            cmd = f"{constants.CMD_ECHO} '{content_line}' {mode} {target_name}"
                            output[f"{resource_type}.{resource_id}"].append(cmd)

                    # Handle directory creation
                    if action == constants.ACTION_CREATE and resource_type == constants.RESOURCE_DIRECTORY:
                        cmd = f"{constants.CMD_MKDIR} -p {target_name}"
                        output[f"{resource_type}.{resource_id}"].append(cmd)

                    # Handle ownership changes
                    params = resource_config.get(constants.ATTR_PARAMS, {})
                    owner = params.get('owner')
                    group = params.get('group')
                    
                    if action == constants.ACTION_CREATE and owner and group:
                        cmd = f"{constants.CMD_CHOWN} {owner}:{group} {target_name}"
                        if params.get('recurse') and json.loads(str(params.get('recurse')).lower()):
                            cmd += " -R"
                        output[f"{resource_type}.{resource_id}"].append(cmd)


                # Handle notifications to other resources
                notifies_config = resource_config.get(constants.ATTR_NOTIFIES)
                if notifies_config:
                    notifies_json = json.loads(notifies_config.replace("\'", "\""))
                    for notify_name in notifies_json[constants.ATTR_NAME]:
                        for notify_action in notifies_json[constants.ATTR_ACTION]:
                            if notify_action == constants.ACTION_INSTALL:
                                output[f"{resource_type}.{resource_id}"].append(
                                    f"{constants.CMD_APT_GET} {notify_action} {notify_name} -y"
                                )
                            else:
                                output[f"{resource_type}.{resource_id}"].append(
                                    f"{constants.CMD_SYSTEMCTL} {notify_action} {notify_name}"
                                )

    if resource_type.upper() == constants.RESOURCE_FIREWALL:
        for resource_id, resource_config in settings_dict[resource_type].items():
            output[f"{resource_type}.{resource_id}"] = []
            
            for rule_name in resource_config[constants.ATTR_NAME]:
                for action in resource_config[constants.ATTR_ACTION]:
                    if action == constants.ACTION_ALLOW:
                        cmd = f"{constants.CMD_SUDO} {constants.CMD_UFW} {action} in {rule_name}"
                        output[f"{resource_type}.{resource_id}"].append(cmd)


def _get_diff_hash(existing_hash: Dict, current_hash: Dict) -> List[str]:
    """
    Compare two hash dictionaries and return the list of changed keys.
    
    Args:
        existing_hash: Previously stored hash values
        current_hash: Current hash values to compare
        
    Returns:
        List of keys that have changed or are new
    """
    changed_keys = []
    
    if existing_hash:
        diff_result = DeepDiff(current_hash, existing_hash)
        for diff_type in JSON_DIFF_ATTR:
            if diff_result.get(diff_type):
                for change_path in diff_result.get(diff_type):
                    # Extract the key from the path string
                    start_bracket = change_path.find('[')
                    end_bracket = change_path.find(']')
                    if start_bracket != -1 and end_bracket != -1:
                        key = change_path[start_bracket + 1:end_bracket]
                        changed_keys.append(key.replace("'", ""))
    else:
        # No existing hash means all keys are new
        changed_keys = list(current_hash.keys())
        
    return changed_keys


def run_os_command(command: str) -> int:
    """
    Execute an OS command safely.
    
    Args:
        command: Shell command to execute
        
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        command_parts = shlex.split(command)
        
        # Special handling for echo commands to redirect output to files
        if command_parts[0] == constants.CMD_ECHO:
            mode = "a" if command_parts[2] == constants.FILE_MODE_APPEND else "w"
            with open(command_parts[-1], mode=mode) as output_file:
                exit_code = check_call(command_parts[:2], stderr=STDOUT, stdout=output_file)
        else:
            exit_code = check_call(command_parts, stderr=STDOUT)
            
        return exit_code
        
    except CalledProcessError as error:
        logging.error(f"Command failed: {error}")
        return 1 


