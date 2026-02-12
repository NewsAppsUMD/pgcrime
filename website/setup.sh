#!/bin/bash

# Setup script for crime statistics dashboard

echo "Setting up Prince George's County Crime Dashboard..."
echo ""

# Create symlink to data directory if it doesn't exist
if [ ! -L "data" ]; then
    echo "Creating symlink to data directory..."
    ln -sf ../data data
    echo "✓ Symlink created: website/data -> ../data"
else
    echo "✓ Symlink already exists"
fi

# Verify data files are accessible
if [ -d "data/json" ] && [ "$(ls -A data/json/*.json 2>/dev/null)" ]; then
    echo "✓ Data files found: $(ls data/json/*.json 2>/dev/null | wc -l) JSON files"
else
    echo "⚠ Warning: No data files found in data/json/"
    echo "  Make sure crime data has been downloaded to ../data/json/"
fi

echo ""
echo "Setup complete! You can now run:"
echo "  ./serve.sh"
echo ""
echo "Then visit: http://localhost:8000"
