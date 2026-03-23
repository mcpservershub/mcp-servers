# ----- Build Stage -----
FROM cgr.dev/chainguard/wolfi-base AS builder

RUN apk update && apk add --no-cache nodejs npm
RUN npm install -g pnpm

WORKDIR /app

# Copy monorepo root config
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml tsconfig.json ./

# Copy the mcp package
COPY packages/mcp ./packages/mcp

# Install dependencies
RUN pnpm install --frozen-lockfile

# Build the mcp package
RUN pnpm --filter @upstash/context7-mcp build

# ----- Production Stage -----
FROM cgr.dev/chainguard/wolfi-base

RUN apk update && apk add --no-cache nodejs npm
RUN npm install -g pnpm

WORKDIR /app

# Copy monorepo root config for pnpm workspace resolution
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY packages/mcp/package.json ./packages/mcp/

# Install production dependencies only
RUN pnpm install --frozen-lockfile --prod --filter @upstash/context7-mcp

# Copy built files from builder
COPY --from=builder /app/packages/mcp/dist ./packages/mcp/dist

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodejs -u 1001

USER nodejs
WORKDIR /app/packages/mcp

CMD ["node", "dist/index.js", "--transport", "stdio"]
