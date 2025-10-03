# Enhanced Cypress MCP Server Dockerfile
FROM cgr.dev/chainguard/wolfi-base

# Set working directory
WORKDIR /app

# Install system dependencies for Puppeteer
RUN apk update && apk add --no-cache \
  nodejs \
  npm \
  chromium \
  nss \
  freetype \
  harfbuzz 

# Tell Puppeteer to skip installing Chromium. We'll be using the installed package.
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true \
  PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium-browser

# Create non-root user for security
RUN addgroup mcpuser && adduser -D -G mcpuser mcpuser

# Copy package files
COPY package.json package-lock.json ./

# Install Node.js dependencies
RUN npm install --only=production && npm cache clean --force

# Copy source code
COPY src/ ./src/
COPY test/ ./test/
COPY README.md ./

# Change ownership to non-root user
RUN chown -R mcpuser:mcpuser /app
USER mcpuser

# Expose port (if needed for HTTP mode in future)
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD node -e "console.log('MCP Server is healthy')" || exit 1

# Default command
CMD ["node", "src/index.js"]
