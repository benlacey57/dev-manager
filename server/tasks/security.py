#!/usr/bin/env python3
# tasks/security.py - Security hardening

import subprocess
from rich.console import Console

console = Console()

def run(config: dict, setup_dir) -> bool:
    """Setup security measures"""
    try:
        # Configure Fail2Ban
        fail2ban_config = f"""[DEFAULT]
bantime = 1h
findtime = 10m
maxretry = 3

[sshd]
enabled = true
port = {config['ssh_port']}
"""
        
        with open('/etc/fail2ban/jail.local', 'w') as f:
            f.write(fail2ban_config)
        
        subprocess.run(['systemctl', 'enable', 'fail2ban'], check=True, capture_output=True)
        subprocess.run(['systemctl', 'start', 'fail2ban'], check=True, capture_output=True)
        
        # Setup firewall if requested
        if config.get('setup_firewall', True):
            _setup_firewall(config)
        
        return True
    except Exception as e:
        console.print(f"[red]Security setup failed: {e}[/red]")
        return False

def _setup_firewall(config: dict):
    """Setup UFW firewall"""
    subprocess.run(['ufw', '--force', 'reset'], check=True, capture_output=True)
    subprocess.run(['ufw', 'default', 'deny', 'incoming'], check=True, capture_output=True)
    subprocess.run(['ufw', 'default', 'allow', 'outgoing'], check=True, capture_output=True)
    
    # Allow necessary ports
    ports = [str(config['ssh_port']), '80', '443', '8080', '81', '9000']
    for port in ports:
        subprocess.run(['ufw', 'allow', port], check=True, capture_output=True)
    
    subprocess.run(['ufw', '--force', 'enable'], check=True, capture_output=True)
