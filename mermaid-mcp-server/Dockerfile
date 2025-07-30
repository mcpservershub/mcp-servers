FROM cgr.dev/chainguard/wolfi-base
USER root
# Install Chromium with its dependencies
RUN apk update && apk add nodejs npm chromium 

# Set working directory
WORKDIR /app


# Copy package files and install dependencies
# Use PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true to avoid downloading Chromium again
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true
COPY index.ts tsconfig.json package.json ./
COPY diagrams /app/diagram
RUN npm install --no-fund --no-audit

# Build the TypeScript code
RUN npm run build

# Command to run the MCP server
CMD [ "node", "dist/index.js" ]
