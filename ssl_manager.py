#!/usr/bin/env python3
# ssl_manager.py - SSL Certificate Manager with menu interface

import os
import sys
import json
import yaml
import subprocess
import time
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import docker
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.progress import Progress, SpinnerColumn, TextColumn
import requests

console = Console()

class SSLManager:
    def __init__(self):
        self.data_dir = Path.home() / '.ssl-manager'
        self.data_dir.mkdir(exist_ok=True)
        self.db_path = self.data_dir / 'ssl_manager.db'
        self.config_path = self.data_dir / 'config.yml'
        
        try:
            self.docker_client = docker.from_env()
        except Exception as e:
            console.print(f"[yellow]Docker not available: {e}[/yellow]")
            self.docker_client = None
            
        self.init_database()
        self.load_config()
    
    def init_database(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS certificates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT UNIQUE NOT NULL,
                type TEXT NOT NULL,
                status TEXT NOT NULL,
                issued_date TEXT,
                expiry_date TEXT,
                auto_renew BOOLEAN DEFAULT 1,
                service_type TEXT,
                container_name TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS renewal_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT NOT NULL,
                action TEXT NOT NULL,
                status TEXT NOT NULL,
                message TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def load_config(self):
        """Load configuration"""
        default_config = {
            'letsencrypt': {
                'email': 'admin@example.com',
                'staging': False,
                'key_type': 'rsa2048'
            },
            'notifications': {
                'enabled': True,
                'email': 'admin@example.com',
                'renewal_days_before': 30
            },
            'docker': {
                'traefik_container': 'traefik',
                'nginx_container': 'nginx-proxy-manager'
            },
            'backup': {
                'enabled': True,
                'retention_days': 90,
                'backup_path': str(self.data_dir / 'backups')
            }
        }
        
        if self.config_path.exists():
            with open(self.config_path) as f:
                self.config = yaml.safe_load(f) or default_config
        else:
            self.config = default_config
            self.save_config()
    
    def save_config(self):
        """Save configuration"""
        with open(self.config_path, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)
    
    def show_ssl_menu(self):
        """Show SSL management interactive menu"""
        while True:
            console.clear()
            console.print(Panel("🔒 SSL Certificate Manager", style="bold green"))
            
            # Show certificate overview
            certificates = self.get_certificates()
            if certificates:
                self._show_certificate_overview(certificates)
            else:
                console.print("[yellow]No certificates configured[/yellow]")
            
            console.print("\n[cyan]Actions:[/cyan]")
            console.print("1. Add new certificate")
            console.print("2. List all certificates")
            console.print("3. Renew certificates")
            console.print("4. Delete certificate")
            console.print("5. Check certificate status")
            console.print("6. Configuration settings")
            console.print("7. View renewal logs")
            console.print("8. Back to main menu")
            
            choice = IntPrompt.ask("Choose action", choices=["1", "2", "3", "4", "5", "6", "7", "8"])
            
            if choice == 8:
                break
            elif choice == 1:
                self._add_certificate_interactive()
            elif choice == 2:
                self._list_certificates_interactive()
            elif choice == 3:
                self._renew_certificates_interactive()
            elif choice == 4:
                self._delete_certificate_interactive()
            elif choice == 5:
                self._check_certificate_status_interactive()
            elif choice == 6:
                self._configuration_menu()
            elif choice == 7:
                self._view_renewal_logs()
    
    def _show_certificate_overview(self, certificates: List[Dict]):
        """Show quick certificate overview"""
        active = sum(1 for cert in certificates if cert['status'] == 'active')
        pending = sum(1 for cert in certificates if cert['status'] == 'pending')
        failed = sum(1 for cert in certificates if cert['status'] == 'failed')
        
        console.print(f"\n[green]Active: {active}[/green] | [yellow]Pending: {pending}[/yellow] | [red]Failed: {failed}[/red]")

    def _add_certificate_interactive(self):
        """Interactive certificate addition"""
        console.clear()
        console.print(Panel("🆕 Add New Certificate", style="bold blue"))
        
        domain = Prompt.ask("Domain name (e.g., example.com)")
        
        cert_type = Prompt.ask(
            "Certificate type",
            choices=["letsencrypt", "self-signed"],
            default="letsencrypt"
        )
        
        service_type = Prompt.ask(
            "Service type",
            choices=["website", "api", "docker", "other"],
            default="website"
        )
        
        container_name = ""
        if service_type == "docker":
            container_name = Prompt.ask("Container name (optional)", default="")
        
        console.print(f"\n[cyan]Certificate Details:[/cyan]")
        console.print(f"Domain: {domain}")
        console.print(f"Type: {cert_type}")
        console.print(f"Service: {service_type}")
        if container_name:
            console.print(f"Container: {container_name}")
        
        if Confirm.ask("\nAdd this certificate?"):
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Adding certificate...", total=None)
                
                success = self.add_certificate(domain, cert_type, service_type, container_name)
                
                if success:
                    progress.update(task, description="✅ Certificate added successfully!")
                    console.print(f"\n[green]Certificate added for {domain}[/green]")
                else:
                    progress.update(task, description="❌ Certificate addition failed")
                    console.print(f"\n[red]Failed to add certificate for {domain}[/red]")
        
        Prompt.ask("\nPress Enter to continue")
    
    def _list_certificates_interactive(self):
        """Interactive certificate listing"""
        console.clear()
        console.print(Panel("📋 Certificate List", style="bold blue"))
        
        certificates = self.get_certificates()
        
        if not certificates:
            console.print("[yellow]No certificates found[/yellow]")
            Prompt.ask("\nPress Enter to continue")
            return
        
        table = Table()
        table.add_column("Domain", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Status", style="yellow")
        table.add_column("Expires", style="magenta")
        table.add_column("Auto Renew", style="blue")
        table.add_column("Service", style="white")
        
        for cert in certificates:
            status_color = {
                'active': '[green]●[/green]',
                'pending': '[yellow]●[/yellow]',
                'failed': '[red]●[/red]'
            }.get(cert['status'], '[gray]●[/gray]')
            
            expiry = cert['expiry_date'] or 'Unknown'
            auto_renew = '✅' if cert['auto_renew'] else '❌'
            
            table.add_row(
                cert['domain'],
                cert['type'],
                f"{status_color} {cert['status']}",
                expiry,
                auto_renew,
                cert['service_type']
            )
        
        console.print(table)
        Prompt.ask("\nPress Enter to continue")
    
    def _renew_certificates_interactive(self):
        """Interactive certificate renewal"""
        console.clear()
        console.print(Panel("🔄 Certificate Renewal", style="bold yellow"))
        
        certificates = self.get_certificates()
        renewable_certs = [cert for cert in certificates if cert['status'] == 'active']
        
        if not renewable_certs:
            console.print("[yellow]No certificates available for renewal[/yellow]")
            Prompt.ask("\nPress Enter to continue")
            return
        
        console.print(f"Found {len(renewable_certs)} certificates that can be renewed:")
        for cert in renewable_certs:
            console.print(f"  • {cert['domain']} (expires: {cert['expiry_date'] or 'Unknown'})")
        
        if Confirm.ask("\nRenew all certificates?"):
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Renewing certificates...", total=None)
                
                results = self.renew_certificates()
                
                success_count = sum(1 for success in results.values() if success)
                total_count = len(results)
                
                progress.update(task, description=f"✅ Renewed {success_count}/{total_count} certificates")
                
                console.print(f"\n[green]Successfully renewed {success_count} out of {total_count} certificates[/green]")
                
                if success_count < total_count:
                    console.print("\n[yellow]Failed renewals:[/yellow]")
                    for domain, success in results.items():
                        if not success:
                            console.print(f"  • {domain}")
        
        Prompt.ask("\nPress Enter to continue")
    
    def _delete_certificate_interactive(self):
        """Interactive certificate deletion"""
        console.clear()
        console.print(Panel("🗑️ Delete Certificate", style="bold red"))
        
        certificates = self.get_certificates()
        
        if not certificates:
            console.print("[yellow]No certificates to delete[/yellow]")
            Prompt.ask("\nPress Enter to continue")
            return
        
        console.print("[cyan]Available certificates:[/cyan]")
        for i, cert in enumerate(certificates, 1):
            console.print(f"{i}. {cert['domain']} ({cert['status']})")
        
        choice = IntPrompt.ask("Select certificate to delete", choices=[str(i) for i in range(1, len(certificates) + 1)])
        selected_cert = certificates[choice - 1]
        
        console.print(f"\n[red]⚠️ Warning: This will delete the certificate for {selected_cert['domain']}[/red]")
        
        if Confirm.ask("Are you sure you want to delete this certificate?"):
            success = self.delete_certificate(selected_cert['domain'])
            
            if success:
                console.print(f"[green]Certificate deleted for {selected_cert['domain']}[/green]")
            else:
                console.print(f"[red]Failed to delete certificate for {selected_cert['domain']}[/red]")
        
        Prompt.ask("\nPress Enter to continue")
    
    def _check_certificate_status_interactive(self):
        """Interactive certificate status check"""
        console.clear()
        console.print(Panel("🔍 Certificate Status Check", style="bold blue"))
        
        certificates = self.get_certificates()
        
        if not certificates:
            console.print("[yellow]No certificates to check[/yellow]")
            Prompt.ask("\nPress Enter to continue")
            return
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Checking certificate status...", total=len(certificates))
            
            for cert in certificates:
                progress.update(task, description=f"Checking {cert['domain']}...")
                
                # Check certificate status
                status = self._check_domain_ssl_status(cert['domain'])
                
                if status != cert['status']:
                    self._update_certificate_status(cert['domain'], status)
                
                progress.advance(task)
        
        console.print("[green]✅ Certificate status check completed[/green]")
        Prompt.ask("\nPress Enter to continue")
    
    def _configuration_menu(self):
        """Configuration settings menu"""
        while True:
            console.clear()
            console.print(Panel("⚙️ SSL Manager Configuration", style="bold cyan"))
            
            console.print(f"[cyan]Current Settings:[/cyan]")
            console.print(f"Let's Encrypt Email: {self.config['letsencrypt']['email']}")
            console.print(f"Staging Mode: {self.config['letsencrypt']['staging']}")
            console.print(f"Renewal Days Before: {self.config['notifications']['renewal_days_before']}")
            console.print(f"Traefik Container: {self.config['docker']['traefik_container']}")
            
            console.print("\n[cyan]Actions:[/cyan]")
            console.print("1. Update Let's Encrypt email")
            console.print("2. Toggle staging mode")
            console.print("3. Set renewal notification days")
            console.print("4. Update Docker container names")
            console.print("5. Back to SSL menu")
            
            choice = IntPrompt.ask("Choose action", choices=["1", "2", "3", "4", "5"])
            
            if choice == 5:
                break
            elif choice == 1:
                new_email = Prompt.ask("Enter Let's Encrypt email", default=self.config['letsencrypt']['email'])
                self.config['letsencrypt']['email'] = new_email
                self.save_config()
                console.print("[green]Email updated successfully[/green]")
            elif choice == 2:
                self.config['letsencrypt']['staging'] = not self.config['letsencrypt']['staging']
                self.save_config()
                status = "enabled" if self.config['letsencrypt']['staging'] else "disabled"
                console.print(f"[green]Staging mode {status}[/green]")
            elif choice == 3:
                days = IntPrompt.ask("Days before expiry to renew", default=self.config['notifications']['renewal_days_before'])
                self.config['notifications']['renewal_days_before'] = days
                self.save_config()
                console.print("[green]Renewal days updated[/green]")
            elif choice == 4:
                traefik = Prompt.ask("Traefik container name", default=self.config['docker']['traefik_container'])
                nginx = Prompt.ask("Nginx container name", default=self.config['docker']['nginx_container'])
                self.config['docker']['traefik_container'] = traefik
                self.config['docker']['nginx_container'] = nginx
                self.save_config()
                console.print("[green]Container names updated[/green]")
            
            Prompt.ask("\nPress Enter to continue")
    
    def _view_renewal_logs(self):
        """View renewal logs"""
        console.clear()
        console.print(Panel("📜 Renewal Logs", style="bold magenta"))
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT domain, action, status, message, timestamp
            FROM renewal_logs
            ORDER BY timestamp DESC
            LIMIT 50
        ''')
        
        logs = cursor.fetchall()
        conn.close()
        
        if not logs:
            console.print("[yellow]No logs found[/yellow]")
        else:
            table = Table()
            table.add_column("Timestamp", style="cyan")
            table.add_column("Domain", style="green")
            table.add_column("Action", style="yellow")
            table.add_column("Status", style="magenta")
            table.add_column("Message", style="white")
            
            for log in logs:
                table.add_row(log[4], log[0], log[1], log[2], log[3] or "")
            
            console.print(table)
        
        Prompt.ask("\nPress Enter to continue")

    def add_certificate(self, domain: str, cert_type: str = 'letsencrypt', 
                       service_type: str = 'website', container_name: str = None) -> bool:
        """Add new certificate request"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO certificates 
                (domain, type, status, service_type, container_name, auto_renew)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (domain, cert_type, 'pending', service_type, container_name, True))
            
            conn.commit()
            conn.close()
            
            # Trigger certificate generation
            return self.generate_certificate(domain)
            
        except Exception as e:
            console.print(f"[red]Failed to add certificate for {domain}: {e}[/red]")
            return False
    
    def generate_certificate(self, domain: str) -> bool:
        """Generate SSL certificate"""
        try:
            console.print(f"[cyan]Generating certificate for {domain}...[/cyan]")
            
            # Check if Traefik is managing this domain
            if self._is_traefik_managed(domain):
                return self._generate_traefik_certificate(domain)
            else:
                return self._generate_standalone_certificate(domain)
                
        except Exception as e:
            console.print(f"[red]Certificate generation failed for {domain}: {e}[/red]")
            self._update_certificate_status(domain, 'failed', str(e))
            return False
    
    def _is_traefik_managed(self, domain: str) -> bool:
        """Check if domain is managed by Traefik"""
        if not self.docker_client:
            return False
            
        try:
            containers = self.docker_client.containers.list()
            for container in containers:
                labels = container.labels
                if 'traefik.enable' in labels and labels.get('traefik.enable') == 'true':
                    # Check router rules for this domain
                    for label_key, label_value in labels.items():
                        if 'traefik.http.routers.' in label_key and '.rule' in label_key:
                            if f'Host(`{domain}`)' in label_value:
                                return True
            return False
        except Exception:
            return False
    
    def _generate_traefik_certificate(self, domain: str) -> bool:
        """Generate certificate through Traefik"""
        try:
            traefik_container = self.config['docker']['traefik_container']
            
            try:
                container = self.docker_client.containers.get(traefik_container)
                if container.status != 'running':
                    console.print(f"[red]Traefik container not running[/red]")
                    return False
            except docker.errors.NotFound:
                console.print(f"[red]Traefik container '{traefik_container}' not found[/red]")
                return False
            
            # Trigger certificate request
            self._trigger_certificate_request(domain)
            
            # Wait for certificate generation
            max_attempts = 30
            for attempt in range(max_attempts):
                if self._check_certificate_exists(domain):
                    expiry_date = self._get_certificate_expiry(domain)
                    self._update_certificate_status(domain, 'active')
                    self._update_certificate_expiry(domain, expiry_date)
                    console.print(f"[green]Certificate generated successfully for {domain}[/green]")
                    return True
                time.sleep(10)
            
            console.print(f"[red]Certificate generation timeout for {domain}[/red]")
            self._update_certificate_status(domain, 'failed', 'Generation timeout')
            return False
            
        except Exception as e:
            console.print(f"[red]Traefik certificate generation failed: {e}[/red]")
            self._update_certificate_status(domain, 'failed', str(e))
            return False
    
    def _generate_standalone_certificate(self, domain: str) -> bool:
        """Generate standalone certificate using certbot"""
        try:
            email = self.config['letsencrypt']['email']
            staging = ['--staging'] if self.config['letsencrypt']['staging'] else []
            
            # Run certbot in standalone mode
            cmd = [
                'docker', 'run', '--rm',
                '-v', '/etc/letsencrypt:/etc/letsencrypt',
                '-v', '/var/lib/letsencrypt:/var/lib/letsencrypt',
                '-p', '80:80',
                'certbot/certbot:latest',
                'certonly', '--standalone',
                '--email', email,
                '--agree-tos',
                '--no-eff-email',
                '-d', domain
            ] + staging
            
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                expiry_date = self._get_certificate_expiry(domain)
                self._update_certificate_status(domain, 'active')
                self._update_certificate_expiry(domain, expiry_date)
                console.print(f"[green]Standalone certificate generated for {domain}[/green]")
                return True
            else:
                console.print(f"[red]Certbot failed: {result.stderr}[/red]")
                self._update_certificate_status(domain, 'failed', result.stderr)
                return False
                
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Standalone certificate generation failed: {e}[/red]")
            self._update_certificate_status(domain, 'failed', str(e))
            return False
    
    def _trigger_certificate_request(self, domain: str):
        """Trigger a request to domain to initiate certificate generation"""
        try:
            requests.get(f"https://{domain}", timeout=10, verify=False)
        except:
            try:
                requests.get(f"http://{domain}", timeout=10)
            except:
                pass
    
    def _check_certificate_exists(self, domain: str) -> bool:
        """Check if certificate exists"""
        try:
            # For Traefik, check ACME storage
            acme_file = Path('/var/lib/docker/volumes/traefik_letsencrypt/_data/acme.json')
            if acme_file.exists():
                with open(acme_file) as f:
                    acme_data = json.load(f)
                    # Check in all resolvers
                    for resolver_name, resolver_data in acme_data.items():
                        if isinstance(resolver_data, dict) and 'Certificates' in resolver_data:
                            certificates = resolver_data['Certificates']
                            for cert in certificates:
                                if 'domain' in cert and 'main' in cert['domain']:
                                    if cert['domain']['main'] == domain:
                                        return True
                                    # Check SANs
                                    sans = cert['domain'].get('sans', [])
                                    if domain in sans:
                                        return True
            
            # For standalone certificates
            cert_path = Path(f'/etc/letsencrypt/live/{domain}/fullchain.pem')
            return cert_path.exists()
            
        except Exception:
            return False
    
    def _get_certificate_expiry(self, domain: str) -> str:
        """Get certificate expiry date"""
        try:
            # Use openssl to check certificate expiry
            result = subprocess.run([
                'openssl', 's_client', '-connect', f'{domain}:443', '-servername', domain
            ], input='', text=True, capture_output=True, timeout=10)
            
            if result.returncode == 0:
                cert_result = subprocess.run([
                    'openssl', 'x509', '-noout', '-dates'
                ], input=result.stdout, text=True, capture_output=True)
                
                if cert_result.returncode == 0:
                    for line in cert_result.stdout.split('\n'):
                        if line.startswith('notAfter='):
                            date_str = line.replace('notAfter=', '')
                            # Parse and return in ISO format
                            from datetime import datetime
                            dt = datetime.strptime(date_str.strip(), '%b %d %H:%M:%S %Y %Z')
                            return dt.isoformat()
        except Exception:
            pass
        
        return None

    def _check_domain_ssl_status(self, domain: str) -> str:
        """Check current SSL status of a domain"""
        try:
            response = requests.get(f"https://{domain}", timeout=10, verify=True)
            if response.status_code < 400:
                return 'active'
        except requests.exceptions.SSLError:
            return 'failed'
        except requests.exceptions.RequestException:
            return 'pending'
        
        return 'unknown'
    
    def _update_certificate_status(self, domain: str, status: str, message: str = None):
        """Update certificate status in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE certificates 
            SET status = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE domain = ?
        ''', (status, domain))
        
        # Log the action
        cursor.execute('''
            INSERT INTO renewal_logs (domain, action, status, message)
            VALUES (?, ?, ?, ?)
        ''', (domain, 'status_update', status, message))
        
        conn.commit()
        conn.close()
    
    def _update_certificate_expiry(self, domain: str, expiry_date: str):
        """Update certificate expiry date"""
        if expiry_date:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE certificates 
                SET expiry_date = ?, issued_date = CURRENT_TIMESTAMP
                WHERE domain = ?
            ''', (expiry_date, domain))
            
            conn.commit()
            conn.close()
    
    def renew_certificates(self) -> Dict[str, bool]:
        """Renew certificates that are expiring soon"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get certificates that need renewal
        renewal_days = self.config['notifications']['renewal_days_before']
        renewal_date = (datetime.now() + timedelta(days=renewal_days)).isoformat()
        
        cursor.execute('''
            SELECT domain, type FROM certificates 
            WHERE auto_renew = 1 AND status = 'active'
            AND (expiry_date < ? OR expiry_date IS NULL)
        ''', (renewal_date,))
        
        certificates = cursor.fetchall()
        conn.close()
        
        results = {}
        for domain, cert_type in certificates:
            console.print(f"[yellow]Renewing certificate for {domain}...[/yellow]")
            results[domain] = self.generate_certificate(domain)
        
        return results
    
    def get_certificates(self) -> List[Dict]:
        """Get all certificates"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT domain, type, status, issued_date, expiry_date, 
                   auto_renew, service_type, container_name
            FROM certificates
            ORDER BY domain
        ''')
        
        certificates = []
        for row in cursor.fetchall():
            certificates.append({
                'domain': row[0],
                'type': row[1],
                'status': row[2],
                'issued_date': row[3],
                'expiry_date': row[4],
                'auto_renew': bool(row[5]),
                'service_type': row[6],
                'container_name': row[7]
            })
        
        conn.close()
        return certificates
    
    def delete_certificate(self, domain: str) -> bool:
        """Delete certificate"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM certificates WHERE domain = ?', (domain,))
            cursor.execute('''
                INSERT INTO renewal_logs (domain, action, status, message)
                VALUES (?, ?, ?, ?)
            ''', (domain, 'delete', 'success', 'Certificate deleted'))
            
            conn.commit()
            conn.close()
            
            # Remove certificate files if using standalone mode
            cert_path = Path(f'/etc/letsencrypt/live/{domain}')
            if cert_path.exists():
                subprocess.run(['rm', '-rf', str(cert_path)], check=True)
            
            return True
            
        except Exception as e:
            console.print(f"[red]Failed to delete certificate for {domain}: {e}[/red]")
            return False
