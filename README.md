# Remote Dev Environment Manager
Code to setup a Linux server with ssh key Auth, install required packages, aliases, VS Code + Extensions and provide a quick way to manage new scripts and projects with Docker, Nginx and Traefic for SSL.

## Usage Examples

### Project Creation
#### Interactive mode
```bash
dev new
```

#### Direct command with versions

```bash
dev new -t python-fastapi -n myapi --versions python:3.11
```

#### Laravel with specific PHP version

```bash
dev new -t laravel -n myblog -d myblog.co.uk --versions php:8.2,mysql:8.0
```

#### Nuxt project with specific Node version

```bash
dev new -t nuxt -n frontend --versions node:18
```

#### WordPress site

```bash
dev new -t wordpress -n mysite -d mysite.co.uk --versions php:8.2,wordpress:6.4
```

## Version Management
### Interactive version management
```bash
dev versions
```

### Check what versions are being used
```bash
dev list
```

### Update to latest versions
```bash
dev versions  # Then choose "Check latest versions"Dotfiles Management# Sync dotfiles from your GitHub repo
dev dotfiles sync
```

### Install dotfiles configuration
```bash
dev dotfiles install
```

### Push local changes
```bash
dev dotfiles  # Then choose push optionProject Management# List all projects
dev list
```

### Start a project
```bash
dev start myapi
```

### Stop a project
```bash
dev stop myapi
```

### Interactive management
```bash
dev
```
