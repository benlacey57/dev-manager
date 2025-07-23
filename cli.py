import os
import sys
import subprocess
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.layout import Layout
from rich.live import Live
from rich.progress import Progress, SpinnerColumn, TextColumn
import click
import docker
from template_manager import TemplateManager

console = Console()
docker_client = docker.from_env()

class DevManager:
    def __init__(self):
        self.template_manager = TemplateManager()
        self.projects_dir = Path.home() / 'scripts'
        self.sites_dir = Path.home() / 'sites'
        
    def show_main_menu(self):
        """Display main interactive menu"""
        while True:
            console.clear()
            console.print(Panel.fit(
                "[bold cyan]🚀 Development Environment Manager[/bold cyan]\n\n"
                "[green]Choose an action:[/green]",
                title="Dev Manager"
            ))
            
            options = [
                "📝 Create New Project",
                "📋 List Projects", 
                "🐳 Manage Containers",
                "🌐 Manage Sites",
                "📦 Template Management",
                "⚙️  Infrastructure",
                "🔧 Configuration",
                "❌ Exit"
            ]
            
            for i, option in enumerate(options, 1):
                console.print(f"  {i}. {option}")
            
            choice = IntPrompt.ask("\nEnter your choice", choices=[str(i) for i in range(1, len(options)+1)])
            
            if choice == 1:
                self.create_project_wizard()
            elif choice == 2:
                self.list_projects()
            elif choice == 3:
                self.manage_containers()
            elif choice == 4:
                self.manage_sites()
            elif choice == 5:
                self.template_management()
            elif choice == 6:
                self.infrastructure_management()
            elif choice == 7:
                self.configuration_management()
            elif choice == 8:
                console.print("[yellow]Goodbye![/yellow]")
                break
                
    def create_project_wizard(self):
        """Interactive project creation wizard"""
        console.clear()
        console.print(Panel("📝 Create New Project", style="bold green"))
        
        # Choose project type
        project_type = Prompt.ask(
            "Project type",
            choices=["script", "website"],
            default="script"
        )
        
        # Get project name
        project_name = Prompt.ask("Project name")
        
        # Get domain if website
        domain = None
        if project_type == "website":
            domain = Prompt.ask("Domain name (e.g., mysite.co.uk)")
        
        # Show available templates
        console.print("\n[cyan]Available templates:[/cyan]")
        self.template_manager.list_templates()
        
        templates = list(self.template_manager.get_available_templates().keys())
        template = Prompt.ask("Choose template", choices=templates)
        
        # Confirm creation
        if Confirm.ask(f"\nCreate {project_type} '{project_name}' using '{template}' template?"):
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Creating project...", total=None)
                
                success = self.template_manager.create_project_from_template(
                    template, project_name, domain
                )
                
                if success:
                    progress.update(task, description="✅ Project created successfully!")
                    console.print(f"\n[green]Project created![/green]")
                    
                    if Confirm.ask("Start development environment now?"):
                        self.start_project(project_name, project_type)
                else:
                    console.print("[red]Failed to create project[/red]")
        
        Prompt.ask("\nPress Enter to continue")
        
    def start_project(self, project_name: str, project_type: str):
        """Start development environment for project"""
        if project_type == "script":
            project_path = self.projects_dir / project_name
        else:
            # For websites, we need to find the domain
            for site_dir in self.sites_dir.iterdir():
                if site_dir.is_dir():
                    # Check if this site contains our project
                    compose_file = site_dir / 'docker-compose.yml'
                    if compose_file.exists():
                        with open(compose_file) as f:
                            compose_data = yaml.safe_load(f)
                            if project_name in str(compose_data):
                                project_path = site_dir
                                break
            else:
                console.print(f"[red]Could not find website project {project_name}[/red]")
                return
        
        if not project_path.exists():
            console.print(f"[red]Project {project_name} not found[/red]")
            return
            
        os.chdir(project_path)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Starting containers...", total=None)
            
            try:
                subprocess.run(['docker-compose', 'up', '-d'], check=True, capture_output=True)
                progress.update(task, description="✅ Containers started!")
                
                # Show access information
                console.print(Panel.fit(
                    f"[green]🚀 {project_name} is now running![/green]\n\n"
                    f"• Code Server: http://localhost:8080\n"
                    f"• Application: http://localhost:3000 (or 8000)\n"
                    f"• Project Path: {project_path}\n\n"
                    f"[cyan]Useful commands:[/cyan]\n"
                    f"• View logs: docker-compose logs -f\n"
                    f"• Stop: docker-compose down\n"
                    f"• Rebuild: docker-compose up --build",
                    title=f"🎉 {project_name} Ready"
                ))
                
            except subprocess.CalledProcessError as e:
                console.print(f"[red]Failed to start containers: {e}[/red]")

    def list_projects(self):
        """List all projects"""
        console.clear()
        console.print(Panel("📋 Project Overview", style="bold blue"))
        
        # List script projects
        console.print("\n[cyan]📝 Script Projects:[/cyan]")
        script_table = Table()
        script_table.add_column("Name", style="green")
        script_table.add_column("Status", style="yellow")
        script_table.add_column("Path", style="blue")
        
        for project_dir in self.projects_dir.iterdir():
            if project_dir.is_dir() and (project_dir / 'docker-compose.yml').exists():
                status = self._get_project_status(project_dir)
                script_table.add_row(project_dir.name, status, str(project_dir))
        
        console.print(script_table)
        
        # List website projects
        console.print("\n[cyan]🌐 Website Projects:[/cyan]")
        site_table = Table()
        site_table.add_column("Domain", style="green")
        site_table.add_column("Status", style="yellow")  
        site_table.add_column("Path", style="blue")
        
        for site_dir in self.sites_dir.iterdir():
            if site_dir.is_dir() and (site_dir / 'docker-compose.yml').exists():
                status = self._get_project_status(site_dir)
                site_table.add_row(site_dir.name, status, str(site_dir))
        
        console.print(site_table)
        
        Prompt.ask("\nPress Enter to continue")
        
    def _get_project_status(self, project_path: Path) -> str:
        """Get status of project containers"""
        try:
            os.chdir(project_path)
            result = subprocess.run(
                ['docker-compose', 'ps', '-q'], 
                capture_output=True, 
                text=True, 
                check=True
            )
            
            if result.stdout.strip():
                # Check if containers are running
                containers = result.stdout.strip().split('\n')
                running_count = 0
                for container_id in containers:
                    if container_id:
                        container = docker_client.containers.get(container_id)
                        if container.status == 'running':
                            running_count += 1
                
                if running_count == len(containers):
                    return "🟢 Running"
                elif running_count > 0:
                    return "🟡 Partial"
                else:
                    return "🔴 Stopped"
            else:
                return "⚪ Not Created"
        except:
            return "❓ Unknown"

      def manage_containers(self):
        """Container management interface"""
        while True:
            console.clear()
            console.print(Panel("🐳 Container Management", style="bold blue"))
            
            # Show running containers
            containers = docker_client.containers.list(all=True)
            dev_containers = [c for c in containers if any(tag in c.name for tag in ['dev', 'script', 'site'])]
            
            if dev_containers:
                table = Table()
                table.add_column("Name", style="cyan")
                table.add_column("Status", style="green")
                table.add_column("Ports", style="yellow")
                table.add_column("Image", style="blue")
                
                for container in dev_containers:
                    ports = ", ".join([f"{k}→{v[0]['HostPort']}" for k, v in container.ports.items() if v])
                    table.add_row(
                        container.name,
                        container.status,
                        ports,
                        container.image.tags[0] if container.image.tags else "unknown"
                    )
                
                console.print(table)
            else:
                console.print("[yellow]No development containers found[/yellow]")
            
            console.print("\n[cyan]Actions:[/cyan]")
            console.print("1. Start project")
            console.print("2. Stop project") 
            console.print("3. Restart project")
            console.print("4. View logs")
            console.print("5. Open shell")
            console.print("6. Clean up")
            console.print("7. Back to main menu")
            
            choice = IntPrompt.ask("Choose action", choices=["1", "2", "3", "4", "5", "6", "7"])
            
            if choice == 7:
                break
            elif choice == 1:
                self._start_project_interactive()
            elif choice == 2:
                self._stop_project_interactive()
            elif choice == 3:
                self._restart_project_interactive()
            elif choice == 4:
                self._view_logs_interactive()
            elif choice == 5:
                self._open_shell_interactive()
            elif choice == 6:
                self._cleanup_containers()

    def _start_project_interactive(self):
        """Interactive project start"""
        projects = self._get_all_projects()
        if not projects:
            console.print("[yellow]No projects found[/yellow]")
            return
            
        console.print("\n[cyan]Available projects:[/cyan]")
        for i, (name, path, type_) in enumerate(projects, 1):
            console.print(f"{i}. {name} ({type_})")
        
        choice = IntPrompt.ask("Select project", choices=[str(i) for i in range(1, len(projects)+1)])
        name, path, type_ = projects[choice-1]
        
        self.start_project(name, type_)

    def _get_all_projects(self) -> List[tuple]:
        """Get all projects (scripts and sites)"""
        projects = []
        
        # Script projects
        for project_dir in self.projects_dir.iterdir():
            if project_dir.is_dir() and (project_dir / 'docker-compose.yml').exists():
                projects.append((project_dir.name, project_dir, "script"))
        
        # Site projects  
        for site_dir in self.sites_dir.iterdir():
            if site_dir.is_dir() and (site_dir / 'docker-compose.yml').exists():
                projects.append((site_dir.name, site_dir, "website"))
                
        return projects

    def manage_sites(self):
        """Website management interface"""
        console.clear()
        console.print(Panel("🌐 Website Management", style="bold green"))
        
        console.print("\n[cyan]Actions:[/cyan]")
        console.print("1. List websites")
        console.print("2. Configure domain")
        console.print("3. SSL certificates")
        console.print("4. Nginx configuration")
        console.print("5. Back to main menu")
        
        choice = IntPrompt.ask("Choose action", choices=["1", "2", "3", "4", "5"])
        
        if choice == 5:
            return
        elif choice == 1:
            self._list_websites()
        elif choice == 2:
            self._configure_domain()
        elif choice == 3:
            self._manage_ssl()
        elif choice == 4:
            self._manage_nginx_config()

    def template_management(self):
        """Template management interface"""
        while True:
            console.clear()
            console.print(Panel("📦 Template Management", style="bold magenta"))
            
            console.print("\n[cyan]Actions:[/cyan]")
            console.print("1. List templates")
            console.print("2. Create new template")
            console.print("3. Edit template")
            console.print("4. Delete template")
            console.print("5. Import template")
            console.print("6. Export template")
            console.print("7. Back to main menu")
            
            choice = IntPrompt.ask("Choose action", choices=[str(i) for i in range(1, 8)])
            
            if choice == 7:
                break
            elif choice == 1:
                self.template_manager.list_templates()
                Prompt.ask("\nPress Enter to continue")
            elif choice == 2:
                self._create_template_wizard()
            elif choice == 3:
                self._edit_template()

    def infrastructure_management(self):
        """Infrastructure management interface"""
        console.clear()
        console.print(Panel("⚙️ Infrastructure Management", style="bold red"))
        
        console.print("\n[cyan]Actions:[/cyan]")
        console.print("1. Start infrastructure")
        console.print("2. Stop infrastructure")
        console.print("3. View status")
        console.print("4. Update services")
        console.print("5. Backup data")
        console.print("6. Restore data")
        console.print("7. Back to main menu")
        
        choice = IntPrompt.ask("Choose action", choices=[str(i) for i in range(1, 8)])
        
        if choice == 7:
            return
        elif choice == 1:
            self._start_infrastructure()
        elif choice == 3:
            self._show_infrastructure_status()

    def _start_infrastructure(self):
        """Start core infrastructure services"""
        infrastructure_path = Path.home() / 'infrastructure'
        
        if not infrastructure_path.exists():
            console.print("[yellow]Setting up infrastructure for the first time...[/yellow]")
            self._setup_infrastructure()
        
        os.chdir(infrastructure_path)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Starting infrastructure...", total=None)
            
            try:
                subprocess.run(['docker-compose', 'up', '-d'], check=True, capture_output=True)
                progress.update(task, description="✅ Infrastructure started!")
                
                console.print(Panel.fit(
                    "[green]🚀 Infrastructure is running![/green]\n\n"
                    "• Nginx Proxy Manager: http://localhost:81\n"
                    "• Traefik Dashboard: http://localhost:8080\n"
                    "• Portainer: http://localhost:9000\n"
                    "• Code Server: http://localhost:8080",
                    title="Infrastructure Ready"
                ))
                
            except subprocess.CalledProcessError as e:
                console.print(f"[red]Failed to start infrastructure: {e}[/red]")
        
        Prompt.ask("\nPress Enter to continue")

if __name__ == "__main__":
    manager = DevManager()
    manager.show_main_menu()
