FROM cgr.dev/chainguard/node:latest-dev AS builder
USER root
WORKDIR /app

# Install transient deps (git, ca-certs) and clean up
RUN apk add --no-cache ca-certificates git \
    && rm -rf /var/cache/apk/*

# Install only production packages
COPY package.json ./

# Copy source (if you had a build step—e.g. `npm run build`—you'd run it here)
COPY . .

RUN npm install --omit=dev --no-fund --no-audit

#### Final stage
FROM cgr.dev/chainguard/node:latest AS final

# Set working dir
WORKDIR /app

# Copy over SSL certs so HTTPS still works
COPY --from=builder /etc/ssl/certs /etc/ssl/certs

# Copy built app and node_modules
COPY --from=builder /app ./

# Create non-root user & data dir, fix ownership
USER root

RUN addgroup -g 1001 -S nodejs \
    && adduser    -u 1001 -S taskmaster -G nodejs 

RUN mkdir -p /app/data \
    && chown -R taskmaster:nodejs /app 


# Switch into non-root user
USER taskmaster

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD node -e "console.log('MCP Server Health Check')" || exit 1

# Runtime environment
ENV NODE_ENV=production
ENV MCP_SERVER_MODE=docker

# Default command
CMD ["mcp-server/server.js"]
