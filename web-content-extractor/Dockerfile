# Use Node.js 20 Alpine for smaller image size
FROM node:20-alpine

# Set working directory
WORKDIR /app

# Copy package files first for better caching
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy TypeScript configuration
COPY tsconfig.json ./

# Copy source code
COPY src/ ./src/

# Install development dependencies needed for building
RUN npm install --save-dev typescript tsx @types/node

# Build the TypeScript code
RUN npm run build

# Remove development dependencies to reduce image size
RUN npm prune --production


#     adduser -S mcp -u 1001

# Create directory for output files and set proper permissions for entire app
# RUN mkdir -p /app/output && chown -R mcp:nodejs /app

# # Switch to non-root user
# USER mcp

# Expose any ports if needed (MCP typically uses stdio, but for debugging)
# EXPOSE 3000

# # Set environment variables
# ENV NODE_ENV=production

# Default command to run the MCP server
CMD ["npm", "start"]

# # Add health check
# HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
#   CMD node -e "console.log('MCP Server is running')" || exit 1
#
# # Labels for better maintainability
# LABEL maintainer="mcp-server"
# LABEL description="Web Content Extractor MCP Server"
# LABEL version="1.0.0"
