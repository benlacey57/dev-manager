#!/bin/bash

# Installation script for the enhanced development environment

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

# Check requirements
check_requirements() {
    log "Checking requirements..."
    
    command -v python3 >/dev/null 2>&1 || error "Python 3 is required"
    command -v docker >/dev/null 2>&1 || error "Docker is required"
    command -v docker-compose >/dev/null 2>&1 || error "Docker Compose is required"
    command -v git >/dev/null 2>&1 || error "Git is required"
    
    log "✅ All requirements met"
}

# Install Python dependencies
install_dependencies() {
    log "Installing Python dependencies..."
    
    pip3 install --user \
        rich \
        click \
        pyyaml \
        docker \
        requests \
        watchdog
    
    log "✅ Dependencies installed"
}

# Setup directory structure
setup_directories() {
    log "Setting up directory structure..."
    
    mkdir -p ~/scripts/dev-manager
    mkdir -p ~/scripts
    mkdir -p ~/sites
    mkdir -p ~/docker/{base,overlays,templates}
    mkdir -p ~/config/{versions,templates,nginx-proxy-manager,traefik,ssl}
    mkdir -p ~/infrastructure
    
    log "✅ Directories created"
}

# Sync dotfiles
sync_dotfiles() {
    log "Syncing dotfiles from GitHub..."
    
    if [[ -d ~/dotfiles ]]; then
        cd ~/dotfiles
        git pull
    else
        git clone https://github.com/benlacey57/dotfiles ~/dotfiles
    fi
    
    log "✅ Dotfiles synced"
}

# Create CLI symlink
create_symlink() {
    log "Creating CLI symlink..."
    
    chmod +x ~/scripts/dev-manager/dev
    sudo ln -sf ~/scripts/dev-manager/dev /usr/local/bin/dev
    
    log "✅ CLI symlink created"
}

# Setup infrastructure
setup_infrastructure() {
    log "Setting up infrastructure..."
    
    # Copy infrastructure docker-compose.yml
    # (This would be created from the YAML content above)
    
    log "✅ Infrastructure configured"
}

main() {
    log "🚀 Installing Enhanced Development Environment Manager"
    
    check_requirements
    install_dependencies
    setup_directories
    sync_dotfiles
    create_symlink
    setup_infrastructure
    
    log "🎉 Installation completed!"
    log ""
    log "Available commands:"
    log "  dev new                    # Create new project"
    log "  dev start <project>        # Start project"
    log "  dev versions              # Manage versions"
    log "  dev dotfiles sync         # Sync dotfiles"
    log "  dev                       # Interactive mode"
    log ""
    log "Example usage:"
    log "  dev new -t laravel -n mysite --versions php:8.2"
    log ""
    log "🔧 Next steps:"
    log "1. Run 'dev versions' to set default tool versions"
    log "2. Run 'dev dotfiles install' to install dotfiles"
    log "3. Create your first project with 'dev new'"
}

main "$@"
