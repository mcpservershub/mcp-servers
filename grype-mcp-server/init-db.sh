#!/bin/sh
# Initialize Grype database if not present

echo "Checking Grype database status..."

# Check if database exists
grype db status > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "Database not found. Initializing..."
    grype db update
    if [ $? -eq 0 ]; then
        echo "Database initialized successfully."
    else
        echo "Warning: Failed to initialize database. Scans may fail."
    fi
else
    echo "Database is ready."
fi

# Run the actual command
exec "$@"