#!/usr/bin/env python3

import os
import time
import subprocess
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from rich.console import Console
import yaml

console = Console()

class HotReloadHandler(FileSystemEventHandler):
    def __init__(self, project_path: Path, config: dict):
        self.project_path = project_path
        self.config = config
        self.last_reload = 0
        self.debounce_seconds = 2
        
    def on_modified(self, event):
        if event.is_directory:
            return
            
        # Debounce rapid file changes
        now = time.time()
        if now - self.last_reload < self.debounce_seconds:
            return
            
        file_path = Path(event.src_path)
        
        # Check if file should trigger reload
        if self._should_reload(file_path):
            console.print(f"[yellow]File changed: {file_path.name}[/yellow]")
            self._trigger_reload()
            self.last_reload = now
            
    def _should_reload(self, file_path: Path) -> bool:
        """Check if file change should trigger reload"""
        # Skip certain files/directories
        skip_patterns = [
            '.git', 'node_modules', '__pycache__', '.pytest_cache',
            '.vscode', '.idea', 'dist', 'build', '.next'
        ]
        
        if any(pattern in str(file_path) for pattern in skip_patterns):
            return False
            
        # Check file extensions
        reload_extensions = self.config.get('hot_reload', {}).get('extensions', [
            '.py', '.js', '.ts', '.vue', '.php', '.html', '.css', '.scss'
        ])
        
        return file_path.suffix in reload_extensions
        
    def _trigger_reload(self):
        """Trigger application reload"""
        reload_command = self.config.get('hot_reload', {}).get('command')
        
        if reload_command:
            try:
                os.chdir(self.project_path)
                subprocess.run(reload_command, shell=True, check=True)
                console.print("[green]✅ Application reloaded[/green]")
            except subprocess.CalledProcessError as e:
                console.print(f"[red]❌ Reload failed: {e}[/red]")

class BuildSystem:
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.config = self._load_config()
        
    def _load_config(self) -> dict:
        """Load build configuration"""
        config_file = self.project_path / 'build.yml'
        if config_file.exists():
            with open(config_file) as f:
                return yaml.safe_load(f)
        return {}
        
    def start_hot_reload(self):
        """Start hot reload file watcher"""
        console.print(f"[cyan]Starting hot reload for {self.project_path.name}[/cyan]")
        
        event_handler = HotReloadHandler(self.project_path, self.config)
        observer = Observer()
        observer.schedule(event_handler, str(self.project_path), recursive=True)
        observer.start()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
            console.print("[yellow]Hot reload stopped[/yellow]")
        observer.join()
        
    def run_build(self, target: str = 'dev'):
        """Run build process"""
        build_steps = self.config.get('build', {}).get(target, [])
        
        if not build_steps:
            console.print(f"[yellow]No build steps defined for target: {target}[/yellow]")
            return
            
        console.print(f"[cyan]Building {target}...[/cyan]")
        
        for step in build_steps:
            console.print(f"[blue]Running: {step}[/blue]")
            try:
                os.chdir(self.project_path)
                subprocess.run(step, shell=True, check=True)
            except subprocess.CalledProcessError as e:
                console.print(f"[red]Build failed: {e}[/red]")
                return False
                
        console.print("[green]✅ Build completed successfully[/green]")
        return True
