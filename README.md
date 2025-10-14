# SCM Platform - Enterprise Configuration Management & Orchestration

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/sairepalletech/scm_project/releases)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)

## Overview

**SCM Platform** is evolving from a simple configuration management tool into an **enterprise-ready orchestration platform** that integrates with 100+ external systems across SCM, CI/CD, cloud, security, observability, and ITSM domains.

### Vision

Transform scm_project into a scalable, secure, extensible platform—similar to Ansible or Chef—that orchestrates and reconciles state across infrastructure and tooling through a declarative workflow DSL and modular plugin system.

### Current State (v1.0.0)

A lightweight Python CLI tool for configuration management on Ubuntu:
- **Resources**: service, directory, file, firewall
- **Format**: TOML-based recipes
- **Execution**: Local command execution
- **Focus**: Ubuntu operating system

### Future State (v2.0+)

An enterprise platform with:
- 🔌 **100+ Integrations** via plugin system (GitHub, GitLab, AWS, Azure, Jenkins, etc.)
- 🎯 **Declarative Workflows** in YAML with idempotent operations
- 🏗️ **Control Plane + Runners** architecture for distributed execution
- 🔐 **Enterprise Security** (OIDC/SAML SSO, RBAC, secrets management, signed artifacts)
- 📊 **Full Observability** (metrics, tracing, audit logs)
- ☸️ **Cloud-Native** deployment on Kubernetes with HA
- 🌍 **Multi-Tenancy** with organization/project isolation
- 📜 **Policy Engine** (OPA) for compliance and governance

## Quick Start (v1.0.0 - Current)

### Prerequisites
- Python 3.6 or higher
- Ubuntu operating system

# Installation
```bash
sudo apt-get update
sudo apt-get install python3.8 python3-pip -y
mkdir -p /root/scm
cd /root/scm
pip3 install scm-config
scm -v 
```
# CLI Reference (v1.0.0)

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
  create    Create a new recipe configuration file
  diff      Show differences between current and desired state
  info      Display recipe information
  init      Initialize SCM configuration directories
  push      Apply recipe configuration to the system
  remove    Remove recipe and its configuration
  validate  Validate recipe syntax and configuration
```

### How It Works

SCM creates two directories during initialization (e.g., `/root/scm`):
1. **config/** - Stores recipe TOML files
2. **config_hash/** - Maintains configuration hashes for idempotency

This mechanism ensures SCM can run multiple times safely without failures or duplicate operations.

## Example workflow for Apache+PHP configuration(After the installation)

- scm init 
- scm create --recipe "apache"
- Copy the contents from the [apache.toml](https://github.com/Sai-Repalle/scm_apache/blob/main/apache.toml) to root/scm/config/apache.toml 
- scm validate --recipe "apache"
- scm diff --recipe "apache" 
- scm push --recipe "apache"


# Commands overview 

| command  | command description                                                                                                                      | usage                                                               | Example                                           |   |
|----------|------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------|---------------------------------------------------|---|
| init     | Used for initialization, creates necessary files and directories for the tool to store configuration.                                                                        | scm init                                                            |                                                   |   |
| create   | Creates the recipe .toml file in the config directory based on the recipe name                                                         | scm create --recipe <name>                                         | scm create --recipe apache                       |   |
| validate | Validates the recipe file configuration based on the standard defined resources                                                         | scm validate --recipe <name>                                       | scm validate --recipe apache                     |   |
| info     | Lists the configurations that are defined in the recipe file                                                                            | scm info --recipe <name>                                           | scm info --recipe apache                         |   |
| diff     | Lists the differences between the existing and the current configuration, if this is this is new recipe, outputs all the configurations | scm diff --recipe <name>                                           | scm diff --recipe apache                         |   |
| push     | Pushes the configuration defined in the recipe file to the operating system and stores the configuration in config_hash_directory       | scm push --recipe <name>                                           | scm push --recipe apache                         |   |
| remove   | Removes the configuration from the hash directory and also removes the recipe file from the config directory                            | scm push --recipe <name> [optional --force [optional --clean-files | scm remove --recipe apache --force --clean-files |   |


# Resource Detailed information 
## Service 
Service resource is useful for installing and managing packages from the linux repository, 
> Note that currently this tool is designed to support only on Ubuntu Operating System

***Name parameter in the below section is a list format, meaning it can take multiple values and the actions and other parameters are applied to each name resource accordingly**
### Example 
```
[service.setup]
name = ["apache2"] 
action= ["install", "enable"]
```
In the above example, "service" is the resource and "setup" is the service identifier. 
* name  -> Name of the service that is to be installed on the ubuntu system 
* action -> Action to be done on the listed service, currently these are only supported 
> ["install", "enable", "disable"]

```
[service.ops]
name = ["apache2"]
action =["restart"]
```
In the above example, "service" is the resource and "ops" is the service identifier. once the service is installed and service operations can be done using this tool. 
* name  -> Name of the service that is to be installed on the ubuntu system 
* action -> Action to be done on the listed service, currently these are only supported 
> ["stop", "start", "restart", "reload", "disable", "enable"]

## Directory
Directory resource is useful for installing and managing the metadata directories on the system, 
> Note that currently this resource is tested only on Ubuntu Operating System, but can run on any Linux Operating System

### Example 
```
# Modify the directory permissions 
[directory.list]
name = ["/etc/apache"] 
params = {'owner'='root','group'='root','mode'= '0755'}
action = ['create']
notifies = "@format {this.service.ops}"
```
In the above example, "directory" is the resource and "list" is the service identifier. 
* name  -> Name of the directory where the metadata needs modification including creation of the directory using the action method
* params -> parameter to support the directory operations, currently ['owner', 'group' and 'mode'] are supported in the list 
* action -> Action to be done on the listed service, currently for directories only ['create'] is supported
* notifies -> Parameter to notify any other resource in the same recipe file, In example, notifies the service ops resources, that would restart the apache2 service based on the modifications 
> ["install", "enable", "disable"]

## File
File resource is useful for managing the metadata and the content on the linux file system, 
> Note that currently this resource is tested only on Ubuntu Operating System, but can run on any Linux Operating System

### Example 
```
# Modify the input content of the file 
[file.conf]
name = ["/var/www/customers/public_html/index.php"]
action = ["create"]
override ="true"
content  = ["This is the test file"]
params = {'owner'= 'root','group'= 'root','mode' = '0755'}
notifies = "@format {this.service.ops}"

```
In the above example, "file" is the resource and "conf" is the service identifier. 
* name  -> Name of the file where the content need to be added or appended based on the configuration requirement
* action -> Action to be done on the listed service, currently for file only ['create'] is supported
* override -> This parameter will override if there is any existing file, default it will append the content to the file 
* content -> Input content for the file provide in the form the double quotes. For simplicity ,large content is not tested with the current version of the code. 
* params -> parameter to support the file operations, currently ['owner', 'group' and 'mode'] are supported in the list 
* notifies -> Parameter to notify any other resource in the same recipe file, In example, notifies the service ops resources, that would restart the apache2 service based on the modifications 
> ["install", "enable", "disable"]


## Firewall
Firewall resource is useful for managing firewall rules using UFW linux command, 
> Note that currently this resource is tested only on Ubuntu Operating System, but can run on any Linux Operating System

### Example 
```
# Modify the input content of the file 
[firewall.setup]
name = ["Apache"]
action=["allow"]
```

In the above example, "firewall" is the resource and "setup" is the service identifier. 
* name  -> Name of the resource where need to allow firewall traffic
* action -> Action to be done on the listed service, currently for file only ['allow'] is supported 
> ["allow"]


# Complete overview of the example file 

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
# Installation and Usage # 

## Manual clone
```bash
  $ git clone https://github.com/Sai-Repalle/scm_project
  $ cd scm_project
  $ python3 -m venv venv 
  $ source venv/bin/activate
  $ pip install -r requirements.txt 
```

## initialization
init command is used for initialization and helpful to create the respective directories, also this command is useful for expanding future versions of the scm tool

`init`
Initialize the tool without any parameters, this would set the configuration files required for tool to work
```bash
$ scm init
```
### output 
```bash   
scm init
[INFO][04-22-2022 06:08:13]::Reading the Json configuration /root/scm/scm/settings/settings.json
[INFO][04-22-2022 06:08:13]::creating directory CONFIG_DIR
[INFO][04-22-2022 06:08:13]::creating directory CONFIG_HASH_DIR
[INFO][04-22-2022 06:08:13]::creating files CONFIG_DEF_FILE
[INFO][04-22-2022 06:08:13]::creating files CONFIG_HASH_FILE

```
## create
`create <name>`
```bash
$ scm create --recipe <recipe>
```
Below example, will create a recipe called "apache" and `apache.toml` file is created in the config directory located at the root directory of the scm 
### output 
```bash
scm create --recipe apache
[INFO][04-22-2022 06:09:56]::Reading the Json configuration /root/scm/scm/settings/settings.json
[INFO][04-22-2022 06:09:56]::creating directory CONFIG_DIR
[INFO][04-22-2022 06:09:56]::CONFIG_DIR directory already exists
[INFO][04-22-2022 06:09:56]::creating directory CONFIG_HASH_DIR
[INFO][04-22-2022 06:09:56]::CONFIG_HASH_DIR directory already exists
[INFO][04-22-2022 06:09:56]::creating files CONFIG_DEF_FILE
[INFO][04-22-2022 06:09:56]::creating files CONFIG_HASH_FIL
```


## info
`info --recipe <name>`
```bash
$ scm info --recipe <recipe>
```
Below example, info command is listing all the resources and its actions based on the configuration defined in the recipe file.
### output 
```bash
scm info --recipe apache
[INFO][04-25-2022 02:00:37]::Reading the Json configuration /root/scm/settings.json
[INFO][04-25-2022 02:00:37]::creating directory CONFIG_DIR
[INFO][04-25-2022 02:00:37]::CONFIG_DIR directory already exists
[INFO][04-25-2022 02:00:37]::creating directory CONFIG_HASH_DIR
[INFO][04-25-2022 02:00:37]::CONFIG_HASH_DIR directory already exists
[INFO][04-25-2022 02:00:37]::creating files CONFIG_DEF_FILE
[INFO][04-25-2022 02:00:37]::creating files CONFIG_HASH_FILE
[INFO][04-25-2022 02:00:37]::SERVICE.setup - {'name': ['apache2'], 'action': ['install', 'enable', 'start']}
[INFO][04-25-2022 02:00:37]::SERVICE.ops - {'name': ['apache2'], 'action': ['restart']}
[INFO][04-25-2022 02:00:37]::SERVICE.setup_php - {'name': ['php', 'libapache2-mod-php'], 'action': ['install']}
[INFO][04-25-2022 02:00:37]::FIREWALL.setup - {'name': ['Apache'], 'action': ['allow']}
[INFO][04-25-2022 02:00:37]::FILE.conf - {'name': ['/var/www/html/index.php'], 'action': ['create'], 'override': 'true', 'content': ['<?php\n header("Content-Type: text/plain");\n echo "Hello, world!\n";\n'], 'params': {'owner': 'root', 'group': 'root', 'mode': '0755'}, 'notifies': "{'name': ['apache2'], 'action': ['restart']}"}
[INFO][04-25-2022 02:00:37]::FILE.phpindex - {'name': ['/etc/apache2/mods-enabled/dir.conf'], 'action': ['create'], 'override': 'true', 'content': ['<IfModule mod_dir.c>\n DirectoryIndex index.php index.html index.cgi index.pl index.xhtml index.htm </IfModule>'], 'params': {'owner': 'root', 'group': 'root', 'mode': '0755'}, 'notifies': "{'name': ['apache2'], 'action': ['restart']}"}
```

## validate
`validate -recipe <name>`
```bash
$ scm validate --recipe <recipe>
```
Below example, validate command is validating all the resources and its actions based on the configuration defined in the recipe file, If all the resources and its configurations are in valid state, recipe would output to do next step, if there are any issues, please refere to the documentation.
### output  
```bash
scm validate --recipe apache
[INFO][04-25-2022 02:01:47]::Reading the Json configuration /root/scm/settings.json
[INFO][04-25-2022 02:01:47]::creating directory CONFIG_DIR
[INFO][04-25-2022 02:01:47]::CONFIG_DIR directory already exists
[INFO][04-25-2022 02:01:47]::creating directory CONFIG_HASH_DIR
[INFO][04-25-2022 02:01:47]::CONFIG_HASH_DIR directory already exists
[INFO][04-25-2022 02:01:47]::creating files CONFIG_DEF_FILE
[INFO][04-25-2022 02:01:47]::creating files CONFIG_HASH_FILE
[INFO][04-25-2022 02:01:47]::apache recipe file is valid for push, use `scm diff` to differences with the existing configuration
```

## diff
`diff -recipe <name>`
```bash
$ scm diff --recipe <recipe>
```
In the below example, if the confiugration in the recipe file is already appplied, scm would output that the configuration is update to date with the existing configuration 
```bash
[INFO][04-25-2022 02:05:00]::Reading the Json configuration /root/scm/settings.json
[INFO][04-25-2022 02:05:00]::Reading the Json configuration /root/scm/settings.json
[INFO][04-25-2022 02:05:00]::creating directory CONFIG_DIR
[INFO][04-25-2022 02:05:00]::CONFIG_DIR directory already exists
[INFO][04-25-2022 02:05:00]::creating directory CONFIG_HASH_DIR
[INFO][04-25-2022 02:05:00]::CONFIG_HASH_DIR directory already exists
[INFO][04-25-2022 02:05:00]::creating files CONFIG_DEF_FILE
[INFO][04-25-2022 02:05:00]::creating files CONFIG_HASH_FILE
[INFO][04-25-2022 02:05:00]::apache recipe file is valid for push, use `scm diff` to differences with the existing configuration
[INFO][04-25-2022 02:05:00]::Reading the Json configuration config_hash/hash_config_md5.json
[INFO][04-25-2022 02:05:00]::`apache` configuration is update to date with the existing configuration
```
In the below example, if the configuration in the recipe file is pushed to the operating system to install the required services 
```bash
root@ip-172-31-255-140:~/scm/config# scm diff --recipe apache_remove
[INFO][04-25-2022 02:20:37]::Reading the Json configuration /root/scm/config/settings.json
[INFO][04-25-2022 02:20:37]::Reading the Json configuration /root/scm/config/settings.json
[INFO][04-25-2022 02:20:37]::creating directory CONFIG_DIR
[INFO][04-25-2022 02:20:37]::CONFIG_DIR directory already exists
[INFO][04-25-2022 02:20:37]::creating directory CONFIG_HASH_DIR
[INFO][04-25-2022 02:20:37]::CONFIG_HASH_DIR directory already exists
[INFO][04-25-2022 02:20:37]::creating files CONFIG_DEF_FILE
[INFO][04-25-2022 02:20:37]::CONFIG_DEF_FILE file already exists
[INFO][04-25-2022 02:20:37]::creating files CONFIG_HASH_FILE
[INFO][04-25-2022 02:20:37]::apache_remove recipe file is valid for push, use `scm diff` to differences with the existing configuration
[INFO][04-25-2022 02:20:37]::Reading the Json configuration config_hash/hash_config_md5.json
[INFO][04-25-2022 02:20:37]::Following resources will be applied:
[INFO][04-25-2022 02:20:37]::SERVICE.setup: ['systemctl stop apache2', 'systemctl disable apache2', 'sudo apt-get update -y', 'sudo apt-get remove apache2 -y']
[INFO][04-25-2022 02:20:37]::Following resources will be applied:
[INFO][04-25-2022 02:20:37]::SERVICE.setup_php: ['sudo apt-get update -y', 'sudo apt-get remove php -y', 'sudo apt-get update -y', 'sudo apt-get remove libapache2-mod-php -y']
```
## push
`push -recipe <name>`
```bash
$ scm push --recipe <recipe>
```
In the below example, scm push is pushing hte recipe named "apache_remove" and the subsequent commands are being run on the operating to the remove the services 
### output
```bash
root@ip-172-31-255-140:~/scm/config# scm push  --recipe apache_remove
[INFO][04-25-2022 02:21:34]::Reading the Json configuration /root/scm/config/settings.json
[INFO][04-25-2022 02:21:34]::Reading the Json configuration /root/scm/config/settings.json
[INFO][04-25-2022 02:21:34]::creating directory CONFIG_DIR
[INFO][04-25-2022 02:21:34]::CONFIG_DIR directory already exists
[INFO][04-25-2022 02:21:34]::creating directory CONFIG_HASH_DIR
[INFO][04-25-2022 02:21:34]::CONFIG_HASH_DIR directory already exists
[INFO][04-25-2022 02:21:34]::creating files CONFIG_DEF_FILE
[INFO][04-25-2022 02:21:34]::CONFIG_DEF_FILE file already exists
[INFO][04-25-2022 02:21:34]::creating files CONFIG_HASH_FILE
[INFO][04-25-2022 02:21:34]::apache_remove recipe file is valid for push, use `scm diff` to differences with the existing configuration
[INFO][04-25-2022 02:21:34]::Reading the Json configuration config_hash/hash_config_md5.json
[INFO][04-25-2022 02:21:34]::Reading the Json configuration /root/scm/config/settings.json
[INFO][04-25-2022 02:21:34]::Following resources will be applied:
[INFO][04-25-2022 02:21:34]::SERVICE.setup: ['systemctl stop apache2', 'systemctl disable apache2', 'sudo apt-get update -y', 'sudo apt-get remove apache2 -y']
[INFO][04-25-2022 02:21:34]::Applying the command `systemctl stop apache2`
[INFO][04-25-2022 02:21:35]::Applying the command `systemctl disable apache2`
Synchronizing state of apache2.service with SysV service script with /lib/systemd/systemd-sysv-install.
Executing: /lib/systemd/systemd-sysv-install disable apache2
[INFO][04-25-2022 02:21:35]::Applying the command `sudo apt-get update -y`
Hit:1 http://us-east-1.ec2.archive.ubuntu.com/ubuntu bionic InRelease
Get:2 http://us-east-1.ec2.archive.ubuntu.com/ubuntu bionic-updates InRelease [88.7 kB]
Get:3 http://us-east-1.ec2.archive.ubuntu.com/ubuntu bionic-backports InRelease [74.6 kB]
Get:4 http://security.ubuntu.com/ubuntu bionic-security InRelease [88.7 kB]
Fetched 252 kB in 0s (666 kB/s)
Reading package lists... Done
[INFO][04-25-2022 02:21:42]::Applying the command `sudo apt-get remove apache2 -y`
Reading package lists... Done
Building dependency tree
Reading state information... Done
The following packages were automatically installed and are no longer required:
  apache2-data apache2-utils ssl-cert
Use 'sudo apt autoremove' to remove them.
The following packages will be REMOVED:
  apache2
0 upgraded, 0 newly installed, 1 to remove and 2 not upgraded.
After this operation, 537 kB disk space will be freed.
(Reading database ... 94525 files and directories currently installed.)
Removing apache2 (2.4.29-1ubuntu4.22) ...
Processing triggers for man-db (2.8.3-2ubuntu0.1) ...
Processing triggers for ufw (0.36-0ubuntu0.18.04.2) ...
Rules updated for profile 'Apache'

```

## remove
`remove --recipe <name> --force <optional> --clean_files <optional>`
```bash
$ scm push --recipe <recipe>
```
In the below example, scm is removing the `apache_remove` recipe from the configuration hash directory,
### output 
```bash
scm remove --recipe apache_remove
[INFO][04-25-2022 02:33:38]::Reading the Json configuration /root/scm/config/settings.json
[INFO][04-25-2022 02:33:38]::Reading the Json configuration /root/scm/config/settings.json
[INFO][04-25-2022 02:33:38]::creating directory CONFIG_DIR
[INFO][04-25-2022 02:33:38]::CONFIG_DIR directory already exists
[INFO][04-25-2022 02:33:38]::creating directory CONFIG_HASH_DIR
[INFO][04-25-2022 02:33:38]::CONFIG_HASH_DIR directory already exists
[INFO][04-25-2022 02:33:38]::creating files CONFIG_DEF_FILE
[INFO][04-25-2022 02:33:38]::CONFIG_DEF_FILE file already exists
[INFO][04-25-2022 02:33:38]::creating files CONFIG_HASH_FILE
[INFO][04-25-2022 02:33:38]::apache_remove recipe file is valid for push, use `scm diff` to differences with the existing configuration
[INFO][04-25-2022 02:33:38]::Configuration doesn't remove the recipe file, please clean up manually
```

---

## 🚀 Enterprise Transformation (v2.0+)

SCM Platform is evolving into an enterprise-ready orchestration platform. This transformation is guided by comprehensive documentation and a phased roadmap.

### 📚 Documentation

Explore the complete enterprise architecture and implementation plans:

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Enterprise architecture, reference design, security model, and deployment patterns
- **[ROADMAP.md](ROADMAP.md)** - 4-quarter implementation plan with milestones and deliverables
- **[docs/plugins/PLUGIN_SYSTEM.md](docs/plugins/PLUGIN_SYSTEM.md)** - Plugin architecture, SPI specification, and developer guide
- **[docs/architecture/WORKFLOW_DSL.md](docs/architecture/WORKFLOW_DSL.md)** - Declarative workflow DSL specification and examples
- **[docs/deployment/KUBERNETES.md](docs/deployment/KUBERNETES.md)** - Production Kubernetes deployment guide

### 🎯 Key Features (Planned)

#### Plugin System
- **100+ Integrations** across SCM, CI/CD, cloud, security, and observability
- **OCI-packaged plugins** with signing and SBOM
- **Multiple isolation modes**: gRPC (out-of-process) and WASM (sandbox)
- **Go/Python/Node.js SDKs** for plugin development
- **Verification program** with conformance testing

#### Workflow DSL
```yaml
apiVersion: workflows.scm.dev/v1
kind: Workflow
metadata:
  name: bootstrap-organization
spec:
  triggers:
    - type: webhook
      source: github
      events: [repository.created]
  
  steps:
    - name: create-repos
      uses: github.repos:create
      with:
        org: ${{ inputs.org_name }}
        repos:
          - name: platform-api
            visibility: private
    
    - name: setup-protection
      uses: github.repos:branch_protection
      with:
        org: ${{ inputs.org_name }}
        repo: platform-api
        rules:
          require_reviews: 2
```

#### Enterprise Features
- **Control Plane + Runners** architecture for distributed execution
- **Multi-tenancy** with organization/project/environment hierarchy
- **OIDC/SAML SSO** authentication
- **RBAC/ABAC** authorization with fine-grained permissions
- **Policy engine** (OPA) for compliance and governance
- **Secrets management** via Vault/AWS/Azure/GCP
- **Full observability** with metrics, tracing, and audit logs
- **High availability** with multi-AZ Kubernetes deployment

#### Developer Experience
```bash
# Initialize new plugin
scm plugin init github --type connector --lang go

# Test plugin
scm plugin test --manifest manifest.yaml

# Publish to registry
scm plugin publish ghcr.io/org/github:v1.0.0

# Validate workflow
scm workflow validate my-workflow.yaml

# Preview changes (dry-run)
scm workflow plan my-workflow.yaml --input org=acme
```

### 📅 Implementation Timeline

| Quarter | Version | Focus | Integrations |
|---------|---------|-------|--------------|
| **Q1** | v2.0.0 | Foundations - Core platform + plugin system MVP | 5 |
| **Q2** | v2.1.0 | Scale - Performance + developer experience | 15 |
| **Q3** | v2.2.0 | Enterprise - Multi-tenancy + security | 35 |
| **Q4** | v3.0.0 | Ecosystem - Marketplace + community | 50+ |

### 🏗️ Current Focus (Q1)

Phase 1 establishes the foundation:
- [x] Architecture documentation (ARCHITECTURE.md)
- [x] Roadmap planning (ROADMAP.md)
- [x] Plugin system design (PLUGIN_SYSTEM.md)
- [x] Workflow DSL specification (WORKFLOW_DSL.md)
- [x] Deployment guides (KUBERNETES.md)
- [ ] Core API implementation (REST + gRPC)
- [ ] Orchestrator and scheduler
- [ ] Plugin SDK (Go)
- [ ] First 5 integrations (GitHub, GitLab, Slack, Service, File)

### 🤝 Contributing

We welcome contributions to this transformation:
- **Architecture feedback**: Review design documents and provide input
- **Plugin development**: Build integrations using the plugin SDK
- **Documentation**: Improve guides and examples
- **Testing**: Help with conformance tests and benchmarks

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines (coming soon).

### 📖 Migration Path

**Backward Compatibility**: The current v1.0.0 TOML-based recipes will continue to work. We'll provide:
- Compatibility bridge for existing recipes
- Migration tools from TOML to new YAML DSL
- Long-term support for v1.0.0 format
- Gradual migration guides

### 🔗 Resources

- **Documentation**: [docs/](docs/)
- **Architecture Diagrams**: [ARCHITECTURE.md](ARCHITECTURE.md)
- **Plugin Examples**: [examples/](examples/) (coming soon)
- **Community**: GitHub Discussions (coming soon)

### 📊 Project Status

**Current Release**: v1.0.0 (Stable - Configuration Management CLI)
**Next Release**: v2.0.0 (Planned - Enterprise Platform Foundation)
**Maturity**: Early planning and design phase
**License**: MIT

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with Python, Typer, and Dynaconf
- Inspired by Ansible, Chef, and Kubernetes ecosystem
- Community feedback and contributions