# Multi-stage Dockerfile for chrome-devtools-mcp using Chainguard base images

# Stage 1: Build stage — bundle all deps into self-contained output
FROM cgr.dev/chainguard/node:latest-dev AS builder

WORKDIR /app

# Copy package files and build configs
COPY package*.json tsconfig.json rollup.config.mjs puppeteer.config.cjs ./

# Copy scripts directory (required for prepare script during npm ci)
COPY scripts ./scripts

# Install all dependencies (upstream moved everything to devDependencies)
RUN npm ci

# Copy source code
COPY src ./src

# Bundle the project (tsc + rollup — produces self-contained build/ with all deps inlined)
RUN npm run bundle

# Stage 2: Runtime stage with Chrome
FROM cgr.dev/chainguard/wolfi-base:latest

# Install Node.js and Chrome dependencies
RUN apk add --no-cache \
    nodejs \
    chromium \
    font-noto-emoji \
    font-noto-cjk \
    ca-certificates \
    libsdl2-ttf \
    && rm -rf /var/cache/apk/*

WORKDIR /app

# Create non-root user for Chrome
RUN mkdir -p /home/nonroot/.cache/chrome-devtools-mcp \
    && chown -R nonroot:nonroot /home/nonroot

# Copy bundled application from builder (self-contained, no node_modules needed)
COPY --from=builder --chown=nonroot:nonroot /app/build ./build
COPY --from=builder --chown=nonroot:nonroot /app/package*.json ./

# Set environment variables for Chrome
ENV CHROME_BIN=/usr/bin/chromium-browser \
    CHROME_PATH=/usr/bin/chromium-browser \
    PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium-browser \
    PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true \
    HOME=/home/nonroot

# Switch to non-root user
USER nonroot

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD node --version || exit 1

ENTRYPOINT ["node", "build/src/index.js"]
CMD ["--headless", "--isolated", "--executablePath=/usr/bin/chromium-browser"]
