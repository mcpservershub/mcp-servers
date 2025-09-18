# Stage 1: Build stage using Chainguard Node.js image
FROM cgr.dev/chainguard/node:latest-dev AS builder

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production && \
  npm cache clean --force

# Copy TypeScript config and source files
COPY tsconfig.json ./
COPY src ./src

# Install dev dependencies for build
RUN npm install --only=development

# Build the TypeScript project
RUN npm run build

# Remove dev dependencies after build
RUN npm prune --production

# Stage 2: Runtime stage using Chainguard Node.js image with shell for entrypoint
FROM cgr.dev/chainguard/node:latest-dev AS runtime-prep

WORKDIR /app

# Create entrypoint script
RUN cat > /app/entrypoint.js << 'EOF'
#!/usr/bin/env node
const { spawn } = require('child_process');

// Build command line arguments based on environment variables
const args = ['build/index.js'];

// Add framework flag if specified
if (process.env.FRAMEWORK && process.env.FRAMEWORK !== 'react') {
args.push('--framework', process.env.FRAMEWORK);
}

// Add GitHub API key if provided
if (process.env.GITHUB_API_KEY) {
args.push('--github-api-key', process.env.GITHUB_API_KEY);
}

// Add any additional arguments passed to the container
args.push(...process.argv.slice(2));

// Run the MCP server with constructed arguments
const child = spawn('node', args, { stdio: 'inherit' });

child.on('exit', (code) => {
process.exit(code);
});
EOF

# Stage 3: Final runtime stage using distroless Chainguard Node.js image
FROM cgr.dev/chainguard/node:latest

# Set working directory
WORKDIR /app

# Copy only production dependencies and built files from builder
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/build ./build
COPY --from=builder /app/package.json ./
COPY --from=runtime-prep /app/entrypoint.js ./

# Create a non-root user (Chainguard images already run as non-root)
# The Chainguard node image runs as uid 65532 by default

# Set environment variables with defaults
ENV NODE_ENV=production \
  NODE_OPTIONS="--enable-source-maps" \
  FRAMEWORK=react \
  GITHUB_API_KEY=""

# Labels for documentation
LABEL org.opencontainers.image.title="Shadcn UI MCP Server" \
  org.opencontainers.image.description="Model Context Protocol server for shadcn/ui components" \
  org.opencontainers.image.documentation="https://github.com/Jpisnice/shadcn-ui-mcp-server" \
  org.opencontainers.image.source="https://github.com/Jpisnice/shadcn-ui-mcp-server"

# Run the application through the entrypoint wrapper
ENTRYPOINT ["node", "entrypoint.js"]
