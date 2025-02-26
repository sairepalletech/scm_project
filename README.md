# SCM

Self Managed Configuration Management (SCM) is a simple command-line app for configuration management, written in Python.
> Designed to run only on Ubuntu operating system.

This tool currently supports the following resources:
* service
* directory
* file 
* firewall

>A resource definition in SCM is directly related to the action of standard Linux commands, e.g., service, directories, files.

>Pre-requisites: Install Python 3.6 & above environment on the machine.

## Installation
```bash
sudo apt-get update
sudo apt-get install python3.8 python3-pip -y
mkdir -p /root/scm
cd /root/scm
pip3 install scm-config
scm -v 
```

## Usage
```bash
Usage: scm [OPTIONS] COMMAND [ARGS]...

Options:
  -v, --version                   Display's the application version
  --install-completion [bash|zsh|fish|powershell|pwsh]
                                  Install completion for the specified shell.
  --show-completion [bash|zsh|fish|powershell|pwsh]
                                  Show completion for the specified shell, to
                                  copy it or customize the installation.
  --help                          Show this message and exit.

Commands:
  create
  diff
  info
  init
  push
  remove
  validate
```

> SCM creates two directories in the root directory during the `init` command, for example `/root/scm`. One is for storing the recipe configuration and the other is for maintaining the configuration in the hash format. This mechanism allows SCM to run any number of times without worrying about failures.

## Example Workflow for Apache+PHP Configuration (After installation)

- `scm init`
- `scm create --recipe "apache"`
- Copy the contents from the [apache.toml](https://github.com/Sai-Repalle/scm_apache/blob/main/apache.toml) to `/root/scm/config/apache.toml`
- `scm validate --recipe "apache"`
- `scm diff --recipe "apache"`
- `scm push --recipe "apache"`

## Commands Overview 

| Command  | Description                                                                                                                      | Usage                                                               | Example                                           |
|----------|----------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------|---------------------------------------------------|
| `init`     | Initializes the tool, creating necessary files and directories for storing configuration.                                       | `scm init`                                                          |                                                   |
| `create`   | Creates the recipe `.toml` file in the config directory based on the recipe name.                                               | `scm create --recipe <name>`                                        | `scm create --recipe apache`                      |
| `validate` | Validates the recipe file configuration based on the standard defined resources.                                               | `scm validate --recipe <name>`                                      | `scm validate --recipe apache`                    |
| `info`     | Lists the configurations that are defined in the recipe file.                                                                  | `scm info --recipe <name>`                                          | `scm info --recipe apache`                        |
| `diff`     | Lists the differences between the existing and the current configuration. If this is a new recipe, outputs all the configurations. | `scm diff --recipe <name>`                                          | `scm diff --recipe apache`                        |
| `push`     | Pushes the configuration defined in the recipe file to the operating system and stores the configuration in the hash directory. | `scm push --recipe <name>`                                          | `scm push --recipe apache`                        |
| `remove`   | Removes the configuration from the hash directory and also removes the recipe file from the config directory.                  | `scm remove --recipe <name> [optional --force --clean-files]`       | `scm remove --recipe apache --force --clean-files`|

## Resource Detailed Information 

### Service 
The service resource is useful for installing and managing packages from the Linux repository.
> Note that this tool is currently designed to support only Ubuntu Operating System.

**Name parameter in the below section is a list format, meaning it can take multiple values and the actions and other parameters are applied to each name resource accordingly.**

#### Example 
```toml
[service.setup]
name = ["apache2"] 
action= ["install", "enable"]
```
In the above example:
* `name` -> Name of the service to be installed on the Ubuntu system.
* `action` -> Action to be done on the listed service. Currently supported actions: ["install", "enable", "disable"]

```toml
[service.ops]
name = ["apache2"]
action =["restart"]
```
In the above example, once the service is installed, service operations can be done using this tool.
* `name` -> Name of the service to be managed on the Ubuntu system.
* `action` -> Action to be done on the listed service. Currently supported actions: ["stop", "start", "restart", "reload", "disable", "enable"]

### Directory
The directory resource is useful for managing metadata directories on the system. 
> Note that this resource is currently tested only on Ubuntu Operating System but can run on any Linux Operating System.

#### Example 
```toml
[directory.list]
name = ["/etc/apache"] 
params = {'owner'='root','group'='root','mode'= '0755'}
action = ['create']
notifies = "@format {this.service.ops}"
```
In the above example:
* `name` -> Name of the directory where metadata needs modification, including creation using the action method.
* `params` -> Parameters to support directory operations. Currently supported: ['owner', 'group', 'mode'].
* `action` -> Action to be done on the listed directory. Currently supported: ['create'].
* `notifies` -> Parameter to notify any other resource in the same recipe file. In this example, it notifies the service ops resources, which would restart the apache2 service based on the modifications.

### File
The file resource is useful for managing metadata and content on the Linux file system.
> Note that this resource is currently tested only on Ubuntu Operating System but can run on any Linux Operating System.

#### Example 
```toml
[file.conf]
name = ["/var/www/customers/public_html/index.php"]
action = ["create"]
override = "true"
content  = ["This is the test file"]
params = {'owner'= 'root','group'= 'root','mode' = '0755'}
notifies = "@format {this.service.ops}"
```
In the above example:
* `name` -> Name of the file where content needs to be added or appended based on the configuration requirement.
* `action` -> Action to be done on the listed file. Currently supported: ['create'].
* `override` -> This parameter will override any existing file. By default, it will append the content to the file.
* `content` -> Input content for the file provided in double quotes.
* `params` -> Parameters to support file operations. Currently supported: ['owner', 'group', 'mode'].
* `notifies` -> Parameter to notify any other resource in the same recipe file. In this example, it notifies the service ops resources, which would restart the apache2 service based on the modifications.

### Firewall
The firewall resource is useful for managing firewall rules using UFW Linux command.
> Note that this resource is currently tested only on Ubuntu Operating System but can run on any Linux Operating System.

#### Example 
```toml
[firewall.setup]
name = ["Apache"]
action = ["allow"]
```
In the above example:
* `name` -> Name of the resource to allow firewall traffic.
* `action` -> Action to be done on the listed resource. Currently supported: ['allow'].

## Complete Overview of the Example File 

```toml
# Service setup for the apache instance 
[service.setup]
name = ["apache2"] 
action= ["install", "enable"]

# Service restart for the apache instance 
[service.ops]
name = ["apache2"]
action =["restart"]

[firewall.setup]
name = ["Apache"]
action=["allow"]

# Modify the directory permissions 
[directory.list]
name = ["/etc/apache"] 
params = {'owner'='root','group'='root','mode'= '0755'}
action = ['create']
notifies = "@format {this.service.ops}"

# Modify the input content of the file 
[file.conf]
name = ["/var/www/customers/public_html/index.php"]
action = ["create"]
content  = ["This is the test file"]
params = {'owner'= 'root','group'= 'root','mode' = '0755'}
notifies = "@format {this.service.ops}"
```

## Installation and Usage

### Manual Clone
```bash
git clone https://github.com/Sai-Repalle/scm_project
cd scm_project
python3 -m venv venv 
source venv/bin/activate
pip install -r requirements.txt 
```

### Initialization
`init` command is used for initialization and helps to create the respective directories. It is also useful for expanding future versions of the SCM tool.

#### Initialize the Tool
```bash
scm init
```

#### Output 
```bash   
scm init
[INFO][04-22-2022 06:08:13]::Reading the JSON configuration /root/scm/scm/settings/settings.json
[INFO][04-22-2022 06:08:13]::Creating directory CONFIG_DIR
[INFO][04-22-2022 06:08:13]::Creating directory CONFIG_HASH_DIR
[INFO][04-22-2022 06:08:13]::Creating files CONFIG_DEF_FILE
[INFO][04-22-2022 06:08:13]::Creating files CONFIG_HASH_FILE
```

### Create
`create <name>`
```bash
scm create --recipe <recipe>
```
Below example, will create a recipe called "apache" and `apache.toml` file is created in the config directory located at the root directory of the SCM.
#### Output 
```bash
scm create --recipe apache
[INFO][04-22-2022 06:09:56]::Reading the JSON configuration /root/scm/scm/settings/settings.json
[INFO][04-22-2022 06:09:56]::Creating directory CONFIG_DIR
[INFO][04-22-2022 06:09:56]::CONFIG_DIR directory already exists
[INFO][04-22-2022 06:09:56]::Creating directory CONFIG_HASH_DIR
[INFO][04-22-2022 06:09:56]::CONFIG_HASH_DIR directory already exists
[INFO][04-22-2022 06:09:56]::Creating files CONFIG_DEF_FILE
[INFO][04-22-2022 06:09:56]::Creating files CONFIG_HASH_FILE
```

### Info
`info --recipe <name>`
```bash
scm info --recipe <recipe>
```
Below example, info command is listing all the resources and its actions based on the configuration defined in the recipe file.
#### Output 
```bash
scm info --recipe apache
[INFO][04-25-2022 02:00:37]::Reading the JSON configuration /root/scm/settings.json
[INFO][04-25-2022 02:00:37]::Creating directory CONFIG_DIR
[INFO][04-25-2022 02:00:37]::CONFIG_DIR directory already exists
[INFO][04-25-2022 02:00:37]::Creating directory CONFIG_HASH_DIR
[INFO][04-25-2022 02:00:37]::CONFIG_HASH_DIR directory already exists
[INFO][04-25-2022 02:00:37]::Creating files CONFIG_DEF_FILE
[INFO][04-25-2022 02:00:37]::Creating files CONFIG_HASH_FILE
[INFO][04-25-2022 02:00:37]::SERVICE.setup - {'name': ['apache2'], 'action': ['install', 'enable', 'start']}
[INFO][04-25-2022 02:00:37]::SERVICE.ops - {'name': ['apache2'], 'action': ['restart']}
[INFO][04-25-2022 02:00:37]::SERVICE.setup_php - {'name': ['php', 'libapache2-mod-php'], 'action': ['install']}
[INFO][04-25-2022 02:00:37]::FIREWALL.setup - {'name': ['Apache'], 'action': ['allow']}
[INFO][04-25-2022 02:00:37]::FILE.conf - {'name': ['/var/www/html/index.php'], 'action': ['create'], 'override': 'true', 'content': ['<?php\n header("Content-Type: text/plain");\n echo "Hello, world!\n";\n'], 'params': {'owner': 'root', 'group': 'root', 'mode': '0755'}, 'notifies': "{'name': ['apache2'], 'action': ['restart']}"}
[INFO][04-25-2022 02:00:37]::FILE.phpindex - {'name': ['/etc/apache2/mods-enabled/dir.conf'], 'action': ['create'], 'override': 'true', 'content': ['<IfModule mod_dir.c>\n DirectoryIndex index.php index.html index.cgi index.pl index.xhtml index.htm </IfModule>'], 'params': {'owner': 'root', 'group': 'root', 'mode': '0755'}, 'notifies': "{'name': ['apache2'], 'action': ['restart']}"}
```

### Validate
`validate --recipe <name>`
```bash
scm validate --recipe <recipe>
```
Below example, validate command is validating all the resources and its actions based on the configuration defined in the recipe file. If all the resources and their configurations are in a valid state, the recipe would output to do the next step. If there are any issues, please refer to the documentation.
#### Output  
```bash
scm validate --recipe apache
[INFO][04-25-2022 02:01:47]::Reading the JSON configuration /root/scm/settings.json
[INFO][04-25-2022 02:01:47]::Creating directory CONFIG_DIR
[INFO][04-25-2022 02:01:47]::CONFIG_DIR directory already exists
[INFO][04-25-2022 02:01:47]::Creating directory CONFIG_HASH_DIR
[INFO][04-25-2022 02:01:47]::CONFIG_HASH_DIR directory already exists
[INFO][04-25-2022 02:01:47]::Creating files CONFIG_DEF_FILE
[INFO][04-25-2022 02:01:47]::Creating files CONFIG_HASH_FILE
[INFO][04-25-2022 02:01:47]::apache recipe file is valid for push, use `scm diff` to see differences with the existing configuration
```

### Diff
`diff --recipe <name>`
```bash
scm diff --recipe <recipe>
```
In the below example, if the configuration in the recipe file is already applied, SCM would output that the configuration is up to date with the existing configuration.
#### Output (Up-to-date)
```bash
scm diff --recipe apache
[INFO][04-25-2022 02:05:00]::Reading the JSON configuration /root/scm/settings.json
[INFO][04-25-2022 02:05:00]::Creating directory CONFIG_DIR
[INFO][04-25-2022 02:05:00]::Creating directory CONFIG_HASH_DIR
[INFO][04-25-2022 02:05:00]::Creating files CONFIG_DEF_FILE
[INFO][04-25-2022 02:05:00]::Creating files CONFIG_HASH_FILE
[INFO][04-25-2022 02:05:00]::apache recipe file is valid for push, use `scm diff` to see differences with the existing configuration
[INFO][04-25-2022 02:05:00]::Reading the JSON configuration config_hash/hash_config_md5.json
[INFO][04-25-2022 02:05:00]::`apache` configuration is up to date with the existing configuration
```

In the below example, if the configuration in the recipe file is pushed to the operating system to install the required services.
#### Output (Changes Required)
```bash
scm diff --recipe apache_remove
[INFO][04-25-2022 02:20:37]::Reading the JSON configuration /root/scm/settings.json
[INFO][04-25-2022 02:20:37]::Creating directory CONFIG_DIR
[INFO][04-25-2022 02:20:37]::Creating directory CONFIG_HASH_DIR
[INFO][04-25-2022 02:20:37]::Creating files CONFIG_DEF_FILE
[INFO][04-25-2022 02:20:37]::apache_remove recipe file is valid for push, use `scm diff` to see differences with the existing configuration
[INFO][04-25-2022 02:20:37]::Reading the JSON configuration config_hash/hash_config_md5.json
[INFO][04-25-2022 02:20:37]::Following resources will be applied:
[INFO][04-25-2022 02:20:37]::SERVICE.setup: ['systemctl stop apache2', 'systemctl disable apache2', 'sudo apt-get update -y', 'sudo apt-get remove apache2 -y']
[INFO][04-25-2022 02:20:37]::SERVICE.setup_php: ['sudo apt-get update -y', 'sudo apt-get remove php -y', 'sudo apt-get update -y', 'sudo apt-get remove libapache2-mod-php -y']
```

### Push
`push --recipe <name>`
```bash
scm push --recipe <recipe>
```
In the below example, `scm push` is pushing the recipe named `apache_remove` and the subsequent commands are being run on the operating system to remove the services.
#### Output
```bash
scm push --recipe apache_remove
[INFO][04-25-2022 02:21:34]::Reading the JSON configuration /root/scm/settings.json
[INFO][04-25-2022 02:21:34]::Creating directory CONFIG_DIR
[INFO][04-25-2022 02:21:34]::Creating directory CONFIG_HASH_DIR
[INFO][04-25-2022 02:21:34]::Creating files CONFIG_DEF_FILE
[INFO][04-25-2022 02:21:34]::apache_remove recipe file is valid for push, use `scm diff` to see differences with the existing configuration
[INFO][04-25-2022 02:21:34]::Reading the JSON configuration config_hash/hash_config_md5.json
[INFO][04-25-2022 02:21
