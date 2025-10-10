#!/bin/bash
# Script to install Universal CTags

set -e

echo "Installing Universal CTags..."

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    if command -v apt-get &> /dev/null; then
        # Debian/Ubuntu
        echo "Detected Debian/Ubuntu system"
        sudo apt-get update
        sudo apt-get install -y universal-ctags
    elif command -v yum &> /dev/null; then
        # RHEL/CentOS/Fedora
        echo "Detected RHEL/CentOS/Fedora system"
        sudo yum install -y ctags
    elif command -v pacman &> /dev/null; then
        # Arch Linux
        echo "Detected Arch Linux system"
        sudo pacman -S ctags
    else
        echo "Unsupported Linux distribution. Please install Universal CTags manually."
        exit 1
    fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    echo "Detected macOS"
    if command -v brew &> /dev/null; then
        brew install universal-ctags
    else
        echo "Homebrew not found. Please install Homebrew first: https://brew.sh"
        exit 1
    fi
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    # Windows
    echo "Detected Windows"
    echo "Please download Universal CTags from: https://github.com/universal-ctags/ctags-win32/releases"
    echo "Or use WSL (Windows Subsystem for Linux) and follow Linux instructions"
    exit 1
else
    echo "Unknown operating system: $OSTYPE"
    exit 1
fi

# Verify installation
if command -v ctags &> /dev/null; then
    echo "Universal CTags installed successfully!"
    ctags --version
else
    echo "Installation failed. Please install Universal CTags manually."
    exit 1
fi