#!/usr/bin/env python3
# tasks/ssh.py - SSH setup and configuration

import subprocess
from pathlib import Path
from rich.console import Console

console = Console()

def run(config: dict, setup_dir) -> bool:
    """Setup SSH configuration"""
    try:
        username = config['username']
        user_home = Path(f'/home/{username}')
        ssh_dir = user_home / '.ssh'
        
        # Setup SSH directory
        ssh_dir.mkdir(mode=0o700, exist_ok=True)
        
        # Handle SSH key
        if config['ssh_key_type'] == 'generate':
            # Generate SSH key
            key_path = ssh_dir / 'id_rsa'
            subprocess.run([
                'ssh-keygen', '-t', 'rsa', '-b', '4096',
                '-f', str(key_path), '-N', '', '-C', f'{username}@server'
            ], check=True, capture_output=True)
            
            # Read public key
            with open(f'{key_path}.pub') as f:
                public_key = f.read().strip()
        else:
            public_key = config['ssh_public_key']
        
        # Setup authorized_keys
        auth_keys = ssh_dir / 'authorized_keys'
        with open(auth_keys, 'w') as f:
            f.write(public_key + '\n')
        
        # Set permissions
        subprocess.run(['chmod', '600', str(auth_keys)], check=True)
        subprocess.run(['chown', '-R', f'{username}:{username}', str(ssh_dir)], check=True)
        
        # Configure SSH daemon
        _configure_sshd(config)
        
        return True
    except Exception as e:
        console.print(f"[red]SSH setup failed: {e}[/red]")
        return False

def _configure_sshd(config: dict):
    """Configure SSH daemon"""
    sshd_config = f"""
# Custom SSH Configuration
Port {config['ssh_port']}
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
X11Forwarding no
AllowUsers {config['username']}
"""
    
    with open('/etc/ssh/sshd_config', 'a') as f:
        f.write(sshd_config)
    
    # Restart SSH
    subprocess.run(['systemctl', 'restart', 'sshd'], check=True, capture_output=True)
