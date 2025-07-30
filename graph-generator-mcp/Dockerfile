# ------------ BUILD STAGE -------------
FROM cgr.dev/chainguard/node:latest-dev AS builder
WORKDIR /app

USER root

# Copy package files first
COPY package.json ./

# Install deps WITHOUT prepare/husky
RUN npm install --ignore-scripts --no-package-lock

# Copy source
COPY . .

# Build TS output
RUN npm run build

# ------------ RUNTIME STAGE -------------
FROM cgr.dev/chainguard/node:latest AS release

WORKDIR /app

# Copy built output & metadata
COPY --from=builder /app/build ./build
COPY --from=builder /app/package.json ./package.json

# ✅ install prod-only deps, skip all scripts
RUN npm install --ignore-scripts --omit=dev --no-package-lock

# Run the app
CMD ["build/index.js" ]
