# Multi-stage Dockerfile using Chainguard Node.js images
# Build stage uses :latest-dev (has shell and build tools)
# Runtime stage uses :latest (minimal, no shell, most secure)

# Stage 1: Dependencies
FROM cgr.dev/chainguard/node:latest-dev AS deps

USER root

# Install pnpm globally
RUN npm install -g pnpm@10.7.1

WORKDIR /app

# Copy package files
COPY package.json pnpm-lock.yaml ./

# Install all dependencies
RUN pnpm install --frozen-lockfile

# Stage 2: Builder
FROM cgr.dev/chainguard/node:latest-dev AS builder

USER root

# Install pnpm globally
RUN npm install -g pnpm@10.7.1

WORKDIR /app

# Copy dependencies from deps stage
COPY --from=deps /app/node_modules ./node_modules

# Copy application source
COPY . .

# Build the application
RUN pnpm run build

# Create writable directories for wrangler
RUN mkdir -p /app/.wrangler /app/node_modules/.mf

# Stage 3: Runner (Minimal production image with wolfi-base)
FROM cgr.dev/chainguard/wolfi-base AS runner

# Install Node.js and npm using apk
RUN apk update && apk add --no-cache nodejs npm

# Install pnpm globally
RUN npm install -g pnpm@10.7.1

WORKDIR /app

# Set NODE_ENV to production
ENV NODE_ENV=production

# Copy package files
COPY --from=builder /app/package.json /app/pnpm-lock.yaml ./

# Copy node_modules from builder (includes all dependencies needed for wrangler)
COPY --from=builder /app/node_modules ./node_modules

# Copy built application
COPY --from=builder /app/build ./build

# Copy necessary runtime files
COPY --from=builder /app/wrangler.jsonc ./
COPY --from=builder /app/src ./src
COPY --from=builder /app/static ./static
COPY --from=builder /app/public ./public
COPY --from=builder /app/worker-configuration.d.ts ./

# Copy writable directories
COPY --from=builder /app/.wrangler ./.wrangler
COPY --from=builder /app/node_modules/.mf ./node_modules/.mf

# Ensure proper ownership for nonroot user (wolfi-base default user)
RUN chown -R nonroot:nonroot /app

# Switch to non-root user
USER nonroot

# Expose port
EXPOSE 8787

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:8787/ || exit 1

# Start the application (pnpm is in PATH from npm install)
CMD ["pnpm", "exec", "wrangler", "dev", "--ip", "0.0.0.0", "--port", "8787", "--log-level", "info"]
