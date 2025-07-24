#!/usr/bin/env python3
# cli/main_menu.py - Main menu interface

from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.prompt import IntPrompt

from .project_manager import ProjectManager
from .ssl_manager import SSLManager
from .version_manager import VersionManager
from .dotfiles_manager import DotfilesManager
from .container_manager import ContainerManager

console = Console()

class DevManager:
    def __init__(self):
        self.project_manager = ProjectManager()
        self.ssl_manager = SSLManager()
        self.version_manager = VersionManager()
        self.dotfiles_manager = DotfilesManager()
        self.container_manager = ContainerManager()
        
    def show_main_menu(self):
        """Display main interactive menu"""
        while True:
            console.clear()
            console.print(Panel.fit(
                "[bold cyan]🚀 Development Environment Manager[/bold cyan]\n\n"
                "[green]Quick Commands:[/green]\n"
                "• [cyan]new[/cyan] - Create new project\n"
                "• [cyan]ssl[/cyan] - Manage SSL certificates\n"
                "• [cyan]versions[/cyan] - Manage tool versions\n"
                "• [cyan]dotfiles[/cyan] - Sync dotfiles\n\n"
                "[green]Choose an action:[/green]",
                title="Dev Manager"
            ))
            
            options = [
                "🆕 Create New Project",
                "📋 List Projects", 
                "🐳 Manage Containers",
                "🌐 Manage Sites",
                "🔒 SSL Certificate Manager",
                "📦 Template Management",
                "🔧 Version Management",
                "📁 Dotfiles Management",
                "⚙️  Infrastructure",
                "❌ Exit"
            ]
            
            for i, option in enumerate(options, 1):
                console.print(f"  {i}. {option}")
            
            choice = IntPrompt.ask("\nEnter your choice", choices=[str(i) for i in range(1, len(options)+1)])
            
            if choice == 1:
                self.project_manager.new_project_wizard()
            elif choice == 2:
                self.project_manager.list_projects()
            elif choice == 3:
                self.container_manager.manage_containers()
            elif choice == 4:
                self.project_manager.manage_sites()
            elif choice == 5:
                self.ssl_manager.show_ssl_menu()
            elif choice == 6:
                self.project_manager.template_management()
            elif choice == 7:
                self.version_manager.show_version_management_menu()
            elif choice == 8:
                self.dotfiles_manager.show_dotfiles_menu()
            elif choice == 9:
                self.infrastructure_management()
            elif choice == 10:
                console.print("[yellow]Goodbye![/yellow]")
                break
    
    def infrastructure_management(self):
        """Infrastructure management placeholder"""
        console.print("[yellow]Infrastructure management coming soon![/yellow]")
        from rich.prompt import Prompt
        Prompt.ask("\nPress Enter to continue")
