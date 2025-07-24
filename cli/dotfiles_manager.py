#!/usr/bin/env python3
# cli/dotfiles_manager.py - Dotfiles management

from rich.console import Console
from rich.prompt import Prompt

console = Console()

class DotfilesManager:
    def __init__(self):
        pass
    
    def show_dotfiles_menu(self):
        """Show dotfiles management menu"""
        console.print("[yellow]Dotfiles management coming soon![/yellow]")
        Prompt.ask("\nPress Enter to continue")
