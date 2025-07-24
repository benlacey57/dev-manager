#!/usr/bin/env python3
# cli/project_manager.py - Enhanced project management

import os
import sys
import subprocess
import secrets
import string
from pathlib import Path
from typing import Dict, List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

console = Console()

class ProjectManager:
    def __init__(self):
        self.projects_dir = Path.home() / 'scripts'
        self.sites_dir = Path.home() / 'sites'
        self.templates_dir = Path(__file__).parent.parent / 'templates'
        
        # Import managers
        from .ssl_manager import SSLManager
        from .version_manager import VersionManager
        
        self.ssl_manager = SSLManager()
        self.version_manager = VersionManager()
    
    def new_project_wizard(self):
        """Enhanced project creation wizard"""
        console.clear()
        console.print(Panel("🆕 Create New Project", style="bold green"))
        
        # Project type selection
        project_types = ["website", "script", "wordpress", "laravel", "nuxt", "react", "api"]
        
        console.print("[cyan]Available project types:[/cyan]")
        for i, project_type in enumerate(project_types, 1):
            console.print(f"  {i}. {project_type.title()}")
        
        choice = IntPrompt.ask("Select project type", choices=[str(i) for i in range(1, len(project_types) + 1)])
        project_type = project_types[choice - 1]
        
        if project_type == "wordpress":
            self._create_wordpress_project()
        elif project_type in ["laravel", "nuxt", "react"]:
            self._create_template_project(project_type)
        else:
            self._create_regular_project(project_type)
    
    def _create_regular_project(self, project_type):
        """Create regular project with full implementation"""
        console.clear()
        console.print(Panel(f"🚀 Create {project_type.title()} Project", style="bold blue"))
        
        # Get project details
        project_name = Prompt.ask("Project name")
        
        # Determine if it's a website or script
        is_website = project_type == "website" or Confirm.ask("Is this a website project?", default=project_type == "website")
        
        domain = ""
        if is_website:
            domain = Prompt.ask("Domain name (e.g., example.com)", default=f"{project_name}.local")
        
        # Technology stack selection
        tech_stack = self._select_technology_stack(project_type)
        
        # Version selection
        versions = self._select_versions(tech_stack)
        
        # SSL configuration for websites
        ssl_enabled = False
        if is_website and domain:
            ssl_enabled = Confirm.ask("Enable SSL certificate?", default=True)
        
        # Show project summary
        console.print(f"\n[cyan]Project Summary:[/cyan]")
        console.print(f"• Name: {project_name}")
        console.print(f"• Type: {project_type}")
        if is_website:
            console.print(f"• Domain: {domain}")
        console.print(f"• Technology: {', '.join(tech_stack)}")
        if versions:
            console.print("• Versions:")
            for tech, version in versions.items():
                console.print(f"  - {tech}: {version}")
        if ssl_enabled:
            console.print("• SSL: Enabled")
        
        if Confirm.ask(f"\nCreate {project_type} project?"):
            success = self._create_project_files(
                project_name, project_type, domain, tech_stack, versions, ssl_enabled
            )
            
            if success:
                console.print(f"[green]✅ {project_type.title()} project created successfully![/green]")
                
                # Show next steps
                self._show_project_next_steps(project_name, domain, is_website)
            else:
                console.print(f"[red]❌ Failed to create {project_type} project[/red]")
        
        Prompt.ask("\nPress Enter to continue")
    
    def _select_technology_stack(self, project_type: str) -> List[str]:
        """Select technology stack for project"""
        tech_options = {
            "website": ["html", "php", "python", "node", "static"],
            "script": ["python", "bash", "node", "php"],
            "api": ["python", "node", "php", "go"]
        }
        
        available_tech = tech_options.get(project_type, ["python", "node", "php"])
        
        console.print(f"\n[cyan]Available technologies for {project_type}:[/cyan]")
        for i, tech in enumerate(available_tech, 1):
            console.print(f"  {i}. {tech.title()}")
        
        choice = IntPrompt.ask("Select technology", choices=[str(i) for i in range(1, len(available_tech) + 1)])
        selected_tech = available_tech[choice - 1]
        
        # Additional technologies
        additional_tech = []
        if selected_tech in ["php", "python", "node"]:
            if Confirm.ask("Add database?", default=True):
                db_choice = Prompt.ask("Database type", choices=["mysql", "postgresql", "sqlite"], default="mysql")
                additional_tech.append(db_choice)
            
            if Confirm.ask("Add Redis cache?", default=False):
                additional_tech.append("redis")
        
        return [selected_tech] + additional_tech
    
    def _select_versions(self, tech_stack: List[str]) -> Dict[str, str]:
        """Select versions for technologies"""
        versions = {}
        
        version_mappings = {
            "php": self.version_manager.get_available_versions("php"),
            "python": self.version_manager.get_available_versions("python"),
            "node": self.version_manager.get_available_versions("node"),
            "mysql": ["8.0", "5.7"],
            "postgresql": ["15", "14", "13"],
            "redis": ["7", "6"]
        }
        
        for tech in tech_stack:
            if tech in version_mappings:
                available_versions = version_mappings[tech]
                default_version = self.version_manager.get_default_version(tech) if hasattr(self.version_manager, 'get_default_version') else available_versions[0]
                
                if len(available_versions) > 1:
                    console.print(f"\n[cyan]{tech.title()} versions:[/cyan]")
                    for i, version in enumerate(available_versions, 1):
                        default_marker = " (default)" if version == default_version else ""
                        console.print(f"  {i}. {version}{default_marker}")
                    
                    choice = IntPrompt.ask(f"Select {tech} version", 
                                         choices=[str(i) for i in range(1, len(available_versions) + 1)],
                                         default="1")
                    versions[tech] = available_versions[choice - 1]
                else:
                    versions[tech] = available_versions[0]
        
        return versions
    
    def _create_project_files(self, project_name: str, project_type: str, domain: str, 
                            tech_stack: List[str], versions: Dict[str, str], ssl_enabled: bool) -> bool:
        """Create project files and structure"""
        try:
            # Determine project path
            if domain:
                project_path = self.sites_dir / domain
            else:
                project_path = self.projects_dir / project_name
            
            project_path.mkdir(parents=True, exist_ok=True)
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Creating project structure...", total=None)
                
                # Create basic structure
                self._create_basic_structure(project_path, tech_stack)
                progress.update(task, description="✅ Basic structure created")
                
                # Generate Docker configuration
                self._generate_docker_config(project_path, project_name, tech_stack, versions, domain)
                progress.update(task, description="✅ Docker configuration generated")
                
                # Create application files
                self._create_application_files(project_path, tech_stack[0], project_name)
                progress.update(task, description="✅ Application files created")
                
                # Setup SSL if enabled
                if ssl_enabled and domain:
                    progress.update(task, description="🔒 Setting up SSL...")
                    ssl_success = self.ssl_manager.add_certificate(domain, 'letsencrypt', 'website')
                    if ssl_success:
                        progress.update(task, description="✅ SSL certificate configured")
                    else:
                        progress.update(task, description="⚠️ SSL setup failed")
                
                # Initialize git repository
                self._init_git_repo(project_path, project_name)
                progress.update(task, description="✅ Git repository initialized")
                
                progress.update(task, description="🎉 Project created successfully!")
            
            return True
            
        except Exception as e:
            console.print(f"[red]Failed to create project: {e}[/red]")
            return False
    
    def _create_basic_structure(self, project_path: Path, tech_stack: List[str]):
        """Create basic project directory structure"""
        directories = ["src", "docs", "tests"]
        
        # Add tech-specific directories
        if "php" in tech_stack:
            directories.extend(["public", "config", "storage"])
        elif "python" in tech_stack:
            directories.extend(["app", "requirements"])
        elif "node" in tech_stack:
            directories.extend(["public", "routes", "views"])
        
        if any(db in tech_stack for db in ["mysql", "postgresql"]):
            directories.append("database")
        
        for directory in directories:
            (project_path / directory).mkdir(exist_ok=True)
        
        # Create .env file
        env_content = f"PROJECT_NAME={project_path.name}\n"
        env_content += "NODE_ENV=development\n"
        
        (project_path / '.env').write_text(env_content)
        (project_path / '.env.example').write_text(env_content)

      def _generate_docker_config(self, project_path: Path, project_name: str, 
                               tech_stack: List[str], versions: Dict[str, str], domain: str):
        """Generate Docker Compose configuration"""
        primary_tech = tech_stack[0]
        
        # Base service configuration
        services = {
            "app": {
                "build": ".",
                "container_name": f"{project_name}-app",
                "restart": "unless-stopped",
                "volumes": ["./:/workspace"],
                "working_dir": "/workspace",
                "networks": ["app-network"]
            }
        }
        
        # Add ports based on technology
        if primary_tech == "php":
            services["app"]["ports"] = ["8000:8000"]
            services["app"]["image"] = f"php:{versions.get('php', '8.2')}-fpm"
        elif primary_tech == "python":
            services["app"]["ports"] = ["8000:8000"]
            services["app"]["image"] = f"python:{versions.get('python', '3.11')}-slim"
        elif primary_tech == "node":
            services["app"]["ports"] = ["3000:3000"]
            services["app"]["image"] = f"node:{versions.get('node', '18')}-alpine"
        
        # Add Traefik labels if domain is provided
        if domain:
            services["app"]["labels"] = [
                "traefik.enable=true",
                f"traefik.http.routers.{project_name}.rule=Host(`{domain}`)",
                f"traefik.http.routers.{project_name}.tls=true",
                f"traefik.http.routers.{project_name}.tls.certresolver=letsencrypt",
                f"traefik.http.services.{project_name}.loadbalancer.server.port={services['app']['ports'][0].split(':')[1]}",
                "traefik.docker.network=proxy"
            ]
            services["app"]["networks"].append("proxy")
        
        # Add database services
        if "mysql" in tech_stack:
            services["db"] = {
                "image": f"mysql:{versions.get('mysql', '8.0')}",
                "container_name": f"{project_name}-db",
                "restart": "unless-stopped",
                "environment": [
                    "MYSQL_ROOT_PASSWORD=rootpassword",
                    f"MYSQL_DATABASE={project_name}",
                    "MYSQL_USER=user",
                    "MYSQL_PASSWORD=password"
                ],
                "volumes": ["mysql_data:/var/lib/mysql"],
                "ports": ["3306:3306"],
                "networks": ["app-network"]
            }
        
        if "postgresql" in tech_stack:
            services["db"] = {
                "image": f"postgres:{versions.get('postgresql', '15')}",
                "container_name": f"{project_name}-db",
                "restart": "unless-stopped",
                "environment": [
                    f"POSTGRES_DB={project_name}",
                    "POSTGRES_USER=user",
                    "POSTGRES_PASSWORD=password"
                ],
                "volumes": ["postgres_data:/var/lib/postgresql/data"],
                "ports": ["5432:5432"],
                "networks": ["app-network"]
            }
        
        if "redis" in tech_stack:
            services["redis"] = {
                "image": f"redis:{versions.get('redis', '7')}-alpine",
                "container_name": f"{project_name}-redis",
                "restart": "unless-stopped",
                "ports": ["6379:6379"],
                "networks": ["app-network"]
            }
        
        # Compose file structure
        compose_config = {
            "version": "3.8",
            "services": services,
            "networks": {
                "app-network": {"driver": "bridge"}
            },
            "volumes": {}
        }
        
        # Add external proxy network if domain is provided
        if domain:
            compose_config["networks"]["proxy"] = {"external": True}
        
        # Add volume definitions
        if "mysql" in tech_stack:
            compose_config["volumes"]["mysql_data"] = {}
        if "postgresql" in tech_stack:
            compose_config["volumes"]["postgres_data"] = {}
        
        # Write docker-compose.yml
        import yaml
        with open(project_path / 'docker-compose.yml', 'w') as f:
            yaml.dump(compose_config, f, default_flow_style=False)
        
        # Create Dockerfile
        self._create_dockerfile(project_path, primary_tech, versions)
    
    def _create_dockerfile(self, project_path: Path, tech: str, versions: Dict[str, str]):
        """Create Dockerfile based on technology"""
        if tech == "php":
            dockerfile_content = f"""FROM php:{versions.get('php', '8.2')}-fpm

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    git curl libpng-dev libonig-dev libxml2-dev zip unzip

# Install PHP extensions
RUN docker-php-ext-install pdo_mysql mbstring exif pcntl bcmath gd

# Install Composer
COPY --from=composer:latest /usr/bin/composer /usr/bin/composer

# Set working directory
WORKDIR /workspace

# Install code-server
RUN curl -fsSL https://code-server.dev/install.sh | sh

# Expose ports
EXPOSE 8000 8080

# Start PHP and code-server
CMD ["sh", "-c", "php -S 0.0.0.0:8000 -t public & code-server --bind-addr 0.0.0.0:8080 --auth none /workspace"]
"""
        
        elif tech == "python":
            dockerfile_content = f"""FROM python:{versions.get('python', '3.11')}-slim

# Install system dependencies
RUN apt-get update && apt-get install -y git curl build-essential

# Install Python packages
RUN pip install fastapi uvicorn requests

# Install code-server
RUN curl -fsSL https://code-server.dev/install.sh | sh

# Set working directory
WORKDIR /workspace

# Expose ports
EXPOSE 8000 8080

# Start application and code-server
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port 8000 --reload & code-server --bind-addr 0.0.0.0:8080 --auth none /workspace"]
"""
        
        elif tech == "node":
            dockerfile_content = f"""FROM node:{versions.get('node', '18')}-alpine

# Install system dependencies
RUN apk add --no-cache git curl bash

# Install global packages
RUN npm install -g nodemon

# Install code-server
RUN curl -fsSL https://code-server.dev/install.sh | sh

# Set working directory
WORKDIR /workspace

# Expose ports
EXPOSE 3000 8080

# Start application and code-server
CMD ["sh", "-c", "npm start & code-server --bind-addr 0.0.0.0:8080 --auth none /workspace"]
"""
        
        else:
            dockerfile_content = """FROM ubuntu:22.04

# Install basic tools
RUN apt-get update && apt-get install -y git curl

# Install code-server
RUN curl -fsSL https://code-server.dev/install.sh | sh

# Set working directory
WORKDIR /workspace

# Expose code-server port
EXPOSE 8080

# Start code-server
CMD ["code-server", "--bind-addr", "0.0.0.0:8080", "--auth", "none", "/workspace"]
"""
        
        (project_path / 'Dockerfile').write_text(dockerfile_content)

    def _create_application_files(self, project_path: Path, tech: str, project_name: str):
        """Create basic application files"""
        if tech == "php":
            # Create basic PHP application
            (project_path / 'public' / 'index.php').write_text(f"""<?php
echo "<h1>Welcome to {project_name}!</h1>";
echo "<p>PHP application is running.</p>";
""")
            
            (project_path / 'composer.json').write_text(f"""{{
    "name": "user/{project_name}",
    "description": "{project_name} PHP application",
    "require": {{
        "php": ">=8.0"
    }}
}}""")
        
        elif tech == "python":
            # Create FastAPI application
            (project_path / 'main.py').write_text(f"""from fastapi import FastAPI

app = FastAPI(title="{project_name}")

@app.get("/")
def read_root():
    return {{"message": "Welcome to {project_name}!"}}

@app.get("/health")
def health_check():
    return {{"status": "healthy"}}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
""")
            
            (project_path / 'requirements.txt').write_text("""fastapi
uvicorn[standard]
requests
""")
        
        elif tech == "node":
            # Create Express application
            (project_path / 'package.json').write_text(f"""{{
    "name": "{project_name}",
    "version": "1.0.0",
    "description": "{project_name} Node.js application",
    "main": "index.js",
    "scripts": {{
        "start": "node index.js",
        "dev": "nodemon index.js"
    }},
    "dependencies": {{
        "express": "^4.18.0"
    }},
    "devDependencies": {{
        "nodemon": "^2.0.0"
    }}
}}""")
            
            (project_path / 'index.js').write_text(f"""const express = require('express');
const app = express();
const port = 3000;

app.get('/', (req, res) => {{
    res.json({{ message: 'Welcome to {project_name}!' }});
}});

app.get('/health', (req, res) => {{
    res.json({{ status: 'healthy' }});
}});

app.listen(port, () => {{
    console.log(`{project_name} listening at http://localhost:${{port}}`);
}});
""")
        
        else:
            # Create basic HTML file
            (project_path / 'index.html').write_text(f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{project_name}</title>
</head>
<body>
    <h1>Welcome to {project_name}!</h1>
    <p>Your project is ready for development.</p>
</body>
</html>
""")
    
    def _init_git_repo(self, project_path: Path, project_name: str):
        """Initialize git repository"""
        try:
            os.chdir(project_path)
            
            # Initialize git
            subprocess.run(['git', 'init'], check=True, capture_output=True)
            
            # Create .gitignore
            gitignore_content = """# Dependencies
node_modules/
vendor/
__pycache__/
*.pyc

# Environment files
.env
.env.local
.env.*.local

# Build outputs
dist/
build/
*.log

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db

# Docker
.docker/
docker-compose.override.yml

# Database
*.sql
*.db
*.sqlite
"""
            
            (project_path / '.gitignore').write_text(gitignore_content)
            
            # Create README
            readme_content = f"""# {project_name}

## Getting Started

### Prerequisites
- Docker and Docker Compose

### Development

1. Start the development environment:
```bash
docker-compose up -dAccess the application:Application: http://localhost:3000 (or 8000)VS Code: http://localhost:8080Stop the environment:docker-compose downProject Structure{project_name}/
├── src/              # Source code
├── tests/            # Test files
├── docs/             # Documentation
├── docker-compose.yml # Docker configuration
├── Dockerfile        # Container definition
└── README.md         # This fileDevelopment Commands# View logs
docker-compose logs -f

# Rebuild containers
docker-compose up --build

# Run shell in container
docker-compose exec app bash"""(project_path / 'README.md').write_text(readme_content)
        
        # Initial commit
        subprocess.run(['git', 'add', '.'], check=True, capture_output=True)
        subprocess.run(['git', 'commit', '-m', f'Initial commit for {project_name}'], 
                     check=True, capture_output=True)
        
    except subprocess.CalledProcessError:
        # Git operations are optional, continue if they fail
        pass

def _show_project_next_steps(self, project_name: str, domain: str, is_website: bool):
    """Show next steps after project creation"""
    next_steps = f"[cyan]Next Steps:[/cyan]\n"
    
    if is_website:
        project_path = self.sites_dir / domain
        next_steps += f"1. cd {project_path}\n"
        next_steps += f"2. docker-compose up -d\n"
        if domain:
            next_steps += f"3. Visit https://{domain} (or http://{domain})\n"
            next_steps += f"4. VS Code: http://{domain}:8080\n"
        else:
            next_steps += f"3. Visit http://localhost:8000\n"
            next_steps += f"4. VS Code: http://localhost:8080\n"
    else:
        project_path = self.projects_dir / project_name
        next_steps += f"1. cd {project_path}\n"
        next_steps += f"2. docker-compose up -d\n"
        next_steps += f"3. VS Code: http://localhost:8080\n"
    
    next_steps += f"\n[yellow]Useful commands:[/yellow]\n"
    next_steps += f"• View logs: docker-compose logs -f\n"
    next_steps += f"• Stop: docker-compose down\n"
    next_steps += f"• Rebuild: docker-compose up --build"
    
    console.print(Panel.fit(next_steps, title=f"🎉 {project_name} Ready"))

def _create_wordpress_project(self):
    """Create WordPress project using WordPress manager"""
    try:
        # Import WordPress manager
        from ..templates.wordpress_manager import WordPressManager
        
        wp_manager = WordPressManager(self.ssl_manager)
        
        project_name = Prompt.ask("Project name")
        domain = Prompt.ask("Domain name (e.g., mysite.com)")
        ssl_enabled = Confirm.ask("Enable SSL certificate?", default=True)
        
        console.print(f"\n[cyan]WordPress Project Summary:[/cyan]")
        console.print(f"• Name: {project_name}")
        console.print(f"• Domain: {domain}")
        console.print(f"• SSL: {'Enabled' if ssl_enabled else 'Disabled'}")
        
        if Confirm.ask("\nCreate WordPress project?"):
            success = wp_manager.create_wordpress_project(project_name, domain, ssl_enabled)
            
            if success:
                console.print("[green]✅ WordPress project created successfully![/green]")
            else:
                console.print("[red]❌ Failed to create WordPress project[/red]")
        
    except ImportError:
        console.print("[red]WordPress manager not available[/red]")
    
    Prompt.ask("\nPress Enter to continue")

def _create_template_project(self, project_type: str):
    """Create project from template (Laravel, Nuxt, React)"""
    console.print(f"[yellow]{project_type.title()} template coming soon![/yellow]")
    
    # Placeholder for template-based project creation
    project_name = Prompt.ask("Project name")
    domain = Prompt.ask("Domain name (optional)", default="")
    
    console.print(f"[blue]Creating {project_type} project: {project_name}[/blue]")
    console.print(f"[yellow]Template system will be implemented soon![/yellow]")
    
    Prompt.ask("\nPress Enter to continue")

def list_projects(self):
    """List all projects"""
    console.clear()
    console.print(Panel("📋 Project Overview", style="bold blue"))
    
    # List script projects
    console.print("\n[cyan]📝 Script Projects:[/cyan]")
    script_projects = self._get_projects(self.projects_dir)
    
    if script_projects:
        script_table = Table()
        script_table.add_column("Name", style="green")
        script_table.add_column("Type", style="cyan")
        script_table.add_column("Status", style="yellow")
        script_table.add_column("Path", style="blue")
        
        for project in script_projects:
            script_table.add_row(
                project['name'], 
                project['type'], 
                project['status'], 
                project['path']
            )
        
        console.print(script_table)
    else:
        console.print("[yellow]No script projects found[/yellow]")
    
    # List website projects
    console.print("\n[cyan]🌐 Website Projects:[/cyan]")
    site_projects = self._get_projects(self.sites_dir)
    
    if site_projects:
        site_table = Table()
        site_table.add_column("Domain", style="green")
        site_table.add_column("Type", style="cyan")
        site_table.add_column("Status", style="yellow")
        site_table.add_column("SSL", style="magenta")
        site_table.add_column("Path", style="blue")
        
        for project in site_projects:
            ssl_status = self._get_ssl_status(project['name'])
            site_table.add_row(
                project['name'], 
                project['type'], 
                project['status'],
                ssl_status,
                project['path']
            )
        
        console.print(site_table)
    else:
        console.print("[yellow]No website projects found[/yellow]")
    
    Prompt.ask("\nPress Enter to continue")

def _get_projects(self, base_dir: Path) -> List[Dict]:
    """Get projects from directory"""
    projects = []
    
    if not base_dir.exists():
        return projects
    
    for project_dir in base_dir.iterdir():
        if project_dir.is_dir():
            project_info = {
                'name': project_dir.name,
                'path': str(project_dir),
                'type': self._detect_project_type(project_dir),
                'status': self._get_project_status(project_dir)
            }
            projects.append(project_info)
    
    return projects

def _detect_project_type(self, project_dir: Path) -> str:
    """Detect project type from files"""
    if (project_dir / 'composer.json').exists():
        composer_data = self._read_json_file(project_dir / 'composer.json')
        if composer_data and 'laravel/framework' in str(composer_data):
            return 'Laravel'
        return 'PHP'
    elif (project_dir / 'package.json').exists():
        package_data = self._read_json_file(project_dir / 'package.json')
        if package_data:
            deps = str(package_data.get('dependencies', {}))
            if 'nuxt' in deps:
                return 'Nuxt'
            elif 'react' in deps:
                return 'React'
            elif 'express' in deps:
                return 'Express'
            return 'Node.js'
    elif (project_dir / 'requirements.txt').exists() or (project_dir / 'main.py').exists():
        return 'Python'
    elif (project_dir / 'docker-compose.yml').exists():
        compose_content = (project_dir / 'docker-compose.yml').read_text()
        if 'wordpress' in compose_content:
            return 'WordPress'
        return 'Docker'
    elif (project_dir / 'index.html').exists():
        return 'Static'
    else:
        return 'Unknown'

def _read_json_file(self, file_path: Path) -> Dict:
    """Safely read JSON file"""
    try:
        import json
        with open(file_path) as f:
            return json.load(f)
    except:
        return {}

def _get_project_status(self, project_dir: Path) -> str:
    """Get project container status"""
    try:
        compose_file = project_dir / 'docker-compose.yml'
        if compose_file.exists():
            os.chdir(project_dir)
            result = subprocess.run(
                ['docker-compose', 'ps', '-q'], 
                capture_output=True, 
                text=True, 
                check=True
            )
            
            if result.stdout.strip():
                # Check if containers are running
                container_ids = result.stdout.strip().split('\n')
                running_count = 0
                
                for container_id in container_ids:
                    if container_id:
                        try:
                            status_result = subprocess.run(
                                ['docker', 'inspect', '-f', '{{.State.Status}}', container_id],
                                capture_output=True, text=True, check=True
                            )
                            if status_result.stdout.strip() == 'running':
                                running_count += 1
                        except:
                            continue
                
                if running_count == len([c for c in container_ids if c]):
                    return "🟢 Running"
                elif running_count > 0:
                    return "🟡 Partial"
                else:
                    return "🔴 Stopped"
            else:
                return "⚪ Not Created"
        else:
            return "📁 No Docker"
    except:
        return "❓ Unknown"

def _get_ssl_status(self, domain: str) -> str:
    """Get SSL certificate status for domain"""
    certificates = self.ssl_manager.get_certificates()
    
    for cert in certificates:
        if cert['domain'] == domain:
            if cert['status'] == 'active':
                cert_type = '🔒' if cert['type'] == 'letsencrypt' else '🏠'
                return f"{cert_type} Active"
            elif cert['status'] == 'pending':
                return "🟡 Pending"
            else:
                return "🔴 Failed"
    
    return "⚪ None"

def manage_sites(self):
    """Manage website projects"""
    console.print("[yellow]Site management coming soon![/yellow]")
    Prompt.ask("\nPress Enter to continue")

def template_management(self):
    """Template management"""
    console.print("[yellow]Template management coming soon![/yellow]")
    Prompt.ask("\nPress Enter to continue")## **6. CLI Module Initialization (`cli/__init__.py`)**

```python
#!/usr/bin/env python3
# cli/__init__.py - CLI module initialization

from .main_menu import DevManager
from .project_manager import ProjectManager
from .ssl_manager import SSLManager

__all__ = ['DevManager', 'ProjectManager', 'SSLManager']
