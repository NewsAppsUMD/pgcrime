#!/usr/bin/env python3
"""
Update the manifest.json file with available crime data files.
This should be run after downloading new crime data.
"""

import json
import os
from pathlib import Path


def update_manifest():
    """Generate manifest.json from available JSON files."""
    data_dir = Path(__file__).parent / 'data' / 'json'

    # Find all JSON files (excluding manifest itself)
    json_files = sorted([
        f.name for f in data_dir.glob('*.json')
        if f.name != 'manifest.json'
    ], reverse=True)

    if not json_files:
        print("No JSON files found!")
        return

    # Create manifest
    manifest = {
        "files": json_files,
        "latest": json_files[0] if json_files else None,
        "count": len(json_files)
    }

    # Write manifest
    manifest_path = data_dir / 'manifest.json'
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)

    print(f"✓ Updated manifest with {len(json_files)} files")
    print(f"  Latest: {manifest['latest']}")
    print(f"  Path: {manifest_path}")


if __name__ == '__main__':
    update_manifest()
