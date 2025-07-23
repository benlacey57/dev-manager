#!/bin/bash
# install.sh - Quick installer script

set -euo pipefail

echo "🚀 Development Server Setup Installer"
echo "======================================"

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "❌ This script must be run as root (use sudo)"
   exit 1
fi

# Install Python and Git if needed
apt update
apt install -y python3 python3-pip git

# Clone or download setup files
SETUP_DIR="/tmp/server-setup"
if [ -d "$SETUP_DIR" ]; then
    rm -rf "$SETUP_DIR"
fi

# For now, create the basic structure
mkdir -p "$SETUP_DIR"/{config,tasks,templates}

# Copy this script's directory structure if running from repo
# Otherwise, download from GitHub
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/setup.py" ]; then
    cp -r "$SCRIPT_DIR"/* "$SETUP_DIR"/
else
    echo "📥 Downloading setup files..."
    # Download from GitHub repository
    git clone https://github.com/your-repo/server-setup.git "$SETUP_DIR"
fi

# Install Python requirements
pip3 install rich pyyaml

# Run setup
cd "$SETUP_DIR"
python3 setup.py

echo "✅ Setup complete!"
