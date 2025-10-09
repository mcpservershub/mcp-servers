FROM cgr.dev/chainguard/node:latest-dev AS builder

# Set the working directory
WORKDIR /app
USER root
# Copy package.json and package-lock.json
COPY . .

# Copy the entire source directory
RUN npm install


FROM cgr.dev/chainguard/node:latest AS release

WORKDIR /app

COPY --from=builder /app/dist /app/dist
COPY --from=builder /app/package.json /app/package.json
COPY --from=builder /app/package-lock.json /app/package-lock.json

ENV NODE_ENV=production

RUN npm ci --ignore-scripts --omit-dev

ENTRYPOINT ["node", "dist/index.js"]
