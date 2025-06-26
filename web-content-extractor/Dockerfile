# Use Node.js 20 Alpine for smaller image size
FROM cgr.dev/chainguard/node:latest
USER root
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

# Default command to run the MCP server
ENTRYPOINT ["npm", "start"]
