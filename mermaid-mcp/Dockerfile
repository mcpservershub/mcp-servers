FROM cgr.dev/chainguard/wolfi-base

RUN apk update && apk add nodejs npm

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy application code
COPY . .

# Build the application
RUN npm run build

# Command will be provided by smithery.yaml
CMD ["node", "build/index.js"]
