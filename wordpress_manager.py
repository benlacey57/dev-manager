#!/usr/bin/env python3
# templates/wordpress_manager.py - WordPress project template manager

import os
import secrets
import string
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

class WordPressManager:
    def __init__(self, ssl_manager=None):
        self.ssl_manager = ssl_manager
        self.template_dir = Path(__file__).parent / 'wordpress'
    
    def create_wordpress_project(self, project_name: str, domain: str, 
                                ssl_enabled: bool = True) -> bool:
        """Create WordPress project with SSL"""
        try:
            # Create project directory
            if domain:
                project_path = Path.home() / 'sites' / domain
            else:
                project_path = Path.home() / 'scripts' / project_name
            
            project_path.mkdir(parents=True, exist_ok=True)
            
            # Generate secure passwords
            db_password = self._generate_password(16)
            db_root_password = self._generate_password(16)
            redis_password = self._generate_password(16)
            
            # Template variables
            variables = {
                'PROJECT_NAME': project_name,
                'DOMAIN': domain,
                'WP_VERSION': '6.4',
                'PHP_VERSION': '8.2',
                'MYSQL_VERSION': '8.0',
                'REDIS_VERSION': '7',
                'DB_PASSWORD': db_password,
                'DB_ROOT_PASSWORD': db_root_password,
                'REDIS_PASSWORD': redis_password,
                'WP_DEBUG': 'false',
                'AWS_ACCESS_KEY': '',
                'AWS_SECRET_KEY': ''
            }
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Creating WordPress project...", total=None)
                
                # Copy and process templates
                self._copy_template_files(project_path, variables)
                progress.update(task, description="✅ Templates copied")
                
                # Create project structure
                self._create_project_structure(project_path)
                progress.update(task, description="✅ Project structure created")
                
                # Start Docker containers
                if self._start_docker_containers(project_path):
                    progress.update(task, description="✅ Docker containers started")
                else:
                    progress.update(task, description="⚠️ Docker containers failed to start")
                
                # Setup SSL if requested and SSL manager available
                if ssl_enabled and domain and self.ssl_manager:
                    progress.update(task, description="🔒 Setting up SSL...")
                    ssl_success = self.ssl_manager.add_certificate(domain, 'letsencrypt', 'website')
                    if ssl_success:
                        progress.update(task, description="✅ SSL certificate configured")
                    else:
                        progress.update(task, description="⚠️ SSL setup failed")
                
                progress.update(task, description="🎉 WordPress project created successfully!")
            
            # Show project information
            self._show_project_info(project_name, domain, project_path, variables)
            
            return True
            
        except Exception as e:
            console.print(f"[red]Failed to create WordPress project: {e}[/red]")
            return False
    
    def _generate_password(self, length: int = 16) -> str:
        """Generate secure password"""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def _copy_template_files(self, project_path: Path, variables: dict):
        """Copy and process template files"""
        template_files = {
            'docker-compose.yml': self._get_docker_compose_template(),
            '.env': self._get_env_template(),
            'uploads.ini': self._get_uploads_ini_template(),
            'install-plugins.sh': self._get_install_plugins_template(),
            'nginx.conf': self._get_nginx_conf_template(),
            '.gitignore': self._get_gitignore_template()
        }
        
        for filename, template_content in template_files.items():
            file_path = project_path / filename
            
            # Replace template variables
            content = template_content
            for var, value in variables.items():
                content = content.replace(f'{{{{{var}}}}}', str(value))
            
            with open(file_path, 'w') as f:
                f.write(content)
            
            # Make shell scripts executable
            if filename.endswith('.sh'):
                file_path.chmod(0o755)
    
    def _create_project_structure(self, project_path: Path):
        """Create WordPress project directory structure"""
        directories = [
            'wordpress',
            'backups',
            'mysql-init',
            'logs'
        ]
        
        for directory in directories:
            (project_path / directory).mkdir(exist_ok=True)
        
        # Create initial MySQL setup script
        mysql_init = project_path / 'mysql-init' / 'init.sql'
        with open(mysql_init, 'w') as f:
            f.write("""-- WordPress Database Initialization
CREATE DATABASE IF NOT EXISTS wordpress;
GRANT ALL PRIVILEGES ON wordpress.* TO 'wordpress'@'%';
FLUSH PRIVILEGES;
""")
    
    def _start_docker_containers(self, project_path: Path) -> bool:
        """Start Docker containers"""
        try:
            import subprocess
            os.chdir(project_path)
            
            # Pull images first
            subprocess.run(['docker', 'compose', 'pull'], check=True, capture_output=True)
            
            # Start containers
            subprocess.run(['docker', 'compose', 'up', '-d'], check=True, capture_output=True)
            
            return True
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Docker startup failed: {e}[/red]")
            return False
    
    def _show_project_info(self, project_name: str, domain: str, project_path: Path, variables: dict):
        """Show project information"""
        from rich.panel import Panel
        
        info_text = f"[bold green]WordPress Project Created Successfully![/bold green]\n\n"
        info_text += f"[cyan]Project Details:[/cyan]\n"
        info_text += f"• Name: {project_name}\n"
        info_text += f"• Domain: {domain}\n"
        info_text += f"• Path: {project_path}\n\n"
        
        info_text += f"[cyan]Access URLs:[/cyan]\n"
        info_text += f"• WordPress: https://{domain} (or http://{domain})\n"
        info_text += f"• Admin: https://{domain}/wp-admin\n"
        info_text += f"• phpMyAdmin: https://pma.{domain}\n\n"
        
        info_text += f"[cyan]Database Credentials:[/cyan]\n"
        info_text += f"• Database: wordpress\n"
        info_text += f"• Username: wordpress\n"
        info_text += f"• Password: {variables['DB_PASSWORD']}\n\n"
        
        info_text += f"[cyan]Next Steps:[/cyan]\n"
        info_text += f"1. Visit https://{domain} to complete WordPress setup\n"
        info_text += f"2. Run: cd {project_path} && ./install-plugins.sh\n"
        info_text += f"3. Configure your WordPress admin account\n"
        info_text += f"4. Install additional plugins as needed"
        
        console.print(Panel.fit(info_text, title="🎉 WordPress Ready"))
    
    def _get_docker_compose_template(self) -> str:
        """Get Docker Compose template"""
        return '''version: '3.8'

services:
  wordpress:
    image: wordpress:{{WP_VERSION}}-php{{PHP_VERSION}}-apache
    container_name: {{PROJECT_NAME}}-wordpress
    restart: unless-stopped
    environment:
      WORDPRESS_DB_HOST: db
      WORDPRESS_DB_USER: wordpress
      WORDPRESS_DB_PASSWORD: {{DB_PASSWORD}}
      WORDPRESS_DB_NAME: wordpress
      WORDPRESS_CONFIG_EXTRA: |
        define('WP_DEBUG', {{WP_DEBUG}});
        define('WP_DEBUG_LOG', {{WP_DEBUG}});
        define('FORCE_SSL_ADMIN', true);
        if ($$_SERVER['HTTP_X_FORWARDED_PROTO'] == 'https') {
          $$_SERVER['HTTPS'] = 'on';
        }
        define('WP_REDIS_HOST', 'redis');
        define('WP_REDIS_PORT', 6379);
        define('WP_REDIS_PASSWORD', '{{REDIS_PASSWORD}}');
    volumes:
      - ./wordpress:/var/www/html
      - ./uploads.ini:/usr/local/etc/php/conf.d/uploads.ini
    networks:
      - wordpress-network
      - proxy
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.{{PROJECT_NAME}}.rule=Host(`{{DOMAIN}}`)"
      - "traefik.http.routers.{{PROJECT_NAME}}.tls=true"
      - "traefik.http.routers.{{PROJECT_NAME}}.tls.certresolver=letsencrypt"
      - "traefik.http.services.{{PROJECT_NAME}}.loadbalancer.server.port=80"
      - "traefik.docker.network=proxy"
    depends_on:
      - db
      - redis

  db:
    image: mysql:{{MYSQL_VERSION}}
    container_name: {{PROJECT_NAME}}-db
    restart: unless-stopped
    environment:
      MYSQL_DATABASE: wordpress
      MYSQL_USER: wordpress
      MYSQL_PASSWORD: {{DB_PASSWORD}}
      MYSQL_ROOT_PASSWORD: {{DB_ROOT_PASSWORD}}
    volumes:
      - db_data:/var/lib/mysql
      - ./mysql-init:/docker-entrypoint-initdb.d
    networks:
      - wordpress-network
    command: '--default-authentication-plugin=mysql_native_password'

  phpmyadmin:
    image: phpmyadmin/phpmyadmin:latest
    container_name: {{PROJECT_NAME}}-phpmyadmin
    restart: unless-stopped
    environment:
      PMA_HOST: db
      PMA_USER: wordpress
      PMA_PASSWORD: {{DB_PASSWORD}}
      UPLOAD_LIMIT: 100M
    networks:
      - wordpress-network
      - proxy
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.{{PROJECT_NAME}}-pma.rule=Host(`pma.{{DOMAIN}}`)"
      - "traefik.http.routers.{{PROJECT_NAME}}-pma.tls=true"
      - "traefik.http.routers.{{PROJECT_NAME}}-pma.tls.certresolver=letsencrypt"
      - "traefik.http.services.{{PROJECT_NAME}}-pma.loadbalancer.server.port=80"
    depends_on:
      - db

  redis:
    image: redis:{{REDIS_VERSION}}-alpine
    container_name: {{PROJECT_NAME}}-redis
    restart: unless-stopped
    command: redis-server --appendonly yes --requirepass {{REDIS_PASSWORD}}
    volumes:
      - redis_data:/data
    networks:
      - wordpress-network

networks:
  wordpress-network:
    driver: bridge
  proxy:
    external: true

volumes:
  db_data:
  redis_data:
'''

    def _get_env_template(self) -> str:
        """Get .env template"""
        return '''# WordPress Configuration
PROJECT_NAME={{PROJECT_NAME}}
DOMAIN={{DOMAIN}}
WP_VERSION={{WP_VERSION}}
PHP_VERSION={{PHP_VERSION}}
MYSQL_VERSION={{MYSQL_VERSION}}
REDIS_VERSION={{REDIS_VERSION}}

# Security
DB_PASSWORD={{DB_PASSWORD}}
DB_ROOT_PASSWORD={{DB_ROOT_PASSWORD}}
REDIS_PASSWORD={{REDIS_PASSWORD}}

# WordPress Settings
WP_DEBUG={{WP_DEBUG}}

# SSL Settings
SSL_ENABLED=true
FORCE_SSL=true
'''

    def _get_uploads_ini_template(self) -> str:
        """Get PHP uploads configuration"""
        return '''file_uploads = On
memory_limit = 512M
upload_max_filesize = 100M
post_max_size = 100M
max_execution_time = 300
max_input_vars = 3000
max_input_time = 300
'''

    def _get_install_plugins_template(self) -> str:
        """Get plugin installation script"""
        return '''#!/bin/bash
# WordPress plugin installation script

set -euo pipefail

CONTAINER_NAME="{{PROJECT_NAME}}-wordpress"

# Essential plugins
PLUGINS=(
    "redis-cache"
    "wordfence"
    "updraftplus"
    "wp-super-cache"
    "yoast-seo"
    "elementor"
    "contact-form-7"
    "akismet"
    "wp-optimize"
    "duplicate-post"
)

echo "🔧 Installing WordPress plugins..."

# Wait for WordPress to be ready
echo "⏳ Waiting for WordPress to be ready..."
sleep 30

for plugin in "${PLUGINS[@]}"; do
    echo "Installing: $plugin"
    docker exec $CONTAINER_NAME wp plugin install $plugin --activate --allow-root || echo "Failed to install $plugin"
done

# Configure Redis
echo "🔧 Configuring Redis cache..."
docker exec $CONTAINER_NAME wp config set WP_REDIS_HOST "redis" --allow-root
docker exec $CONTAINER_NAME wp config set WP_REDIS_PORT 6379 --allow-root
docker exec $CONTAINER_NAME wp config set WP_REDIS_PASSWORD "{{REDIS_PASSWORD}}" --allow-root
docker exec $CONTAINER_NAME wp redis enable --allow-root || echo "Redis configuration failed"

# Set basic WordPress settings
echo "🔧 Configuring WordPress settings..."
docker exec $CONTAINER_NAME wp option update blogname "{{PROJECT_NAME}}" --allow-root || echo "Failed to set blog name"
docker exec $CONTAINER_NAME wp option update siteurl "https://{{DOMAIN}}" --allow-root || echo "Failed to set site URL"
docker exec $CONTAINER_NAME wp option update home "https://{{DOMAIN}}" --allow-root || echo "Failed to set home URL"

# Configure permalinks
docker exec $CONTAINER_NAME wp rewrite structure '/%postname%/' --allow-root || echo "Failed to set permalinks"

echo "✅ WordPress setup complete!"
echo "🌐 Site: https://{{DOMAIN}}"
echo "🗄️  Database: https://pma.{{DOMAIN}}"
echo ""
echo "Next steps:"
echo "1. Visit https://{{DOMAIN}} to complete WordPress installation"
echo "2. Create your admin user account"
echo "3. Configure your site settings"
'''

    def _get_nginx_conf_template(self) -> str:
        """Get Nginx configuration template"""
        return '''# WordPress optimized Nginx configuration
server {
    listen 80;
    server_name {{DOMAIN}} www.{{DOMAIN}};
    root /var/www/html;
    index index.php index.html;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types
        application/atom+xml
        application/javascript
        application/json
        application/rss+xml
        application/vnd.ms-fontobject
        application/x-font-ttf
        application/x-web-app-manifest+json
        application/xhtml+xml
        application/xml
        font/opentype
        image/svg+xml
        image/x-icon
        text/css
        text/plain
        text/x-component;

    # Cache static files
    location ~* \\.(jpg|jpeg|png|gif|ico|css|js|pdf|txt)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # WordPress security
    location = /favicon.ico { 
        log_not_found off; 
        access_log off; 
    }
    
    location = /robots.txt { 
        log_not_found off; 
        access_log off; 
        allow all; 
    }
    
    location ~* /(?:uploads|files)/.*\\.php$ {
        deny all;
    }
    
    location ~ /\\. {
        deny all;
    }
    
    location ~ ~$ {
        deny all;
    }

    # WordPress permalinks
    location / {
        try_files $uri $uri/ /index.php?$args;
    }

    # PHP processing
    location ~ \\.php$ {
        try_files $uri =404;
        fastcgi_split_path_info ^(.+\\.php)(/.+)$;
        fastcgi_pass wordpress:9000;
        fastcgi_index index.php;
        include fastcgi_params;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        fastcgi_param PATH_INFO $fastcgi_path_info;
        
        # WordPress specific
        fastcgi_param HTTP_PROXY "";
        fastcgi_buffers 16 16k;
        fastcgi_buffer_size 32k;
        fastcgi_read_timeout 300;
    }
}
'''

    def _get_gitignore_template(self) -> str:
        """Get .gitignore template"""
        return '''# WordPress
/wordpress/wp-config.php
/wordpress/wp-content/uploads/
/wordpress/wp-content/cache/
/wordpress/wp-content/upgrade/
/wordpress/wp-content/backup-db/
/wordpress/wp-content/advanced-cache.php
/wordpress/wp-content/wp-cache-config.php
/wordpress/wp-content/blogs.dir/
/wordpress/wp-content/debug.log

# Environment files
.env
.env.local
.env.*.local

# Docker
docker-compose.override.yml

# Logs
logs/
*.log

# Backups
backups/
*.sql
*.zip

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# IDE
.vscode/
.idea/
*.swp
*.swo

# Database
db_data/
mysql_data/
redis_data/
'''
