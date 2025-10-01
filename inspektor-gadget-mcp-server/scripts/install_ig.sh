#!/bin/bash
# Install Inspektor-Gadget CLI tool

set -e

echo "Installing Inspektor-Gadget..."

# Detect architecture
ARCH=$(uname -m)
case $ARCH in
    x86_64)
        ARCH="amd64"
        ;;
    aarch64)
        ARCH="arm64"
        ;;
    *)
        echo "Unsupported architecture: $ARCH"
        exit 1
        ;;
esac

# Download and install
IG_VERSION="latest"
IG_URL="https://github.com/inspektor-gadget/inspektor-gadget/releases/latest/download/ig-linux-${ARCH}-${IG_VERSION}.tar.gz"

echo "Downloading from: $IG_URL"
curl -sL "$IG_URL" | sudo tar -C /usr/local/bin -xzf - ig

# Make executable
sudo chmod +x /usr/local/bin/ig

# Verify installation
if command -v ig &> /dev/null; then
    echo "✅ Inspektor-Gadget installed successfully!"
    ig version
else
    echo "❌ Installation failed"
    exit 1
fi