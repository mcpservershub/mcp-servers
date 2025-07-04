FROM mcr.microsoft.com/dotnet/sdk:8.0-bullseye-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /tmp/sandbox_output /tmp/sandbox_plots

WORKDIR /sandbox