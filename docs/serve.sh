#!/bin/bash

# Simple script to serve the crime statistics dashboard locally

PORT=8000

echo "Starting Prince George's County Crime Statistics Dashboard..."
echo "Server will be available at: http://localhost:$PORT"
echo ""
echo "Note: Make sure the 'data' symlink exists in the website directory"
echo "If data doesn't load, run: ln -sf ../data data"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start Python's built-in HTTP server
python3 -m http.server $PORT
