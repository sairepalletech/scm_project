"""Module provides the CLI package"""
# scm/cli.py
import os
import logging
from scm_config.defaults import SETTINGS_DATA
from typing import Optional
from ordered_set import OrderedSet
import typer
import hashlib
import functools
from scm_config import __version__, __app_name__, default_config
from scm_config.default_config import read_json, create_def_directory, create_def_files,check_if_recipe_exists, get_user_settings, get_user_defined_resources, validate_unsupported_resources, gen_command, run_os_command,_get_diff_hash, del_recipe_file
from dynaconf.utils.boxing import DynaBox
from collections import OrderedDict
from scm_config import defaults
import json

# BASIC LOGGING MESSAGE
logging.basicConfig(format='[%(levelname)s][%(asctime)s]::%(message)s',
                    datefmt="%m-%d-%Y %H:%M:%S", level=logging.INFO)
logger = logging.getLogger()

# Global variables
def_settings_dict = {}

app = typer.Typer()


def _version(value: bool) -> None:
    if value:
        typer.echo(f"{__app_name__} - v{__version__}")
        raise typer.Exit()


@app.command()
def init(
    file: str = typer.Option(
        str(default_config.CONFIG_FILE_PATH),
        "--default-file",
        "-f"
    )
) -> None:
    global def_settings_dict
     
    with open(file, "w") as outfile:
        json.dump(SETTINGS_DATA, outfile)
    
    
    def_settings_dict = read_json(file)['default']

    os.environ['ROOT_PATH_FOR_DYNACONF'] = def_settings_dict.get(
        'CONFIG_DIR', os.path.join(os.getcwd(), "config"))

    is_dir_created = create_def_directory(def_settings_dict)

    if not is_dir_created:
        logging.warning("default directories creation failed")
        raise typer.Exit()

    is_files_created = create_def_files(def_settings_dict)

    if not is_files_created:
        logging.warning("default files creation failed")
        raise typer.Exit()

    
    return 0

# create command


@app.command()
def create(
    recipe: str = typer.Option(...),
    force: bool = typer.Option(False)
) -> None:

    init(default_config.CONFIG_FILE_PATH)
    con_dir, def_file = def_settings_dict.get('CONFIG_DIR'), f"{recipe}.toml"
    con_dir_full = os.path.join(os.getcwd(), con_dir)
    def_file_full = os.path.join(con_dir_full, def_file)
    
    

    if not check_if_recipe_exists(recipe) or force:
        with open(def_file_full, mode="w") as f:
            f.write(f"# Place holder for creating the scm {recipe} recipe")
    else:
        logging.warning(
            f"`{recipe}` configuration file exists, use --force to override.")
        raise typer.Exit()

    
    
    return 0


@app.command()
def info(
    recipe: str = typer.Option(...)
) -> None:

    init(default_config.CONFIG_FILE_PATH)
    con_dir, def_file = def_settings_dict.get('CONFIG_DIR'), f"{recipe}.toml"
    con_dir_full = os.path.join(os.getcwd(), con_dir)
    def_file_full = os.path.join(con_dir_full, def_file)

    if not check_if_recipe_exists(recipe):
        logging.warning(
            f"recipe {recipe} doesn't exist in the config directory")
        logging.warning("use `scm create` for the recipe creation")
        raise typer.Exit()

    user_settings = get_user_settings(recipe)
    user_resources = get_user_defined_resources(user_settings)

    for res in user_resources:
        if res in user_settings:
            for i in user_settings[res]:
                logging.info(f"{res}.{i} - {user_settings[res][i]}")

    return 0

# validate command


@app.command()
def validate(
    recipe: str = typer.Option(...)
) -> None:

    init(default_config.CONFIG_FILE_PATH)
    con_dir, def_file = def_settings_dict.get('CONFIG_DIR'), f"{recipe}.toml"
    con_dir_full = os.path.join(os.getcwd(), con_dir)
    def_file_full = os.path.join(con_dir_full, def_file)

    if not check_if_recipe_exists(recipe):
        logging.warning(
            f"recipe {recipe} doesn't exist in the config directory")
        logging.warning("use `scm create` for the recipe creation")
        raise typer.Exit()

    res_validation = validate_unsupported_resources(get_user_settings(recipe))

    if res_validation:
        logging.warning(
            f"Unsupported resources found in the `{recipe}` configuration file"
        )
        for i in res_validation:
            logging.warning(
                f"`{i}` resource in {recipe} recipe isn't supported")
            raise typer.Exit()

    user_settings = get_user_settings(recipe)
    user_resources = get_user_defined_resources(user_settings)

    if not user_resources:
        logging.warning(
            f"No user resources found in the `{recipe}` configuration file")
        raise typer.Exit()

    for res in user_resources:
        if res in user_settings:
            for i in user_settings[res]:

                if not isinstance(user_settings[res][i], DynaBox):
                    logging.warning(
                        f"Missing subconfig `{res}` resource in {recipe} recipe"
                    )
                    raise typer.Exit()

                if not user_settings[res][i].get('name', None):
                    logging.warning(
                        f"Missing `name`attributes in resource `{i}` in recipe {recipe}"
                    )
                    raise typer.Exit()

                if not user_settings[res][i].get('action', None):
                    logging.warning(
                        f"Missing `action` attributes in resource `{i}` in recipe {recipe}"
                    )
                    raise typer.Exit()

                defaults.UNSUPPORTED_ATTR = OrderedSet(
                    user_settings[res][i].keys()) - defaults.RES_ATTRIBUTES

                if (defaults.UNSUPPORTED_ATTR -
                        defaults.SRV_ATTRIBUTES) and res.upper() == "SERVICE":
                    logging.warning(
                        f"Found one more attributes that aren't supported"
                    )
                    for unsup in (
                            defaults.UNSUPPORTED_ATTR -
                            defaults.SRV_ATTRIBUTES):
                        logging.warning(
                            f"`{unsup}` not supported attribute in resource {res} in recipe {recipe}"
                        )
                    raise typer.Exit()

                if (defaults.UNSUPPORTED_ATTR -
                        defaults.DIR_ATTRIBUTES) and res.upper() == "DIRECTORY":
                    logging.warning(
                        f"Found one more attributes that aren't supported"
                    )
                    for unsup in (
                            defaults.UNSUPPORTED_ATTR -
                            defaults.DIR_ATTRIBUTES):
                        logging.warning(
                            f"`{unsup}` not supported attribute in resource {res} in recipe {recipe}"
                        )
                    raise typer.Exit()

                if (defaults.UNSUPPORTED_ATTR -
                        defaults.FILE_ATTRIBUTES) and res.upper() == "FILE":
                    logging.warning(
                        f"Found one more attributes that aren't supported"
                    )
                    for unsup in (
                            defaults.UNSUPPORTED_ATTR -
                            defaults.FILE_ATTRIBUTES):
                        logging.warning(
                            f"`{unsup}` not supported attribute in resource {res} in recipe {recipe}"
                        )
                    raise typer.Exit()

                # now validate the values from the user-input string
                user_values = user_settings[res][i].get('action', None)
                if res.upper() == "SERVICE":
                    for val in user_values:
                        if val not in defaults.SERVICE_SETUP_ACTIONS.union(
                                defaults.SERVICE_OP_ACTIONS):
                            logging.warning(
                                f"`{val}` not supported in action attribute in resource {res} in recipe {recipe}"
                            )
                            raise typer.Exit()
                
                else:
                    if res.upper() in ["FILE", "DIRECTORY"]:
                        for val in user_values:
                            if val not in defaults.DIR_FILE_ACTIONS:
                                logging.warning(
                                    f"`{val}` not supported in action attribute in resource {res} in recipe {recipe}"
                                )
                                raise typer.Exit()
                
                    if res.upper() in ["FIREWALL"]:
                        for val in user_values:
                            if val not in defaults.FIREWALL_ACTIONS:
                                logging.warning(
                                    f"`{val}` not supported in action attribute in resource {res} in recipe {recipe}"
                                )
                                raise typer.Exit()

    logging.info(
        f"{recipe} recipe file is valid for push, use `scm diff` to differences with the existing configuration")
    return 0

def push_command(recipe) -> tuple:
    
    curr_resouces = OrderedDict()

    settings = read_json(default_config.CONFIG_FILE_PATH)['default']

    os.environ['ROOT_PATH_FOR_DYNACONF'] = settings.get(
        'CONFIG_DIR', os.path.join(os.getcwd(), "config"))

    hash_config_dir = os.path.join(
        settings.get('CONFIG_HASH_DIR'),
        settings.get('CONFIG_HASH_FILE'))

    validate(recipe)

    user_settings = get_user_settings(recipe)
    user_resources = get_user_defined_resources(user_settings)
    
    curr_resouces[recipe] = {}   
    for i in user_resources:
        gen_command(user_settings, i, curr_resouces[recipe])
    
    write_dict = {}
    write_dict[recipe] = {}
    
    for index,value in curr_resouces[recipe].items():
        concat = functools.reduce(lambda x, y: x + y, value, "")
        write_dict[recipe][index] = hashlib.md5(concat.encode("utf-8")).hexdigest()
    
    existing_hash = read_json(hash_config_dir)
    
    if not existing_hash:
        existing_hash[recipe] = {}
    
    diff_output = _get_diff_hash(existing_hash[recipe],write_dict[recipe])
      
    return (diff_output, curr_resouces, write_dict)


@app.command()
def push(
    recipe: str = typer.Option(...)
) -> None:
    diff_output, curr_resources, new_hash_dict = push_command(recipe)
    
    if not diff_output:
        logging.info(f"`{recipe}` configuration is update to date with the existing configuration")
        raise typer.Exit()
    
    
    settings = read_json(default_config.CONFIG_FILE_PATH)['default']
    
    hash_config_dir = os.path.join(
        settings.get('CONFIG_HASH_DIR'),
        settings.get('CONFIG_HASH_FILE'))
    
    logging.info("Following resources will be applied:")
    for cmd in diff_output: 
        if cmd in  curr_resources[recipe]:       
            logging.info(f"{cmd}: {curr_resources[recipe][cmd]}")
            for c in curr_resources[recipe][cmd]: 
                logging.info(f"Applying the command `{c}`")
                code = run_os_command(c)
                if code:
                    logging.error(f"Failed to run the command {c}")
                    raise typer.Exit()
                
    with open(hash_config_dir, "w") as output:
        json.dump(new_hash_dict, output)

    logging.info("Applied all the changes without any issues")
    return 0


@app.command()
def diff(
    recipe: str = typer.Option(...)
) -> None:
    
    output, curr_resources, new_hash_dict = push_command(recipe)
    
    if not output:
        logging.info(f"`{recipe}` configuration is update to date with the existing configuration")
    
    for i in output: 
        if i in  curr_resources[recipe]:
            logging.info("Following resources will be applied:")
            logging.info(f"{i}: {curr_resources[recipe][i]}")    
        
    return 0

@app.command()
def remove(
    recipe: str = typer.Option(...), 
    force: bool = False, 
    clean_files: bool = False 
) -> None:
    
    settings = read_json(default_config.CONFIG_FILE_PATH)['default']

    os.environ['ROOT_PATH_FOR_DYNACONF'] = settings.get(
        'CONFIG_DIR', os.path.join(os.getcwd(), "config"))

    hash_config_dir = os.path.join(
        settings.get('CONFIG_HASH_DIR'),
        settings.get('CONFIG_HASH_FILE'))

    validate(recipe)
    
    if force: 
        logging.info(f"This configuration removes the recipe `{recipe}`")
        logging.info(f"Please set the flag to force `--force` to remove the configuration")
        raise typer.Exit()
    
    if not clean_files:
        logging.info("Configuration doesn't remove the recipe file, please clean up manually")
    
    with open(hash_config_dir) as data_file:
        data = json.load(data_file)
    
    if not data.get(recipe, None):
        logging.warning(f"`recipe`configuration not found in the hash dataset")
        raise typer.Exit()
    
    del data[recipe]
    
    with open(hash_config_dir, "w") as data_file:
        data = json.dump(data, data_file)    
    
    if clean_files and check_if_recipe_exists(recipe):
        logging.info("dropping the recipe file..")
        del_recipe_file(recipe)
        
         
    return 0



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
