#!/bin/bash

# Docker build script for Zoekt MCP Server with Universal Ctags
set -e

IMAGE_NAME="zoekt-mcp-server"
IMAGE_TAG="ctags"
FULL_IMAGE_NAME="${IMAGE_NAME}:${IMAGE_TAG}"

echo "Building Zoekt MCP Server Docker image with Universal Ctags..."
echo "Image: ${FULL_IMAGE_NAME}"

# Build the Docker image
docker build -f Dockerfile.ctags -t "${FULL_IMAGE_NAME}" .

echo "✅ Docker image built successfully: ${FULL_IMAGE_NAME}"
echo ""
echo "To run the container:"
echo "docker run -it --rm -v \$(pwd)/data:/app/.zoekt -v \$(pwd)/repos:/app/repos ${FULL_IMAGE_NAME}"
echo ""
echo "For interactive testing:"
echo "docker run -it --rm --entrypoint=/bin/sh ${FULL_IMAGE_NAME}"
echo ""
echo "Available tools in the container:"
echo "  Zoekt CLI tools:"
echo "    - zoekt"
echo "    - zoekt-index"
echo "    - zoekt-git-index"
echo "    - zoekt-git-clone"
echo "    - zoekt-mirror-github"
echo "    - zoekt-webserver"
echo "    - zoekt-indexserver"
echo "    - zoekt-mcp-server"
echo ""
echo "  Universal Ctags tools:"
echo "    - ctags (main binary, nightly build 2025.07.08)"
echo "    - readtags"
echo ""
echo "Test ctags installation:"
echo "docker run --rm ${FULL_IMAGE_NAME} /usr/local/bin/ctags --version"