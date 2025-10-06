#!/usr/bin/env python3
"""
Railway startup script that handles PORT environment variable properly
Fixed SSL issue for production deployment
"""
import os
import sys
import subprocess

def main():
    print("🚀 Railway startup script starting...")
    
    # Force production environment to avoid SSL
    os.environ['ENVIRONMENT'] = 'production'
    
    # Get PORT from environment, default to 8000
    port = os.environ.get('PORT', '8000')
    
    # Ensure it's a valid integer
    try:
        port_int = int(port)
    except ValueError:
        print(f"Invalid PORT value: {port}, using 8000")
        port_int = 8000
    
    # Build the uvicorn command without ANY SSL configuration
    cmd = [
        sys.executable, '-m', 'uvicorn',
        'src.main:app',
        '--host', '0.0.0.0',
        '--port', str(port_int),
        '--workers', '1'
    ]
    
    print(f"Starting server with command: {' '.join(cmd)}")
    print(f"Environment: {os.environ.get('ENVIRONMENT', 'development')}")
    print(f"Port: {port_int}")
    print(f"Working directory: {os.getcwd()}")
    
    # Execute uvicorn using subprocess to see any errors
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running uvicorn: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
