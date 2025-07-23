#!/usr/bin/env python3
# tasks/web_server.py - Web infrastructure setup

import subprocess
from pathlib import Path
from rich.console import Console

console = Console()

def run(config: dict, setup_dir) -> bool:
    """Setup web infrastructure"""
    if not config.get('install_nginx', True):
        return True
    
    try:
        username = config['username']
        infra_dir = Path(f'/home/{username}/infrastructure')
        infra_dir.mkdir(exist_ok=True)
        
        # Copy docker-compose template
        template_file = setup_dir / 'templates' / 'docker-compose.yml'
        target_file = infra_dir / 'docker-compose.yml'
        
        if template_file.exists():
            import shutil
            shutil.copy(template_file, target_file)
        else:
            # Create basic compose file
            _create_basic_compose(target_file)
        
        # Set ownership
        subprocess.run(['chown', '-R', f'{username}:{username}', str(infra_dir)], 
                     check=True, capture_output=True)
        
        return True
    except Exception as e:
        console.print(f"[red]Web server setup failed: {e}[/red]")
        return False

def _create_basic_compose(target_file: Path):
    """Create basic docker-compose.yml"""
    compose_content = """version: '3.8'

services:
  nginx-proxy-manager:
    image: 'jc21/nginx-proxy-manager:latest'
    restart: unless-stopped
    ports:
      - '81:81'
      - '443:443'
    volumes:
      - ./data:/data
      - ./letsencrypt:/etc/letsencrypt

  portainer:
    image: portainer/portainer-ce:latest
    restart: unless-stopped
    ports:
      - "9000:9000"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./portainer:/data
"""
    
    with open(target_file, 'w') as f:
        f.write(compose_content)
