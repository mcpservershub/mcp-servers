FROM node:22.12-alpine AS builder

COPY src/postgres /app
COPY tsconfig.json /tsconfig.json

WORKDIR /app

RUN --mount=type=cache,target=/root/.npm npm install --no-fund --no-audit

FROM node:22-alpine AS release

COPY --from=builder /app/dist /app/dist
COPY --from=builder /app/package.json /app/package.json

ENV NODE_ENV=production

WORKDIR /app

RUN npm install --ignore-scripts --omit=dev --no-fund --no-audit

ENTRYPOINT ["node", "dist/index.js"]
