#!/usr/bin/env python3

import os
import sys
import importlib
from pathlib import Path
from typing import Dict, List
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config.collect_config import ConfigCollector
from tasks import (
    system, user, ssh, security, docker, 
    dev_tools, web_server, final
)

console = Console()

class ServerSetup:
    def __init__(self):
        self.setup_dir = Path(__file__).parent
        self.config = {}
        self.setup_log = []
        
    def run(self):
        """Run the complete setup process"""
        console.clear()
        console.print(Panel.fit(
            "[bold cyan]🚀 Development Server Setup[/bold cyan]\n\n"
            "[green]Simple, modular server setup for development environments[/green]",
            title="Server Setup"
        ))
        
        # Check root
        if os.geteuid() != 0:
            console.print("[red]This script must be run as root (use sudo)[/red]")
            sys.exit(1)
        
        # Collect configuration
        collector = ConfigCollector(self.setup_dir)
        self.config = collector.collect()
        
        # Run setup tasks
        self._run_setup_tasks()
        
        # Show summary
        self._show_summary()
    
    def _run_setup_tasks(self):
        """Run all setup tasks"""
        tasks = [
            ("System Updates", system.run),
            ("User Management", user.run),
            ("SSH Configuration", ssh.run),
            ("Security Setup", security.run),
            ("Docker Installation", docker.run),
            ("Development Tools", dev_tools.run),
            ("Web Infrastructure", web_server.run),
            ("Final Configuration", final.run)
        ]
        
        console.print(Panel("🔧 Running Setup Tasks", style="bold green"))
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            
            main_task = progress.add_task("Overall Progress", total=len(tasks))
            
            for task_name, task_func in tasks:
                current_task = progress.add_task(f"[cyan]{task_name}[/cyan]", total=1)
                
                try:
                    result = task_func(self.config, self.setup_dir)
                    if result:
                        progress.update(current_task, completed=1, 
                                      description=f"[green]✅ {task_name}[/green]")
                        self.setup_log.append(f"✅ {task_name}")
                    else:
                        progress.update(current_task, completed=1, 
                                      description=f"[yellow]⚠️ {task_name} (Skipped)[/yellow]")
                        self.setup_log.append(f"⚠️ {task_name}")
                
                except Exception as e:
                    progress.update(current_task, completed=1, 
                                  description=f"[red]❌ {task_name}[/red]")
                    self.setup_log.append(f"❌ {task_name}: {str(e)}")
                    console.print(f"[red]Error in {task_name}: {str(e)}[/red]")
                
                progress.update(main_task, advance=1)
    
    def _show_summary(self):
        """Show setup summary"""
        console.print(Panel.fit(
            f"[bold green]🎉 Setup Complete![/bold green]\n\n"
            f"[cyan]Server Details:[/cyan]\n"
            f"• User: {self.config['username']}\n"
            f"• SSH Port: {self.config['ssh_port']}\n"
            f"• Domain: {self.config.get('domain', 'Not set')}\n\n"
            f"[cyan]Access:[/cyan]\n"
            f"• SSH: ssh {self.config['username']}@your-server -p {self.config['ssh_port']}\n"
            f"• VS Code: http://your-server:8080\n"
            f"• Proxy Manager: http://your-server:81\n\n"
            f"[cyan]Commands:[/cyan]\n"
            f"• dev - Development manager\n"
            f"• new - Create projects",
            title="🚀 Development Server Ready"
        ))

if __name__ == "__main__":
    setup = ServerSetup()
    setup.run()
