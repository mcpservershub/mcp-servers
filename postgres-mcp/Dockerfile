FROM cgr.dev/chainguard/node:latest-dev AS builder

WORKDIR /app

# Switch to root to copy and install
USER root

COPY . /app/

# Fix ownership of all files to node user
RUN chown -R node:node /app

# Switch back to node user for npm operations
USER node

RUN --mount=type=cache,target=/home/node/.npm,uid=65532,gid=65532 npm install --ignore-scripts --no-package-lock

# Build the TypeScript code
RUN npm run build

# Install production dependencies only
RUN --mount=type=cache,target=/home/node/.npm-production,uid=65532,gid=65532 npm install --ignore-scripts --omit=dev --no-package-lock

FROM cgr.dev/chainguard/node:latest AS release

WORKDIR /app

# Copy files with proper ownership
COPY --from=builder --chown=node:node /app/dist /app/dist
COPY --from=builder --chown=node:node /app/package.json /app/package.json
COPY --from=builder --chown=node:node /app/node_modules /app/node_modules

ENV NODE_ENV=production

# No need to run npm ci again since we're copying node_modules from builder

ENTRYPOINT ["node", "dist/index.js"]
