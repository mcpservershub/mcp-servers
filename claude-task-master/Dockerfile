# Dockerfile for Task Master MCP Server
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Install dependencies for better container performance
RUN apk add --no-cache \
  git \
  ca-certificates \
  && rm -rf /var/cache/apk/*

# Copy package files
COPY package*.json ./

# Install production dependencies
RUN npm ci --only=production --silent

# Copy application code
COPY . .

# Run prepare script (sets permissions on executables)
RUN npm run prepare

# Create non-root user for security
RUN addgroup -g 1001 -S nodejs && \
  adduser -S taskmaster -u 1001 -G nodejs

# Create directory for task data and set permissions
RUN mkdir -p /app/data && \
  chown -R taskmaster:nodejs /app

# Switch to non-root user
USER taskmaster

# Expose port (if needed for debugging/monitoring)
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD node -e "console.log('MCP Server Health Check')" || exit 1

# Set environment variables
ENV NODE_ENV=production
ENV MCP_SERVER_MODE=docker

# Default command to run the MCP server
CMD ["node", "mcp-server/server.js"]