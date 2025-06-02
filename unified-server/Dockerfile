# Build stage
FROM cgr.dev/chainguard/go:latest-dev AS build
ARG VERSION="dev"

# Set the working directory
WORKDIR /build

COPY  . .

RUN go mod download

RUN go build -o mcpserver ./server

# Final stage

FROM cgr.dev/chainguard/wolfi-base

# TODO: Need to add mirrorD and ast-grep from source in cgr
RUN apk update && apk add git postgresql python-3.12 py3.12-pip py3.12-setuptools sqlite 

WORKDIR /app

COPY --from=builder /mcp/mcpserver /app/

EXPOSE 1234

ENTRYPOINT ["/app/mcpserver"]



