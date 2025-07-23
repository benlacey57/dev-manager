#!/usr/bin/env python3

import os
import subprocess
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm

console = Console()

class DotfilesManager:
    def __init__(self):
        self.dotfiles_repo = "https://github.com/benlacey57/dotfiles"
        self.dotfiles_dir = Path.home() / "dotfiles"
        
    def sync_dotfiles(self):
        """Sync dotfiles from GitHub repository"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            if self.dotfiles_dir.exists():
                task = progress.add_task("Updating dotfiles...", total=None)
                os.chdir(self.dotfiles_dir)
                subprocess.run(['git', 'pull'], check=True, capture_output=True)
            else:
                task = progress.add_task("Cloning dotfiles...", total=None)
                subprocess.run([
                    'git', 'clone', self.dotfiles_repo, str(self.dotfiles_dir)
                ], check=True, capture_output=True)
            
            progress.update(task, description="✅ Dotfiles synced!")
        
        console.print("[green]Dotfiles synced successfully![/green]")
        
        if Confirm.ask("Install/update dotfiles configuration?"):
            self.install_dotfiles()
    
    def install_dotfiles(self):
        """Install dotfiles configuration"""
        if not self.dotfiles_dir.exists():
            console.print("[red]Dotfiles not found. Run sync first.[/red]")
            return
        
        install_script = self.dotfiles_dir / "install.sh"
        
        if install_script.exists():
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Installing dotfiles...", total=None)
                
                os.chdir(self.dotfiles_dir)
                subprocess.run(['bash', 'install.sh'], check=True)
                
                progress.update(task, description="✅ Dotfiles installed!")
            
            console.print("[green]Dotfiles installed successfully![/green]")
            console.print("[cyan]Restart your terminal or run 'source ~/.zshrc' to apply changes[/cyan]")
        else:
            console.print("[red]Install script not found in dotfiles repository[/red]")
    
    def update_dotfiles_for_project(self, project_path: Path):
        """Update dotfiles with project-specific configurations"""
        # Create project-specific zsh config
        project_zshrc = project_path / ".zshrc"
        if not project_zshrc.exists():
            zshrc_content = f"""# Project-specific zsh configuration for {project_path.name}

# Load main dotfiles configuration
source ~/.zshrc

# Project aliases
alias proj='cd {project_path}'
alias start='docker-compose up -d'
alias stop='docker-compose down'
alias logs='docker-compose logs -f'
alias shell='docker-compose exec dev bash'
alias code-server='docker-compose exec dev code-server'

# Project environment
export PROJECT_PATH="{project_path}"
export PROJECT_NAME="{project_path.name}"

# Auto-start development environment function
start-dev() {{
    cd {project_path}
    docker-compose up -d
    echo "Development environment started!"
    echo "Code Server: http://localhost:8080"
    echo "Application: http://localhost:3000"
}}

stop-dev() {{
    cd {project_path}
    docker-compose down
    echo "Development environment stopped!"
}}
"""
            
            with open(project_zshrc, 'w') as f:
                f.write(zshrc_content)
            
            console.print(f"[green]Created project-specific .zshrc for {project_path.name}[/green]")
    
    def show_dotfiles_menu(self):
        """Show dotfiles management menu"""
        console.clear()
        console.print(Panel("📁 Dotfiles Management", style="bold green"))
        
        # Show current status
        if self.dotfiles_dir.exists():
            console.print("[green]✅ Dotfiles repository found[/green]")
            
            # Check if it's up to date
            os.chdir(self.dotfiles_dir)
            result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
            if result.stdout.strip():
                console.print("[yellow]⚠️  Local changes detected[/yellow]")
            else:
                console.print("[green]✅ Repository is clean[/green]")
        else:
            console.print("[red]❌ Dotfiles repository not found[/red]")
        
        console.print("\n[cyan]Actions:[/cyan]")
        console.print("1. Sync from GitHub")
        console.print("2. Install/Update dotfiles")
        console.print("3. Push local changes")
        console.print("4. View status")
        console.print("5. Edit configuration")
        console.print("6. Back to main menu")
        
        from rich.prompt import IntPrompt
        choice = IntPrompt.ask("Choose action", choices=["1", "2", "3", "4", "5", "6"])
        
        if choice == 6:
            return
        elif choice == 1:
            self.sync_dotfiles()
        elif choice == 2:
            self.install_dotfiles()
        elif choice == 3:
            self._push_changes()
        elif choice == 4:
            self._show_status()
        elif choice == 5:
            self._edit_configuration()
        
        from rich.prompt import Prompt
        Prompt.ask("\nPress Enter to continue")
    
    def _push_changes(self):
        """Push local dotfiles changes to GitHub"""
        if not self.dotfiles_dir.exists():
            console.print("[red]Dotfiles repository not found[/red]")
            return
        
        os.chdir(self.dotfiles_dir)
        
        # Check for changes
        result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
        if not result.stdout.strip():
            console.print("[yellow]No changes to push[/yellow]")
            return
        
        console.print("[cyan]Changes detected:[/cyan]")
        subprocess.run(['git', 'status', '--short'])
        
        if Confirm.ask("\nCommit and push changes?"):
            commit_message = console.input("[cyan]Commit message (or press Enter for default): [/cyan]") or "Update dotfiles configuration"
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Pushing changes...", total=None)
                
                subprocess.run(['git', 'add', '.'], check=True)
                subprocess.run(['git', 'commit', '-m', commit_message], check=True)
                subprocess.run(['git', 'push'], check=True)
                
                progress.update(task, description="✅ Changes pushed!")
            
            console.print("[green]Changes pushed to GitHub successfully![/green]")
    
    def _show_status(self):
        """Show dotfiles repository status"""
        if not self.dotfiles_dir.exists():
            console.print("[red]Dotfiles repository not found[/red]")
            return
        
        os.chdir(self.dotfiles_dir)
        
        console.print("[cyan]Repository Status:[/cyan]")
        subprocess.run(['git', 'status'])
        
        console.print("\n[cyan]Recent Commits:[/cyan]")
        subprocess.run(['git', 'log', '--oneline', '-5'])
    
    def _edit_configuration(self):
        """Open dotfiles for editing"""
        if not self.dotfiles_dir.exists():
            console.print("[red]Dotfiles repository not found[/red]")
            return
        
        console.print("[cyan]Opening dotfiles in VS Code...[/cyan]")
        subprocess.run(['code', str(self.dotfiles_dir)])
