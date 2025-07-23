#!/usr/bin/env python3
# tasks/dev_tools.py - Development tools installation

import subprocess
from rich.console import Console

console = Console()

def run(config: dict, setup_dir) -> bool:
    """Install development tools"""
    try:
        # Install Node.js
        subprocess.run([
            'curl', '-fsSL', 'https://deb.nodesource.com/setup_18.x'
        ], check=True, stdout=open('/tmp/nodejs.sh', 'wb'))
        subprocess.run(['bash', '/tmp/nodejs.sh'], check=True, capture_output=True)
        subprocess.run(['apt', 'install', '-y', 'nodejs'], check=True, capture_output=True)
        
        # Install PHP
        subprocess.run(['apt', 'install', '-y', 
                       'php8.2', 'php8.2-cli', 'php8.2-fpm', 'php8.2-mysql', 
                       'php8.2-zip', 'php8.2-gd', 'php8.2-mbstring'], 
                     check=True, capture_output=True)
        
        # Install Composer
        subprocess.run(['curl', '-sS', 'https://getcomposer.org/installer'], 
                     check=True, stdout=open('/tmp/composer.php', 'wb'))
        subprocess.run(['php', '/tmp/composer.php'], check=True, capture_output=True)
        subprocess.run(['mv', 'composer.phar', '/usr/local/bin/composer'], 
                     check=True, capture_output=True)
        subprocess.run(['chmod', '+x', '/usr/local/bin/composer'], 
                     check=True, capture_output=True)
        
        # Install VS Code Server
        subprocess.run(['curl', '-fsSL', 'https://code-server.dev/install.sh'], 
                     check=True, stdout=open('/tmp/code-server.sh', 'wb'))
        subprocess.run(['sh', '/tmp/code-server.sh'], check=True, capture_output=True)
        
        return True
    except Exception as e:
        console.print(f"[red]Development tools installation failed: {e}[/red]")
        return False
