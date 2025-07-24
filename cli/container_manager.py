#!/usr/bin/env python3
# cli/container_manager.py - Container management

from rich.console import Console
from rich.prompt import Prompt

console = Console()

class ContainerManager:
    def __init__(self):
        pass
    
    def manage_containers(self):
        """Container management interface"""
        console.print("[yellow]Container management coming soon![/yellow]")
        Prompt.ask("\nPress Enter to continue")
