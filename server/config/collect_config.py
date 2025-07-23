#!/usr/bin/env python3

import yaml
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

console = Console()

class ConfigCollector:
    def __init__(self, setup_dir: Path):
        self.setup_dir = setup_dir
        self.defaults = self._load_defaults()
    
    def _load_defaults(self):
        """Load default configuration"""
        defaults_file = self.setup_dir / 'config' / 'defaults.yml'
        if defaults_file.exists():
            with open(defaults_file) as f:
                return yaml.safe_load(f)
        return {}
    
    def collect(self) -> dict:
        """Collect configuration from user"""
        console.print(Panel("📝 Configuration Setup", style="bold blue"))
        
        config = {}
        
        # Basic settings
        config['username'] = Prompt.ask("Username", default=self.defaults.get('username', 'developer'))
        config['email'] = Prompt.ask("Email", default=self.defaults.get('email', 'dev@example.com'))
        config['ssh_port'] = int(Prompt.ask("SSH Port", default=str(self.defaults.get('ssh_port', 22))))
        
        # SSH Key
        ssh_choice = Prompt.ask("SSH Key", choices=["generate", "paste"], default="generate")
        if ssh_choice == "generate":
            config['ssh_key_type'] = 'generate'
        else:
            config['ssh_key_type'] = 'paste'
            config['ssh_public_key'] = Prompt.ask("Paste your public SSH key")
        
        # Optional settings
        config['domain'] = Prompt.ask("Domain (optional)", default="")
        config['github_username'] = Prompt.ask("GitHub username (optional)", default="")
        
        # Simple yes/no options
        config['install_docker'] = Confirm.ask("Install Docker?", default=True)
        config['install_nginx'] = Confirm.ask("Install Nginx Proxy Manager?", default=True)
        config['setup_firewall'] = Confirm.ask("Setup firewall?", default=True)
        config['setup_backups'] = Confirm.ask("Setup backups?", default=True)
        
        # Show summary
        console.print("\n[cyan]Configuration Summary:[/cyan]")
        for key, value in config.items():
            if 'key' not in key.lower():  # Don't show SSH keys
                console.print(f"  {key}: {value}")
        
        if not Confirm.ask("\nProceed with setup?"):
            console.print("Setup cancelled.")
            exit(0)
        
        return config
