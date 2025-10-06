#!/usr/bin/env python3
"""
Debug script to see what Railway is setting as environment variables
"""
import os
import sys

print("=== RAILWAY DEBUG INFO ===")
print(f"Python executable: {sys.executable}")
print(f"Working directory: {os.getcwd()}")
print(f"Command line args: {sys.argv}")

print("\n=== ENVIRONMENT VARIABLES ===")
for key, value in sorted(os.environ.items()):
    if any(keyword in key.upper() for keyword in ['SSL', 'TLS', 'CERT', 'KEY', 'UVICORN', 'PORT', 'RAILWAY']):
        print(f"{key}={value}")

print("\n=== FILES IN CURRENT DIRECTORY ===")
import glob
files = glob.glob("*")
for f in sorted(files):
    print(f)

print("\n=== CHECKING FOR SSL FILES ===")
ssl_paths = [
    "config/key.pem",
    "config/cert.pem", 
    "config/localhost-key.pem",
    "config/localhost-cert.pem",
    "ssl/key.pem",
    "ssl/cert.pem",
    "key.pem",
    "cert.pem"
]

for path in ssl_paths:
    if os.path.exists(path):
        print(f"Found SSL file: {path}")

print("\n=== Starting uvicorn manually ===")

# Now start uvicorn the way we want
port = os.environ.get('PORT', '8000')
cmd = [sys.executable, '-m', 'uvicorn', 'src.main:app', '--host', '0.0.0.0', '--port', port]
print(f"Running: {' '.join(cmd)}")

import subprocess
subprocess.run(cmd)