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
        self.version_manager = VersionManager()
        
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

    def create_project_from_template(self, template_name: str, project_name: str, domain: str = None, version_specs: Dict[str, str] = None):
        """Create new project from template with version specifications"""
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
        
        # Resolve versions
        resolved_versions = self._resolve_versions(template_config, version_specs)
        console.print(f"[cyan]Using versions: {resolved_versions}[/cyan]")
        
        # Copy template files with version substitution
        variables = {
            'PROJECT_NAME': project_name,
            'DOMAIN': domain or f"{project_name}.local",
            'PROJECT_PATH': str(project_path),
            **{f'{tool.upper()}_VERSION': version for tool, version in resolved_versions.items()}
        }
        
        self._copy_template_files(template_dir, project_path, variables)
        
        # Generate version-specific Dockerfiles
        self._generate_version_dockerfiles(project_path, resolved_versions)
        
        # Generate docker-compose.yml with versions
        self._generate_docker_compose(template_config, project_path, project_name, resolved_versions)
        
        # Create environment file
        self._create_env_file(template_config, project_path, project_name, domain, resolved_versions)
        
        # Setup git repository
        self._setup_git_repo(project_path, project_name)
        
        console.print(f"[green]Project {project_name} created successfully![/green]")
        console.print(f"[cyan]Location: {project_path}[/cyan]")
        
        return True
    
    def _resolve_versions(self, template_config: Dict, version_specs: Dict[str, str] = None) -> Dict[str, str]:
        """Resolve versions for template"""
        resolved = {}
        
        # Get required tools from template
        tech_stack = template_config.get('tech_stack', [])
        
        for tech in tech_stack:
            tool_name = tech.lower().split()[0]  # Extract tool name from "PHP 8.1" -> "php"
            
            if version_specs and tool_name in version_specs:
                # Use specified version
                resolved[tool_name] = version_specs[tool_name]
            else:
                # Use default version
                resolved[tool_name] = self.version_manager.get_default_version(tool_name)
        
        return resolved
    
    def _generate_version_dockerfiles(self, project_path: Path, versions: Dict[str, str]):
        """Generate Dockerfiles for specific versions"""
        docker_dir = project_path / 'docker'
        docker_dir.mkdir(exist_ok=True)
        
        for tool, version in versions.items():
            dockerfile_content = self.version_manager.generate_dockerfile(tool, version, project_path)
            if dockerfile_content:
                dockerfile_path = docker_dir / f'Dockerfile.{tool}'
                with open(dockerfile_path, 'w') as f:
                    f.write(dockerfile_content)
                console.print(f"  Generated: docker/Dockerfile.{tool} (v{version})")
    
    def _generate_docker_compose(self, template_config: Dict, project_path: Path, project_name: str, versions: Dict[str, str]):
        """Generate docker-compose.yml with version-specific services"""
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
        
        # Determine primary service based on template
        primary_tool = self._get_primary_tool(template_config)
        
        if primary_tool and primary_tool in versions:
            # Main development service
            main_service = {
                'build': {
                    'context': '.',
                    'dockerfile': f'docker/Dockerfile.{primary_tool}'
                },
                'container_name': f"{project_name}-dev",
                'volumes': [
                    ".:/workspace",
                    "/workspace/node_modules"  # Prevent overwrite
                ],
                'ports': template_config.get('ports', ['8080:8080']),
                'environment': [
                    f"PROJECT_NAME={project_name}",
                    f"{primary_tool.upper()}_VERSION={versions[primary_tool]}",
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
        
        # Add database services with versions
        if 'mysql' in str(template_config).lower() or 'laravel' in template_config.get('name', '').lower():
            compose_config['services']['db'] = {
                'image': 'mysql:8.0',
                'container_name': f"{project_name}-db",
                'environment': [
                    f"MYSQL_DATABASE={project_name}",
                    "MYSQL_USER=user",
                    "MYSQL_PASSWORD=password",
                    "MYSQL_ROOT_PASSWORD=rootpassword"
                ],
                'volumes': [
                    "mysql_data:/var/lib/mysql"
                ],
                'ports': ['3306:3306'],
                'networks': ['dev-network']
            }
            compose_config['volumes']['mysql_data'] = {}
        
        elif 'postgres' in str(template_config).lower():
            compose_config['services']['db'] = {
                'image': 'postgres:15',
                'container_name': f"{project_name}-db",
                'environment': [
                    f"POSTGRES_DB={project_name}",
                    "POSTGRES_USER=user",
                    "POSTGRES_PASSWORD=password"
                ],
                'volumes': [
                    "postgres_data:/var/lib/postgresql/data"
                ],
                'ports': ['5432:5432'],
                'networks': ['dev-network']
            }
            compose_config['volumes']['postgres_data'] = {}

        # Add Redis if needed
        if 'redis' in str(template_config).lower():
            compose_config['services']['redis'] = {
                'image': 'redis:7-alpine',
                'container_name': f"{project_name}-redis",
                'ports': ['6379:6379'],
                'networks': ['dev-network']
            }
        
        # Write docker-compose.yml
        with open(project_path / 'docker-compose.yml', 'w') as f:
            yaml.dump(compose_config, f, default_flow_style=False)
    
    def _get_primary_tool(self, template_config: Dict) -> str:
        """Determine primary tool from template config"""
        name = template_config.get('name', '').lower()
        
        if 'php' in name or 'laravel' in name or 'wordpress' in name:
            return 'php'
        elif 'node' in name or 'vue' in name or 'nuxt' in name or 'react' in name:
            return 'node'
        elif 'python' in name or 'fastapi' in name or 'django' in name:
            return 'python'
        
        # Check tech stack
        tech_stack = template_config.get('tech_stack', [])
        for tech in tech_stack:
            tech_lower = tech.lower()
            if 'php' in tech_lower:
                return 'php'
            elif 'node' in tech_lower or 'javascript' in tech_lower:
                return 'node'
            elif 'python' in tech_lower:
                return 'python'
        
        return 'node'  # Default fallback
    
    def _create_env_file(self, template_config: Dict, project_path: Path, project_name: str, domain: str, versions: Dict[str, str]):
        """Create .env file with version information"""
        env_content = f"""# Project Configuration
PROJECT_NAME={project_name}
DOMAIN={domain or f"{project_name}.local"}
NODE_ENV=development

# Tool Versions
"""
        
        # Add version information
        for tool, version in versions.items():
            env_content += f"{tool.upper()}_VERSION={version}\n"
        
        env_content += """
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
