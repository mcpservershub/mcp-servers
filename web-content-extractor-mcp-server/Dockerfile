# Use Node.js 20 Alpine for smaller image size
FROM cgr.dev/chainguard/node:latest
USER root
# Set working directory
WORKDIR /app

# Copy package files first for better caching
COPY package.json ./

# Install ALL dependencies (both production and dev)
RUN npm install --no-fund --no-audit

# Copy TypeScript configuration
COPY tsconfig.json ./

# Copy source code
COPY src/ ./src/

# Build the TypeScript code
RUN npm run build

# Remove development dependencies to reduce image size
RUN npm prune --production

# Default command to run the MCP server
ENTRYPOINT ["npm", "start"]
