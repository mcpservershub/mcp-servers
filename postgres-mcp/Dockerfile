FROM node:22.12-alpine AS builder

WORKDIR /app

# Copy all source files
COPY package.json ./
COPY tsconfig.json ./
COPY index.ts ./

# Install dependencies and build
RUN npm install --no-fund --no-audit
RUN npm run build

FROM node:22-alpine AS release

WORKDIR /app

# Copy built files and package.json
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/package.json ./

ENV NODE_ENV=production

# Install production dependencies only
RUN npm install --ignore-scripts --omit=dev --no-fund --no-audit

ENTRYPOINT ["node", "dist/index.js"]
