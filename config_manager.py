#!/usr/bin/env python3

import yaml
import json
from pathlib import Path
from typing import Dict, Any
from rich.console import Console

console = Console()

class ConfigManager:
    def __init__(self):
        self.config_dir = Path.home() / 'config'
        self.config_dir.mkdir(exist_ok=True)
        
    def get_default_configs(self) -> Dict[str, Dict]:
        """Get centralized default configurations"""
        return {
            'nginx': {
                'gzip': 'on',
                'gzip_vary': 'on',
                'gzip_min_length': 1024,
                'gzip_types': [
                    'text/plain',
                    'text/css',
                    'text/xml',
                    'text/javascript',
                    'application/javascript',
                    'application/xml+rss',
                    'application/json'
                ],
                'client_max_body_size': '100M',
                'proxy_cache_valid': '200 302 10m',
                'proxy_cache_valid_404': '1m'
            },
            'ssl': {
                'protocols': 'TLSv1.2 TLSv1.3',
                'ciphers': 'ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS',
                'prefer_server_ciphers': 'off',
                'session_cache': 'shared:SSL:10m',
                'session_timeout': '10m'
            },
            'docker': {
                'restart_policy': 'unless-stopped',
                'logging': {
                    'driver': 'json-file',
                    'options': {
                        'max-size': '10m',
                        'max-file': '3'
                    }
                },
                'networks': ['dev-network'],
                'security_opt': ['no-new-privileges:true']
            },
            'development': {
                'hot_reload': {
                    'enabled': True,
                    'debounce': 2,
                    'extensions': ['.py', '.js', '.ts', '.vue', '.php', '.html', '.css']
                },
                'code_server': {
                    'bind_addr': '0.0.0.0:8080',
                    'auth': 'password',
                    'disable_telemetry': True,
                    'extensions': {
                        'python': [
                            'ms-python.python',
                            'ms-python.pylint',
                            'ms-python.black-formatter'
                        ],
                        'javascript': [
                            'bradlc.vscode-tailwindcss',
                            'esbenp.prettier-vscode'
                        ],
                        'php': [
                            'bmewburn.vscode-intelephense-client',
                            'xdebug.php-debug'
                        ]
                    }
                }
            }
        }
        
    def apply_config_to_project(self, project_path: Path, template_name: str):
        """Apply default configurations to a new project"""
        defaults = self.get_default_configs()
        
        # Create nginx config
        self._create_nginx_config(project_path, defaults['nginx'])
        
        # Create docker config
        self._update_docker_compose(project_path, defaults['docker'])
        
        # Create build config
        self._create_build_config(project_path, template_name, defaults['development'])
        
    def _create_nginx_config(self, project_path: Path, nginx_config: Dict):
        """Create optimized nginx configuration"""
        nginx_dir = project_path / 'nginx'
        nginx_dir.mkdir(exist_ok=True)
        
        config_content = f"""# Optimized nginx configuration
server {{
    listen 80;
    server_name _;
    root /var/www/html;
    index index.html index.php;

    # Gzip compression
    gzip {nginx_config['gzip']};
    gzip_vary {nginx_config['gzip_vary']};
    gzip_min_length {nginx_config['gzip_min_length']};
    gzip_types {' '.join(nginx_config['gzip_types'])};

    # File upload limit
    client_max_body_size {nginx_config['client_max_body_size']};

    # Static file caching
    location ~* \.(jpg|jpeg|png|gif|ico|css|js|pdf|txt)$ {{
        expires 1y;
        add_header Cache-Control "public, immutable";
    }}

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # PHP processing
    location ~ \.php$ {{
        try_files $uri =404;
        fastcgi_split_path_info ^(.+\.php)(/.+)$;
        fastcgi_pass dev:9000;
        fastcgi_index index.php;
        include fastcgi_params;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        fastcgi_param PATH_INFO $fastcgi_path_info;
    }}

    # SPA fallback
    location / {{
        try_files $uri $uri/ /index.html;
    }}
}}
"""
        
        with open(nginx_dir / 'default.conf', 'w') as f:
            f.write(config_content)
