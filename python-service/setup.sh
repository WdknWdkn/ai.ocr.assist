#!/bin/bash
set -e

# Activate virtual environment
. /app/venv/bin/activate

# Install dependencies
pip install --no-cache-dir -r requirements.txt

# List installed packages
pip list
