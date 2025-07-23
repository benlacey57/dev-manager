#!/usr/bin/env python3
# tasks/docker.py - Docker installation

import subprocess
from rich.console import Console

console = Console()

def run(config: dict, setup_dir) -> bool:
    """Install Docker and Docker Compose"""
    if not config.get('install_docker', True):
        return True
    
    try:
        # Add Docker repository
        subprocess.run([
            'curl', '-fsSL', 'https://download.docker.com/linux/ubuntu/gpg'
        ], check=True, stdout=open('/tmp/docker.gpg', 'wb'))
        
        subprocess.run([
            'gpg', '--dearmor', '-o', '/usr/share/keyrings/docker.gpg'
        ], check=True, stdin=open('/tmp/docker.gpg', 'rb'))
        
        # Add repository
        lsb_release = subprocess.run(['lsb_release', '-cs'], 
                                   capture_output=True, text=True).stdout.strip()
        
        with open('/etc/apt/sources.list.d/docker.list', 'w') as f:
            f.write(f"deb [arch=amd64 signed-by=/usr/share/keyrings/docker.gpg] "
                   f"https://download.docker.com/linux/ubuntu {lsb_release} stable\n")
        
        # Install Docker
        subprocess.run(['apt', 'update'], check=True, capture_output=True)
        subprocess.run([
            'apt', 'install', '-y', 'docker-ce', 'docker-ce-cli', 
            'containerd.io', 'docker-compose-plugin'
        ], check=True, capture_output=True)
        
        # Add user to docker group
        subprocess.run(['usermod', '-aG', 'docker', config['username']], 
                     check=True, capture_output=True)
        
        # Enable Docker
        subprocess.run(['systemctl', 'enable', 'docker'], check=True, capture_output=True)
        subprocess.run(['systemctl', 'start', 'docker'], check=True, capture_output=True)
        
        return True
    except Exception as e:
        console.print(f"[red]Docker installation failed: {e}[/red]")
        return False
