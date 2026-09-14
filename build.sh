#!/usr/bin/env bash
set -o errexit

echo "=== Installing Python dependencies ==="
pip install --upgrade pip
pip install --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt

echo "=== Installing Node dependencies ==="
npm install

echo "=== Building frontend ==="
npm run build

echo "=== Build complete ==="
