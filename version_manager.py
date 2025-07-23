#!/usr/bin/env python3

import os
import json
import yaml
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.progress import Progress, SpinnerColumn, TextColumn
import requests

console = Console()

class VersionManager:
    def __init__(self):
        self.config_dir = Path.home() / 'config' / 'versions'
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / 'versions.yml'
        self.load_config()
        
    def load_config(self):
        """Load version configuration"""
        if self.config_file.exists():
            with open(self.config_file) as f:
                self.config = yaml.safe_load(f) or {}
        else:
            self.config = self.get_default_config()
            self.save_config()
    
    def save_config(self):
        """Save version configuration"""
        with open(self.config_file, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)
    
    def get_default_config(self) -> Dict:
        """Get default version configuration"""
        return {
            'tools': {
                'php': {
                    'default': '8.2',
                    'available': ['7.4', '8.0', '8.1', '8.2', '8.3'],
                    'docker_image': 'php:{version}-fpm',
                    'extensions': [
                        'mysqli', 'pdo_mysql', 'mbstring', 'xml', 'curl',
                        'zip', 'gd', 'bcmath', 'intl', 'opcache'
                    ]
                },
                'node': {
                    'default': '18',
                    'available': ['16', '18', '20', 'latest'],
                    'docker_image': 'node:{version}-alpine',
                    'global_packages': [
                        'typescript', 'nodemon', 'pm2', 'eslint', 'prettier'
                    ]
                },
                'python': {
                    'default': '3.11',
                    'available': ['3.8', '3.9', '3.10', '3.11', '3.12'],
                    'docker_image': 'python:{version}-slim',
                    'packages': [
                        'fastapi', 'uvicorn', 'requests', 'pytest', 'black', 'flake8'
                    ]
                },
                'wordpress': {
                    'default': '6.4',
                    'available': ['6.2', '6.3', '6.4', 'latest'],
                    'docker_image': 'wordpress:{version}',
                    'php_version': '8.2'
                },
                'laravel': {
                    'default': '10',
                    'available': ['9', '10', '11'],
                    'installer': 'composer create-project laravel/laravel:{version}',
                    'php_version': '8.1'
                },
                'vue': {
                    'default': '3',
                    'available': ['2', '3'],
                    'installer': 'npm create vue@{version}',
                    'node_version': '18'
                },
                'nuxt': {
                    'default': '3',
                    'available': ['2', '3'],
                    'installer': 'npx nuxi@{version} init',
                    'node_version': '18'
                }
            },
            'preferences': {
                'auto_update': True,
                'check_latest': True,
                'cache_duration': 24  # hours
            }
        }
    
    def get_available_versions(self, tool: str) -> List[str]:
        """Get available versions for a tool"""
        return self.config['tools'].get(tool, {}).get('available', [])
    
    def get_default_version(self, tool: str) -> str:
        """Get default version for a tool"""
        return self.config['tools'].get(tool, {}).get('default', 'latest')
    
    def set_default_version(self, tool: str, version: str):
        """Set default version for a tool"""
        if tool in self.config['tools']:
            self.config['tools'][tool]['default'] = version
            self.save_config()
            console.print(f"[green]Set {tool} default version to {version}[/green]")
        else:
            console.print(f"[red]Unknown tool: {tool}[/red]")
    
    def check_latest_versions(self) -> Dict[str, str]:
        """Check latest versions from official sources"""
        latest_versions = {}
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Checking latest versions...", total=None)
            
            # Check PHP versions
            try:
                php_versions = self._get_php_versions()
                if php_versions:
                    latest_versions['php'] = php_versions[0]
            except:
                pass
            
            # Check Node.js versions
            try:
                node_versions = self._get_node_versions()
                if node_versions:
                    latest_versions['node'] = node_versions[0]
            except:
                pass
            
            # Check Python versions
            try:
                python_versions = self._get_python_versions()
                if python_versions:
                    latest_versions['python'] = python_versions[0]
            except:
                pass
            
            # Check WordPress versions
            try:
                wp_version = self._get_wordpress_version()
                if wp_version:
                    latest_versions['wordpress'] = wp_version
            except:
                pass
            
            progress.update(task, description="✅ Version check complete")
        
        return latest_versions
    
    def _get_php_versions(self) -> List[str]:
        """Get latest PHP versions from Docker Hub"""
        try:
            response = requests.get('https://registry.hub.docker.com/v2/repositories/library/php/tags?page_size=100')
            data = response.json()
            
            versions = []
            for tag in data.get('results', []):
                name = tag['name']
                if '-fpm' in name and '.' in name:
                    version = name.split('-')[0]
                    if version.replace('.', '').isdigit() and version.count('.') == 1:
                        versions.append(version)
            
            # Sort versions
            versions = sorted(set(versions), key=lambda x: tuple(map(int, x.split('.'))), reverse=True)
            return versions[:10]  # Return top 10
        except:
            return []
    
    def _get_node_versions(self) -> List[str]:
        """Get latest Node.js versions"""
        try:
            response = requests.get('https://nodejs.org/dist/index.json')
            data = response.json()
            
            versions = []
            for release in data[:20]:  # Get latest 20 releases
                version = release['version'].lstrip('v')
                major_version = version.split('.')[0]
                if major_version not in [v.split('.')[0] for v in versions]:
                    versions.append(major_version)
            
            return versions
        except:
            return []
    
    def _get_python_versions(self) -> List[str]:
        """Get latest Python versions"""
        try:
            response = requests.get('https://api.github.com/repos/python/cpython/tags')
            data = response.json()
            
            versions = []
            for tag in data:
                name = tag['name']
                if name.startswith('v3.') and name.count('.') == 2:
                    version = name[1:4]  # Extract 3.x part
                    if version not in versions:
                        versions.append(version)
            
            return sorted(set(versions), key=lambda x: tuple(map(int, x.split('.'))), reverse=True)[:10]
        except:
            return []
    
    def _get_wordpress_version(self) -> str:
        """Get latest WordPress version"""
        try:
            response = requests.get('https://api.wordpress.org/core/version-check/1.7/')
            data = response.json()
            return data['offers'][0]['version']
        except:
            return None
    
    def generate_dockerfile(self, tool: str, version: str, base_path: Path) -> str:
        """Generate Dockerfile for specific tool version"""
        tool_config = self.config['tools'].get(tool, {})
        
        if tool == 'php':
            return self._generate_php_dockerfile(version, tool_config)
        elif tool == 'node':
            return self._generate_node_dockerfile(version, tool_config)
        elif tool == 'python':
            return self._generate_python_dockerfile(version, tool_config)
        elif tool == 'wordpress':
            return self._generate_wordpress_dockerfile(version, tool_config)
        else:
            return ""
    
    def _generate_php_dockerfile(self, version: str, config: Dict) -> str:
        """Generate PHP Dockerfile"""
        image = config.get('docker_image', 'php:{version}-fpm').format(version=version)
        extensions = ' '.join(config.get('extensions', []))
        
        return f"""FROM {image}

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    git \\
    curl \\
    libpng-dev \\
    libonig-dev \\
    libxml2-dev \\
    zip \\
    unzip \\
    libzip-dev \\
    libicu-dev \\
    && rm -rf /var/lib/apt/lists/*

# Install PHP extensions
RUN docker-php-ext-configure gd --with-freetype --with-jpeg \\
    && docker-php-ext-install -j$(nproc) {extensions}

# Install Composer
COPY --from=composer:latest /usr/bin/composer /usr/bin/composer

# Install code-server
RUN curl -fsSL https://code-server.dev/install.sh | sh

# Install PHP VS Code extensions
RUN code-server --install-extension bmewburn.vscode-intelephense-client \\
    --install-extension xdebug.php-debug \\
    --install-extension recca0120.vscode-phpunit

# Set working directory
WORKDIR /workspace

# Configure PHP
RUN echo "upload_max_filesize = 100M" >> /usr/local/etc/php/conf.d/uploads.ini \\
    && echo "post_max_size = 100M" >> /usr/local/etc/php/conf.d/uploads.ini \\
    && echo "memory_limit = 512M" >> /usr/local/etc/php/conf.d/memory.ini

# Expose ports
EXPOSE 9000 8080

# Start services
CMD ["sh", "-c", "php-fpm & code-server --bind-addr 0.0.0.0:8080 --auth none /workspace"]
"""

    def _generate_node_dockerfile(self, version: str, config: Dict) -> str:
        """Generate Node.js Dockerfile"""
        image = config.get('docker_image', 'node:{version}-alpine').format(version=version)
        packages = ' '.join(config.get('global_packages', []))
        
        return f"""FROM {image}

# Install system dependencies
RUN apk add --no-cache \\
    git \\
    curl \\
    bash \\
    python3 \\
    make \\
    g++

# Install global packages
RUN npm install -g {packages}

# Install code-server
RUN curl -fsSL https://code-server.dev/install.sh | sh

# Install Node.js VS Code extensions
RUN code-server --install-extension bradlc.vscode-tailwindcss \\
    --install-extension esbenp.prettier-vscode \\
    --install-extension ms-vscode.vscode-typescript-next

# Set working directory
WORKDIR /workspace

# Expose ports
EXPOSE 3000 8080

# Start services
CMD ["sh", "-c", "npm run dev & code-server --bind-addr 0.0.0.0:8080 --auth none /workspace"]
"""

    def _generate_python_dockerfile(self, version: str, config: Dict) -> str:
        """Generate Python Dockerfile"""
        image = config.get('docker_image', 'python:{version}-slim').format(version=version)
        packages = ' '.join(config.get('packages', []))
        
        return f"""FROM {image}

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    git \\
    curl \\
    build-essential \\
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip install --no-cache-dir {packages}

# Install code-server
RUN curl -fsSL https://code-server.dev/install.sh | sh

# Install Python VS Code extensions
RUN code-server --install-extension ms-python.python \\
    --install-extension ms-python.pylint \\
    --install-extension ms-python.black-formatter \\
    --install-extension ms-toolsai.jupyter

# Set working directory
WORKDIR /workspace

# Expose ports
EXPOSE 8000 8080

# Start services
CMD ["sh", "-c", "python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload & code-server --bind-addr 0.0.0.0:8080 --auth none /workspace"]
"""

    def _generate_wordpress_dockerfile(self, version: str, config: Dict) -> str:
        """Generate WordPress Dockerfile"""
        php_version = config.get('php_version', '8.2')
        
        return f"""FROM wordpress:{version}

# Install additional PHP extensions for development
RUN apt-get update && apt-get install -y \\
    git \\
    curl \\
    zip \\
    unzip \\
    && rm -rf /var/lib/apt/lists/*

# Install WP-CLI
RUN curl -O https://raw.githubusercontent.com/wp-cli/wp-cli/v2.8.1/wp-cli.phar \\
    && chmod +x wp-cli.phar \\
    && mv wp-cli.phar /usr/local/bin/wp

# Install code-server
RUN curl -fsSL https://code-server.dev/install.sh | sh

# Install WordPress VS Code extensions
RUN code-server --install-extension bmewburn.vscode-intelephense-client \\
    --install-extension wordpresstoolbox.wordpress-toolbox

# Set working directory
WORKDIR /var/www/html

# Expose ports
EXPOSE 80 8080

# Start services
CMD ["sh", "-c", "apache2-foreground & code-server --bind-addr 0.0.0.0:8080 --auth none /var/www/html"]
"""

    def show_version_management_menu(self):
        """Show version management interactive menu"""
        while True:
            console.clear()
            console.print(Panel("🔧 Version Management", style="bold blue"))
            
            # Show current defaults
            table = Table(title="Current Default Versions")
            table.add_column("Tool", style="cyan")
            table.add_column("Default Version", style="green")
            table.add_column("Available Versions", style="yellow")
            
            for tool, config in self.config['tools'].items():
                available = ", ".join(config.get('available', [])[:5])
                if len(config.get('available', [])) > 5:
                    available += "..."
                table.add_row(tool, config.get('default', 'N/A'), available)
            
            console.print(table)
            
            console.print("\n[cyan]Actions:[/cyan]")
            console.print("1. Set default version")
            console.print("2. Check latest versions")
            console.print("3. Update available versions")
            console.print("4. Generate Dockerfile")
            console.print("5. Back to main menu")
            
            choice = IntPrompt.ask("Choose action", choices=["1", "2", "3", "4", "5"])
            
            if choice == 5:
                break
            elif choice == 1:
                self._set_default_version_interactive()
            elif choice == 2:
                self._check_latest_versions_interactive()
            elif choice == 3:
                self._update_available_versions()
            elif choice == 4:
                self._generate_dockerfile_interactive()
    
    def _set_default_version_interactive(self):
        """Interactive default version setting"""
        tools = list(self.config['tools'].keys())
        console.print("\n[cyan]Available tools:[/cyan]")
        for i, tool in enumerate(tools, 1):
            console.print(f"{i}. {tool}")
        
        choice = IntPrompt.ask("Select tool", choices=[str(i) for i in range(1, len(tools)+1)])
        tool = tools[choice-1]
        
        available_versions = self.get_available_versions(tool)
        console.print(f"\n[cyan]Available versions for {tool}:[/cyan]")
        for i, version in enumerate(available_versions, 1):
            current = " (current)" if version == self.get_default_version(tool) else ""
            console.print(f"{i}. {version}{current}")
        
        version_choice = IntPrompt.ask("Select version", choices=[str(i) for i in range(1, len(available_versions)+1)])
        new_version = available_versions[version_choice-1]
        
        self.set_default_version(tool, new_version)
        Prompt.ask("\nPress Enter to continue")
    
    def _check_latest_versions_interactive(self):
        """Interactive latest version check"""
        latest_versions = self.check_latest_versions()
        
        if latest_versions:
            table = Table(title="Latest Available Versions")
            table.add_column("Tool", style="cyan")
            table.add_column("Current Default", style="yellow")
            table.add_column("Latest Available", style="green")
            table.add_column("Update Available", style="red")
            
            for tool, latest_version in latest_versions.items():
                current_default = self.get_default_version(tool)
                update_available = "Yes" if latest_version != current_default else "No"
                table.add_row(tool, current_default, latest_version, update_available)
            
            console.print(table)
            
            if Confirm.ask("\nUpdate defaults to latest versions?"):
                for tool, latest_version in latest_versions.items():
                    self.set_default_version(tool, latest_version)
                console.print("[green]✅ Defaults updated to latest versions[/green]")
        else:
            console.print("[yellow]Could not fetch latest versions[/yellow]")
        
        Prompt.ask("\nPress Enter to continue")
