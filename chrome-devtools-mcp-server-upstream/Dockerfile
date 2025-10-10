# Multi-stage Dockerfile for chrome-devtools-mcp using Chainguard base images
# This Dockerfile creates a minimal, secure container for running the MCP server

# Stage 1: Build stage
FROM cgr.dev/chainguard/node:latest-dev AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./
COPY tsconfig.json ./

# Copy scripts directory (required for prepare script during npm ci)
COPY scripts ./scripts

# Install dependencies
RUN npm ci

# Copy source code
COPY src ./src

# Build the project
RUN npm run build

# Stage 2: Production dependencies
FROM cgr.dev/chainguard/node:latest-dev AS deps

WORKDIR /app

# Copy package files
COPY package*.json ./

# Copy scripts directory (required for prepare script)
COPY scripts ./scripts

# Install only production dependencies
RUN npm ci --omit=dev --ignore-scripts

# Stage 3: Runtime stage with Chrome
FROM cgr.dev/chainguard/wolfi-base:latest

# Install Node.js and Chrome dependencies
RUN apk add --no-cache \
    nodejs \
    npm \
    chromium \
    font-noto-emoji \
    font-noto-cjk \
    ca-certificates \
    libsdl2-ttf \
    && rm -rf /var/cache/apk/*

WORKDIR /app

# Create non-root user for Chrome (Chainguard images are non-root by default)
# Chrome requires specific directories and permissions
RUN mkdir -p /home/nonroot/.cache/chrome-devtools-mcp \
    && chown -R nonroot:nonroot /home/nonroot

# Copy built application from builder
COPY --from=builder --chown=nonroot:nonroot /app/build ./build
COPY --from=builder --chown=nonroot:nonroot /app/package*.json ./

# Copy production dependencies
COPY --from=deps --chown=nonroot:nonroot /app/node_modules ./node_modules

# Set environment variables for Chrome
ENV CHROME_BIN=/usr/bin/chromium-browser \
    CHROME_PATH=/usr/bin/chromium-browser \
    PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium-browser \
    PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true \
    HOME=/home/nonroot

# Switch to non-root user
USER nonroot

# Expose no ports (MCP servers communicate via stdio)

# Health check (optional - checks if node binary exists)
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD node --version || exit 1

# Set the entrypoint to the MCP server
# Users should run with --headless=true and --isolated=true for containerized environments
ENTRYPOINT ["node", "build/src/index.js"]

# Default arguments for containerized environment
CMD ["--headless", "--isolated", "--executablePath=/usr/bin/chromium-browser"]
