#!/usr/bin/env python3
"""
Debug script to diagnose Railway deployment issues
"""
import os
import sys
import subprocess
import glob

print("="*60)
print("=== RAILWAY DEBUG INFO ===")
print("="*60)
print(f"Python executable: {sys.executable}")
print(f"Working directory: {os.getcwd()}")
print(f"Command line args: {sys.argv}")
print(f"Python version: {sys.version}")

print("\n" + "="*60)
print("=== RELEVANT ENVIRONMENT VARIABLES ===")
print("="*60)
relevant_found = False
for key, value in sorted(os.environ.items()):
    if any(keyword in key.upper() for keyword in ['SSL', 'TLS', 'CERT', 'KEY', 'UVICORN', 'PORT', 'RAILWAY']):
        print(f"{key}={value}")
        relevant_found = True

if not relevant_found:
    print("No SSL/TLS/CERT/KEY/UVICORN/PORT/RAILWAY variables found")

print("\n" + "="*60)
print("=== ALL ENVIRONMENT VARIABLES (subset) ===")
print("="*60)
all_vars = list(os.environ.items())
for key, value in sorted(all_vars)[:30]:  # First 30
    print(f"{key}={value[:100]}{'...' if len(value) > 100 else ''}")
if len(all_vars) > 30:
    print(f"... and {len(all_vars) - 30} more variables")

print("\n" + "="*60) 
print("=== FILES IN CURRENT DIRECTORY ===")
print("="*60)
files = glob.glob("*")
for f in sorted(files):
    try:
        if os.path.isfile(f):
            size = os.path.getsize(f)
            print(f"[FILE] {f} ({size} bytes)")
        else:
            print(f"[DIR]  {f}/")
    except:
        print(f"[?]    {f}")

print("\n" + "="*60)
print("=== CHECKING FOR SSL FILES ===")
print("="*60)
ssl_paths = [
    "config/key.pem",
    "config/cert.pem", 
    "config/localhost-key.pem",
    "config/localhost-cert.pem",
    "ssl/key.pem",
    "ssl/cert.pem",
    "key.pem",
    "cert.pem",
    "/etc/ssl/certs/",
    "/etc/ssl/private/"
]

ssl_found = False
for path in ssl_paths:
    if os.path.exists(path):
        print(f"✓ FOUND: {path}")
        ssl_found = True
    else:
        print(f"✗ NOT FOUND: {path}")

if not ssl_found:
    print("\n*** NO SSL CERTIFICATE FILES FOUND ***")

print("\n" + "="*60)
print("=== INSTALLED PACKAGES (uvicorn related) ===") 
print("="*60)
try:
    result = subprocess.run(['pip', 'show', 'uvicorn'], capture_output=True, text=True, timeout=5)
    if result.returncode == 0:
        print(result.stdout)
    else:
        print("uvicorn not found via pip show")
except Exception as e:
    print(f"Error checking uvicorn: {e}")

print("\n" + "="*60)
print("=== STARTING UVICORN WITHOUT SSL ===")
print("="*60)

# Get port from environment
port = os.environ.get('PORT', '8000')
print(f"Using port: {port}")

# Build uvicorn command without any SSL parameters
cmd = [sys.executable, '-m', 'uvicorn', 'src.main:app', '--host', '0.0.0.0', '--port', port]
print(f"Command: {' '.join(cmd)}")
print("\nStarting uvicorn...")
print("="*60)

try:
    # Execute uvicorn
    subprocess.run(cmd, check=True)
except subprocess.CalledProcessError as e:
    print(f"\n*** UVICORN FAILED WITH RETURN CODE {e.returncode} ***")
    sys.exit(1)
except FileNotFoundError:
    print("\n*** ERROR: uvicorn command not found ***")
    sys.exit(1)
except Exception as e:
    print(f"\n*** UNEXPECTED ERROR: {e} ***")
    sys.exit(1)
