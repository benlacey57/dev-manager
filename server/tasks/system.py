#!/usr/bin/env python3
# tasks/system.py - System updates and basic packages

import subprocess
from rich.console import Console

console = Console()

def run(config: dict, setup_dir) -> bool:
    """Update system and install basic packages"""
    try:
        # Update package lists
        subprocess.run(['apt', 'update'], check=True, capture_output=True)
        
        # Upgrade packages
        subprocess.run(['apt', 'upgrade', '-y'], check=True, capture_output=True)
        
        # Install essential packages
        packages = [
            'curl', 'wget', 'git', 'unzip', 'software-properties-common',
            'apt-transport-https', 'ca-certificates', 'gnupg', 'lsb-release',
            'build-essential', 'htop', 'tree', 'vim', 'nano', 'tmux', 'ufw',
            'fail2ban', 'python3-pip'
        ]
        
        subprocess.run(['apt', 'install', '-y'] + packages, check=True, capture_output=True)
        
        # Install Python packages for setup
        subprocess.run(['pip3', 'install', 'rich', 'pyyaml'], check=True, capture_output=True)
        
        return True
    except subprocess.CalledProcessError as e:
        console.print(f"[red]System setup failed: {e}[/red]")
        return False
