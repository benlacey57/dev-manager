#!/usr/bin/env python3
# tasks/user.py - User creation and setup

import subprocess
from pathlib import Path
from rich.console import Console

console = Console()

def run(config: dict, setup_dir) -> bool:
    """Create and configure user"""
    try:
        username = config['username']
        
        # Check if user exists
        try:
            subprocess.run(['id', username], check=True, capture_output=True)
            console.print(f"[yellow]User {username} already exists[/yellow]")
        except subprocess.CalledProcessError:
            # Create user
            subprocess.run([
                'useradd', '-m', '-s', '/bin/bash', username
            ], check=True, capture_output=True)
            
            # Add to sudo group
            subprocess.run(['usermod', '-aG', 'sudo', username], check=True, capture_output=True)
        
        # Create directories
        user_home = Path(f'/home/{username}')
        directories = ['scripts', 'sites', 'docker', 'workspace', '.ssh']
        
        for directory in directories:
            dir_path = user_home / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            subprocess.run(['chown', f'{username}:{username}', str(dir_path)], 
                         check=True, capture_output=True)
        
        return True
    except subprocess.CalledProcessError as e:
        console.print(f"[red]User setup failed: {e}[/red]")
        return False
