#!/usr/bin/env python3
"""
Start Rasta Voice Pipeline - Ensures only one instance runs
"""
import subprocess
import sys
import time
from pathlib import Path

def kill_existing_pipelines():
    """Kill any existing rasta_live.py processes using PID file"""
    pid_file = Path(__file__).parent / "pipeline.pid"

    # Check if PID file exists
    if pid_file.exists():
        try:
            with open(pid_file) as f:
                old_pid = f.read().strip()

            print(f"Found existing pipeline PID: {old_pid}")

            # Kill the process (works on Windows)
            subprocess.run(['taskkill', '/F', '/PID', old_pid, '/T'],
                          stderr=subprocess.DEVNULL,
                          stdout=subprocess.DEVNULL)

            time.sleep(1)  # Give process time to die
            pid_file.unlink()  # Remove PID file
            print("Killed existing pipeline process")
        except Exception as e:
            print(f"Note: Could not kill old process (may already be dead): {e}")
            try:
                pid_file.unlink()
            except:
                pass
    else:
        print("No existing pipeline found")

def start_pipeline():
    """Start the pipeline with proper device configuration"""
    venv_python = Path(__file__).parent / "venv" / "Scripts" / "python.exe"
    rasta_script = Path(__file__).parent / "rasta_live.py"

    # Auto-detect all devices - rasta_live.py finds:
    #   VB-Cable Input (48kHz WASAPI) for Twitter
    #   Headphones (48kHz WASAPI) for monitoring
    #   Windows default mic for input

    cmd = [
        str(venv_python),
        str(rasta_script),
        # All devices auto-detected - no hardcoded IDs
    ]

    print("Starting rasta voice pipeline...")
    print(f"Command: {' '.join(cmd)}")

    # Start the process
    process = subprocess.Popen(cmd)
    pid = process.pid

    # Save PID to file
    pid_file = Path(__file__).parent / "pipeline.pid"
    with open(pid_file, 'w') as f:
        f.write(str(pid))

    print(f"Pipeline started! (PID: {pid})")

if __name__ == "__main__":
    print("=" * 60)
    print("RASTA VOICE PIPELINE STARTER")
    print("=" * 60)

    # Kill any existing instances first
    kill_existing_pipelines()

    # Start fresh instance
    start_pipeline()

    print("\nPipeline is now running in the background")
    print("Audio routing: auto-detected (check pipeline logs for details)")
