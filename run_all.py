#!/usr/bin/env python3
"""
Parallel runner for CareerMind AI backend and frontend
Starts both services concurrently
"""

import subprocess
import sys
import time
import os
from pathlib import Path

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent

def run_backend():
    """Run the FastAPI backend server"""
    print("\n" + "="*60)
    print("🚀 Starting Backend (FastAPI) on http://localhost:8000")
    print("="*60)
    backend_dir = PROJECT_ROOT / "backend"
    
    try:
        subprocess.run(
            [sys.executable, "-m", "uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
            cwd=backend_dir,
            check=False
        )
    except KeyboardInterrupt:
        # Silently exit on Ctrl+C
        pass
    except Exception as e:
        print(f"❌ Error starting backend: {e}")
        sys.exit(1)


def run_frontend():
    """Run a simple HTTP server for the frontend"""
    print("\n" + "="*60)
    print("🌐 Starting Frontend (HTTP Server) on http://localhost:3000")
    print("="*60)
    frontend_dir = PROJECT_ROOT / "frontend"
    
    # Wait a moment for backend to start
    time.sleep(2)
    
    try:
        # Use Python's built-in HTTP server on port 3000
        subprocess.run(
            [sys.executable, "-m", "http.server", "3000", "--directory", str(frontend_dir)],
            check=False
        )
    except KeyboardInterrupt:
        # Silently exit on Ctrl+C
        pass
    except Exception as e:
        print(f"❌ Error starting frontend: {e}")
        sys.exit(1)


def main():
    """Main function to run both services in parallel"""
    print("\n" + "="*60)
    print("🎯 CareerMind AI - Parallel Runner")
    print("="*60)
    print("\n📋 Services to start:")
    print("   • Backend (FastAPI): http://localhost:8000")
    print("   • Frontend (Static): http://localhost:3000")
    
    # Change to project root directory
    os.chdir(PROJECT_ROOT)
    
    # Import multiprocessing for parallel execution
    from multiprocessing import Process
    
    # Create processes for backend and frontend
    backend_process = Process(target=run_backend, daemon=True)
    frontend_process = Process(target=run_frontend, daemon=True)
    
    try:
        # Start both processes
        backend_process.start()
        frontend_process.start()
        
        print("\n✅ Both services are running!")
        
        # Keep the main process alive
        backend_process.join()
        frontend_process.join()
        
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down services...")
        backend_process.terminate()
        frontend_process.terminate()
        backend_process.join(timeout=5)
        frontend_process.join(timeout=5)
        print("✅ All services stopped")
        sys.exit(0)


if __name__ == "__main__":
    main()
