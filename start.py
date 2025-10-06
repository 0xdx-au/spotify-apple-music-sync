#!/usr/bin/env python3
"""
Railway startup script that handles PORT environment variable properly
Fixed SSL issue for production deployment
"""
import os
import sys
import subprocess

def main():
    # Get PORT from environment, default to 8000
    port = os.environ.get('PORT', '8000')
    
    # Ensure it's a valid integer
    try:
        port_int = int(port)
    except ValueError:
        print(f"Invalid PORT value: {port}, using 8000")
        port_int = 8000
    
    # Build the uvicorn command without SSL for production
    cmd = [
        sys.executable, '-m', 'uvicorn',
        'src.main:app',
        '--host', '0.0.0.0',
        '--port', str(port_int)
    ]
    
    print(f"Starting server with command: {' '.join(cmd)}")
    print(f"Environment: {os.environ.get('ENVIRONMENT', 'development')}")
    print(f"Port: {port_int}")
    
    # Execute uvicorn
    os.execv(sys.executable, cmd)

if __name__ == '__main__':
    main()
