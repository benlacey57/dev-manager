#!/usr/bin/env python3
# tasks/final.py - Final setup and configuration

import subprocess
from pathlib import Path
from rich.console import Console

console = Console()

def run(config: dict, setup_dir) -> bool:
    """Final configuration"""
    try:
        username = config['username']
        
        # Create basic dev manager script
        _create_dev_scripts(username, setup_dir)
        
        # Setup dotfiles if GitHub username provided
        if config.get('github_username'):
            _setup_dotfiles(username, config['github_username'])
        
        # Create welcome message
        _create_welcome(username, config)
        
        return True
    except Exception as e:
        console.print(f"[red]Final configuration failed: {e}[/red]")
        return False

def _create_dev_scripts(username: str, setup_dir):
    """Create basic development scripts"""
    scripts_dir = Path(f'/home/{username}/scripts')
    
    # Create basic 'dev' command
    dev_script = scripts_dir / 'dev'
    with open(dev_script, 'w') as f:
        f.write("""#!/bin/bash
echo "🚀 Development Environment Manager"
echo "Available commands:"
echo "  dev start    - Start infrastructure"
echo "  dev stop     - Stop infrastructure"
echo "  dev status   - Show status"
echo ""
case "$1" in
    start)
        cd ~/infrastructure && docker compose up -d
        ;;
    stop)
        cd ~/infrastructure && docker compose down
        ;;
    status)
        docker ps
        ;;
    *)
        echo "Usage: dev {start|stop|status}"
        ;;
esac
""")
    
    subprocess.run(['chmod', '+x', str(dev_script)], check=True)
    subprocess.run(['chown', f'{username}:{username}', str(dev_script)], check=True)
    
    # Create symlink
    subprocess.run(['ln', '-sf', str(dev_script), '/usr/local/bin/dev'], check=True)

def _setup_dotfiles(username: str, github_username: str):
    """Setup dotfiles from GitHub"""
    try:
        dotfiles_url = f"https://github.com/{github_username}/dotfiles"
        user_home = Path(f'/home/{username}')
        
        subprocess.run([
            'sudo', '-u', username, 'git', 'clone', 
            dotfiles_url, str(user_home / 'dotfiles')
        ], check=True, capture_output=True)
        
    except subprocess.CalledProcessError:
        console.print("[yellow]Could not clone dotfiles repository[/yellow]")

def _create_welcome(username: str, config: dict):
    """Create welcome message"""
    welcome_content = f"""
echo "🚀 Welcome to your Development Server!"
echo ""
echo "Quick commands:"
echo "  dev start    - Start infrastructure"
echo "  dev status   - Show running containers"
echo ""
echo "Web interfaces:"
echo "  http://localhost:81  - Nginx Proxy Manager"
echo "  http://localhost:9000 - Portainer"
echo "  http://localhost:8080 - VS Code Server"
echo ""
"""
    
    welcome_file = Path(f'/home/{username}/.welcome')
    with open(welcome_file, 'w') as f:
        f.write(welcome_content)
    
    # Add to .bashrc
    bashrc = Path(f'/home/{username}/.bashrc')
    with open(bashrc, 'a') as f:
        f.write('\n# Show welcome\nbash ~/.welcome\n')
    
    subprocess.run(['chown', f'{username}:{username}', str(welcome_file)], check=True)
