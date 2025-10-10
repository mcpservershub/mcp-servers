# ----- Build Stage -----
FROM cgr.dev/chainguard/wolfi-base AS builder

RUN apk update && apk add nodejs npm

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* bun.lock* tsconfig.json ./

# Copy source code
COPY src ./src

# Install dependencies and build the TypeScript code
RUN npm install && npm run build

# Create a non-root user to run the application
RUN addgroup -g 1001 -S nodejs && \
  adduser -S nodejs -u 1001

# Copy package.json for production dependencies
COPY --chown=nodejs:nodejs package.json ./

# Install only production dependencies
RUN npm install --production --ignore-scripts && \
  npm cache clean --force

# Switch to non-root user
USER nodejs

# Run the server with stdio transport (default)
CMD ["node", "dist/index.js", "--transport", "stdio"]
