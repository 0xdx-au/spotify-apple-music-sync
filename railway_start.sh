#!/bin/bash

echo "=== RAILWAY START SCRIPT ==="
echo "Current directory: $(pwd)"
echo "Files in directory:"
ls -la
echo ""
echo "Environment variables (SSL/TLS/CERT related):"
env | grep -i -E "(ssl|tls|cert|key|uvicorn|port)" | sort
echo ""
echo "Python version:"
python --version
echo ""
echo "Running debug_railway.py..."
python debug_railway.py