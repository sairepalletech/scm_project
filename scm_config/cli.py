"""Module provides the CLI package"""
import os
import logging
from typing import Optional
from collections import OrderedDict
import json
import hashlib
import functools

import typer
from ordered_set import OrderedSet

from scm_config import __version__, __app_name__
from scm_config import constants
from scm_config.config_manager import get_config_manager
from scm_config.validators import RecipeValidator
from scm_config.default_config import (
    read_json,
    check_if_recipe_exists,
    get_user_settings,
    get_user_defined_resources,
    gen_command,
    run_os_command,
    _get_diff_hash,
    del_recipe_file,
    CONFIG_FILE_PATH
)

# Configure logging
logging.basicConfig(
    format='[%(levelname)s][%(asctime)s]::%(message)s',
    datefmt="%m-%d-%Y %H:%M:%S",
    level=logging.INFO
)
logger = logging.getLogger()

app = typer.Typer()


def _version(value: bool) -> None:
    """Display version information."""
    if value:
        typer.echo(f"{__app_name__} - v{__version__}")
        raise typer.Exit()


@app.command()
def init(
    file: str = typer.Option(
        str(CONFIG_FILE_PATH),
        "--default-file",
        "-f",
        help="Path to configuration file"
    )
) -> None:
    """
    Initialize SCM by creating necessary directories and files.
    
    Args:
        file: Path to the configuration file
    """
    try:
        config_mgr = get_config_manager()
        config_mgr.initialize(file)
        logging.info("SCM initialized successfully")
    except RuntimeError as error:
        logging.error(f"Initialization failed: {error}")
        raise typer.Exit(1)

@app.command()
def create(
    recipe: str = typer.Option(..., help="Name of the recipe to create"),
    force: bool = typer.Option(False, help="Force overwrite if recipe exists")
) -> None:
    """
    Create a new recipe configuration file.
    
    Args:
        recipe: Name of the recipe to create
        force: Whether to overwrite existing recipe
    """
    # Ensure SCM is initialized
    config_mgr = get_config_manager()
    try:
        config_mgr.get_settings()
    except RuntimeError:
        init(CONFIG_FILE_PATH)
    
    recipe_path = config_mgr.get_recipe_path(recipe)
    
    # Check if recipe already exists
    if check_if_recipe_exists(recipe) and not force:
        logging.warning(
            f"`{recipe}` configuration file exists, use --force to override."
        )
        raise typer.Exit(1)
    
    # Create the recipe file
    with open(recipe_path, mode="w") as recipe_file:
        recipe_file.write(f"# Configuration for {recipe} recipe\n")
    
    logging.info(f"Created recipe: {recipe}")
    logging.info(f"Edit the file at: {recipe_path}")


@app.command()
def info(
    recipe: str = typer.Option(..., help="Name of the recipe to display")
) -> None:
    """
    Display information about a recipe configuration.
    
    Args:
        recipe: Name of the recipe
    """
    # Ensure recipe exists
    if not check_if_recipe_exists(recipe):
        logging.error(f"Recipe '{recipe}' doesn't exist in the config directory")
        logging.info("Use `scm create --recipe <name>` to create a recipe")
        raise typer.Exit(1)
    
    # Load and display recipe information
    user_settings = get_user_settings(recipe)
    user_resources = get_user_defined_resources(user_settings)
    
    logging.info(f"Recipe: {recipe}")
    logging.info("-" * 50)
    
    for resource_type in user_resources:
        if resource_type in user_settings:
            for resource_id, config in user_settings[resource_type].items():
                logging.info(f"{resource_type}.{resource_id} - {config}")

@app.command()
def validate(
    recipe: str = typer.Option(..., help="Name of the recipe to validate")
) -> None:
    """
    Validate a recipe configuration file.
    
    Args:
        recipe: Name of the recipe to validate
    """
    # Ensure recipe exists
    if not check_if_recipe_exists(recipe):
        logging.error(f"Recipe '{recipe}' doesn't exist in the config directory")
        logging.info("Use `scm create --recipe <name>` to create a recipe")
        raise typer.Exit(1)
    
    # Load recipe settings
    user_settings = get_user_settings(recipe)
    
    # Validate using the RecipeValidator
    validator = RecipeValidator(recipe, user_settings)
    
    if not validator.validate_all():
        validator.log_errors()
        logging.error(f"Recipe '{recipe}' validation failed")
        raise typer.Exit(1)
    
    logging.info(f"Recipe '{recipe}' is valid")
    logging.info("Use `scm diff --recipe <name>` to see differences with existing configuration")

def push_command(recipe: str) -> tuple:
    """
    Prepare a recipe for push by validating and computing changes.
    
    Args:
        recipe: Name of the recipe to prepare
        
    Returns:
        Tuple of (changed_keys, resources_commands, new_hash_dict)
    """
    # Get configuration manager
    config_mgr = get_config_manager()
    try:
        settings = config_mgr.get_settings()
    except RuntimeError:
        init(CONFIG_FILE_PATH)
        settings = config_mgr.get_settings()
    
    hash_config_path = config_mgr.get_hash_config_path()
    
    # Validate recipe
    validate(recipe)
    
    # Load user settings and resources
    user_settings = get_user_settings(recipe)
    user_resources = get_user_defined_resources(user_settings)
    
    # Generate commands for all resources
    current_resources = OrderedDict()
    current_resources[recipe] = {}
    
    for resource_type in user_resources:
        gen_command(user_settings, resource_type, current_resources[recipe])
    
    # Compute hashes for each resource command set
    hash_dict = {recipe: {}}
    
    for resource_key, commands in current_resources[recipe].items():
        # Concatenate all commands and compute MD5 hash
        combined_commands = functools.reduce(lambda x, y: x + y, commands, "")
        hash_dict[recipe][resource_key] = hashlib.md5(
            combined_commands.encode("utf-8")
        ).hexdigest()
    
    # Load existing hashes
    existing_hash = read_json(hash_config_path)
    if not existing_hash:
        existing_hash = {}
    if recipe not in existing_hash:
        existing_hash[recipe] = {}
    
    # Compute differences
    changed_keys = _get_diff_hash(existing_hash[recipe], hash_dict[recipe])
    
    return (changed_keys, current_resources, hash_dict)


@app.command()
def push(
    recipe: str = typer.Option(..., help="Name of the recipe to apply")
) -> None:
    """
    Apply a recipe configuration to the system.
    
    Args:
        recipe: Name of the recipe to push
    """
    # Compute changes
    changed_keys, curr_resources, new_hash_dict = push_command(recipe)
    
    # Check if there are any changes
    if not changed_keys:
        logging.info(f"Recipe '{recipe}' is up to date with existing configuration")
        raise typer.Exit(0)
    
    # Get hash configuration path
    config_mgr = get_config_manager()
    hash_config_path = config_mgr.get_hash_config_path()
    
    # Apply changes
    logging.info("Following resources will be applied:")
    for resource_key in changed_keys:
        if resource_key in curr_resources[recipe]:
            commands = curr_resources[recipe][resource_key]
            logging.info(f"{resource_key}: {commands}")
            
            for command in commands:
                logging.info(f"Applying command: `{command}`")
                exit_code = run_os_command(command)
                
                if exit_code != 0:
                    logging.error(f"Failed to run command: {command}")
                    raise typer.Exit(1)
    
    # Save new hash configuration
    with open(hash_config_path, "w") as hash_file:
        json.dump(new_hash_dict, hash_file, indent=4)
    
    logging.info("Applied all changes successfully")


@app.command()
def diff(
    recipe: str = typer.Option(..., help="Name of the recipe to check")
) -> None:
    """
    Show differences between recipe and current configuration.
    
    Args:
        recipe: Name of the recipe to check
    """
    # Compute changes
    changed_keys, curr_resources, new_hash_dict = push_command(recipe)
    
    # Display results
    if not changed_keys:
        logging.info(f"Recipe '{recipe}' is up to date with existing configuration")
        return
    
    logging.info("Following resources will be applied:")
    for resource_key in changed_keys:
        if resource_key in curr_resources[recipe]:
            commands = curr_resources[recipe][resource_key]
            logging.info(f"{resource_key}: {commands}")

@app.command()
def remove(
    recipe: str = typer.Option(..., help="Name of the recipe to remove"),
    force: bool = typer.Option(False, help="Force removal of the recipe"),
    clean_files: bool = typer.Option(False, help="Also remove the recipe file")
) -> None:
    """
    Remove a recipe from the hash configuration.
    
    Args:
        recipe: Name of the recipe to remove
        force: Whether to proceed with removal
        clean_files: Whether to also delete the recipe file
    """
    # Validate recipe exists
    validate(recipe)
    
    # Check force flag (logic seems inverted in original - keeping as is for compatibility)
    if not force:
        logging.info(f"This will remove the recipe '{recipe}'")
        logging.info("Please use `--force` flag to confirm removal")
        raise typer.Exit(0)
    
    # Get configuration manager
    config_mgr = get_config_manager()
    hash_config_path = config_mgr.get_hash_config_path()
    
    # Load hash data
    with open(hash_config_path) as hash_file:
        hash_data = json.load(hash_file)
    
    # Check if recipe exists in hash
    if recipe not in hash_data:
        logging.warning(f"Recipe '{recipe}' not found in hash configuration")
        raise typer.Exit(1)
    
    # Remove recipe from hash
    del hash_data[recipe]
    
    # Save updated hash
    with open(hash_config_path, "w") as hash_file:
        json.dump(hash_data, hash_file, indent=4)
    
    logging.info(f"Removed recipe '{recipe}' from configuration")
    
    # Optionally remove recipe file
    if clean_files and check_if_recipe_exists(recipe):
        logging.info("Removing recipe file...")
        del_recipe_file(recipe)
        logging.info("Recipe file removed")
    else:
        logging.info("Recipe file not removed. Use --clean-files to remove it")



@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="Display's the application version",
        callback=_version,
        is_eager=True,
    )
) -> None:
    return 0
