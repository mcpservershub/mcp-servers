FROM cgr.dev/chainguard/python:latest-dev
USER root

ENV DEBIAN_FRONTEND=noninteractive
ENV EXIFTOOL_PATH=/usr/bin/exiftool
ENV FFMPEG_PATH=/usr/bin/ffmpeg
ENV MARKITDOWN_ENABLE_PLUGINS=True

# Runtime dependency
# NOTE: Add any additional MarkItDown plugins here
RUN apk add --no-cache exiftool ffmpeg

# Cleanup
RUN rm -rf /var/lib/apt/lists/*

COPY . /app
RUN pip --no-cache-dir install /app

WORKDIR /workdir

# Default USERID and GROUPID
ARG USERID=nobody
ARG GROUPID=nogroup

USER $USERID:$GROUPID

ENTRYPOINT [ "markitdown-mcp" ]
