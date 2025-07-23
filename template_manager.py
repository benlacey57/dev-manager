import os
import json
import yaml
from pathlib import Path
from typing import Dict, List, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
import click

console = Console()

class TemplateManager:
    def __init__(self):
        self.templates_dir = Path.home() / 'docker' / 'templates'
        self.config_dir = Path.home() / 'config' / 'templates'
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
    def get_available_templates(self) -> Dict[str, Dict]:
        """Dynamically discover available templates"""
        templates = {}
        
        for template_dir in self.templates_dir.iterdir():
            if template_dir.is_dir():
                config_file = template_dir / 'template.yml'
                if config_file.exists():
                    with open(config_file) as f:
                        config = yaml.safe_load(f)
                        templates[template_dir.name] = config
                        
        return templates
    
    def list_templates(self):
        """Display available templates"""
        templates = self.get_available_templates()
        
        table = Table(title="Available Project Templates")
        table.add_column("Template", style="cyan")
        table.add_column("Description", style="green")
        table.add_column("Tech Stack", style="yellow")
        table.add_column("Features", style="magenta")
        
        for name, config in templates.items():
            tech_stack = ", ".join(config.get('tech_stack', []))
            features = ", ".join(config.get('features', []))
            table.add_row(
                name,
                config.get('description', 'No description'),
                tech_stack,
                features
            )
        
        console.print(table)
        
    def create_project_from_template(self, template_name: str, project_name: str, domain: str = None):
        """Create new project from template"""
        templates = self.get_available_templates()
        
        if template_name not in templates:
            console.print(f"[red]Template {template_name} not found[/red]")
            return False
            
        template_config = templates[template_name]
        template_dir = self.templates_dir / template_name
        
        # Determine project location
        if domain:
            project_path = Path.home() / 'sites' / domain
        else:
            project_path = Path.home() / 'scripts' / project_name
            
        project_path.mkdir(parents=True, exist_ok=True)
        
        console.print(f"[green]Creating project from template: {template_name}[/green]")
        
        # Copy template files
        self._copy_template_files(template_dir, project_path, {
            'PROJECT_NAME': project_name,
            'DOMAIN': domain or f"{project_name}.local",
            'PROJECT_PATH': str(project_path)
        })
        
        # Generate docker-compose.yml
        self._generate_docker_compose(template_config, project_path, project_name)
        
        # Create environment file
        self._create_env_file(template_config, project_path, project_name, domain)
        
        # Setup git repository
        self._setup_git_repo(project_path, project_name)
        
        console.print(f"[green]Project {project_name} created successfully![/green]")
        console.print(f"[cyan]Location: {project_path}[/cyan]")
        
        return True
        
    def _copy_template_files(self, template_dir: Path, project_path: Path, variables: Dict[str, str]):
        """Copy template files with variable substitution"""
        import shutil
        
        for item in template_dir.rglob('*'):
            if item.is_file() and item.name != 'template.yml':
                # Calculate relative path
                rel_path = item.relative_to(template_dir)
                target_path = project_path / rel_path
                
                # Create target directory
                target_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Copy and substitute variables
                if item.suffix in ['.yml', '.yaml', '.json', '.py', '.js', '.php', '.md', '.txt', '.env']:
                    with open(item, 'r') as f:
                        content = f.read()
                    
                    # Variable substitution
                    for var, value in variables.items():
                        content = content.replace(f'{{{{{var}}}}}', value)
                    
                    with open(target_path, 'w') as f:
                        f.write(content)
                else:
                    shutil.copy2(item, target_path)
                    
    def _generate_docker_compose(self, template_config: Dict, project_path: Path, project_name: str):
        """Generate docker-compose.yml from template config"""
        compose_config = {
            'version': '3.8',
            'services': {},
            'networks': {
                'dev-network': {
                    'driver': 'bridge'
                }
            },
            'volumes': {}
        }
        
        # Add main development service
        main_service = {
            'build': {
                'context': str(Path.home() / 'docker'),
                'dockerfile': f"overlays/{template_config['base_overlay']}/Dockerfile"
            },
            'container_name': f"{project_name}-dev",
            'volumes': [
                f".:/workspace",
                f"/workspace/node_modules"  # Prevent node_modules from being overwritten
            ],
            'ports': template_config.get('ports', ['8080:8080']),
            'environment': [
                f"PROJECT_NAME={project_name}",
                "NODE_ENV=development"
            ],
            'networks': ['dev-network'],
            'labels': [
                f"traefik.enable=true",
                f"traefik.http.routers.{project_name}.rule=Host(`{project_name}.local`)",
                f"traefik.http.services.{project_name}.loadbalancer.server.port=8080",
                f"traefik.docker.network=dev-network"
            ]
        }
        
        compose_config['services']['dev'] = main_service
        
        # Add additional services from template
        for service_name, service_config in template_config.get('services', {}).items():
            compose_config['services'][service_name] = service_config
            
        # Write docker-compose.yml
        with open(project_path / 'docker-compose.yml', 'w') as f:
            yaml.dump(compose_config, f, default_flow_style=False)

    def _create_env_file(self, template_config: Dict, project_path: Path, project_name: str, domain: str):
        """Create .env file from template"""
        env_content = f"""# Project Configuration
PROJECT_NAME={project_name}
DOMAIN={domain or f"{project_name}.local"}
NODE_ENV=development

# Database Configuration
DB_HOST=db
DB_PORT=3306
DB_NAME={project_name}
DB_USER=user
DB_PASSWORD=password

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379

# Code Server Configuration
CODE_SERVER_PASSWORD=devpassword
"""
        
        # Add template-specific environment variables
        for key, value in template_config.get('environment', {}).items():
            env_content += f"{key}={value}\n"
            
        with open(project_path / '.env', 'w') as f:
            f.write(env_content)
            
        # Also create .env.example
        with open(project_path / '.env.example', 'w') as f:
            f.write(env_content)
            
    def _setup_git_repo(self, project_path: Path, project_name: str):
        """Initialize git repository"""
        import subprocess
        
        os.chdir(project_path)
        
        # Initialize git
        subprocess.run(['git', 'init'], check=True)
        
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
"""
        
        with open(project_path / '.gitignore', 'w') as f:
            f.write(gitignore_content)
            
        # Initial commit
        subprocess.run(['git', 'add', '.'], check=True)
      
