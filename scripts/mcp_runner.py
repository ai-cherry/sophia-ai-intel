#!/usr/bin/env python3
"""
MCP Service Runner Helper
Assists with starting MCP services for health check testing
"""

import subprocess
import sys
import time
import signal
import os

def run_mcp_service(service_path, port):
    """Start an MCP service on the specified port"""
    try:
        # Change to service directory
        os.chdir(service_path)
        
        # Start the service
        proc = subprocess.Popen(
            ["uvicorn", "app:app", "--port", str(port), "--host", "0.0.0.0"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid  # Create new process group for clean termination
        )
        
        # Output the PID for the parent script to track
        print(proc.pid)
        
        # Wait a bit to ensure service starts
        time.sleep(3)
        
        # Return the process (won't actually return in normal operation)
        return proc
        
    except Exception as e:
        print(f"Error starting service: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    if len(sys.argv) != 3:
        print("Usage: mcp_runner.py <service_path> <port>", file=sys.stderr)
        sys.exit(1)
    
    service_path = sys.argv[1]
    port = int(sys.argv[2])
    
    if not os.path.exists(service_path):
        print(f"Service path does not exist: {service_path}", file=sys.stderr)
        sys.exit(1)
    
    if not os.path.exists(os.path.join(service_path, "app.py")):
        print(f"app.py not found in {service_path}", file=sys.stderr)
        sys.exit(1)
    
    # Run the service
    proc = run_mcp_service(service_path, port)
    
    # Keep the process running until interrupted
    try:
        proc.wait()
    except KeyboardInterrupt:
        # Clean shutdown
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        sys.exit(0)

if __name__ == "__main__":
    main()