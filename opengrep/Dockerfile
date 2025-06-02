# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /server

# Install curl so we can fetch the opengrep binary
RUN apt-get update && \
  apt-get install -y --no-install-recommends curl && \
  rm -rf /var/lib/apt/lists/*

# Download the opengrep CLI and install it into /usr/local/bin (which is in PATH)
RUN curl -L \
  -o /usr/local/bin/opengrep \
  https://github.com/opengrep/opengrep/releases/download/v1.2.2/opengrep_manylinux_x86 && \
  chmod +x /usr/local/bin/opengrep

# Install any needed Python packages specified in requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code
COPY . .

# Run opengrep.py when the container launches
ENTRYPOINT ["python", "/server/opengrep.py"]
