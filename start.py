import os
import sys
import subprocess
from pathlib import Path

def main():
    root_dir = Path(__file__).parent.absolute()
    venv_dir = root_dir / ".venv"
    frontend_dir = root_dir / "frontend"

    # 1. Check if running in virtual environment
    # We check if the python executable path starts with the venv directory
    is_venv = sys.prefix != sys.base_prefix
    
    if not is_venv:
        print("Not running in virtual environment. Attempting to switch...")
        if sys.platform == "win32":
            python_executable = venv_dir / "Scripts" / "python.exe"
        else:
            python_executable = venv_dir / "bin" / "python"
            
        if python_executable.exists():
            print(f"Re-launching with {python_executable}...")
            # Re-run this script with the venv python
            try:
                subprocess.run([str(python_executable), __file__] + sys.argv[1:], check=True)
                return
            except subprocess.CalledProcessError as e:
                print(f"Error running script in venv: {e}")
                sys.exit(1)
        else:
            print("Virtual environment not found at .venv. Continuing with current Python...")

    # 2. Build Ionic Frontend
    print("\n--- Building Ionic Frontend ---")
    if not frontend_dir.exists():
        print(f"Error: Frontend directory not found at {frontend_dir}")
        sys.exit(1)

    # Check for dependency installation argument (S/N)
    # Default is 'S' (Install) if not provided
    install_deps = True
    if len(sys.argv) > 1:
        arg = sys.argv[1].upper()
        if arg == 'N':
            install_deps = False
            print("Skipping npm dependencies installation (argument 'N' provided).")
        elif arg == 'S':
            print("Installing npm dependencies (argument 'S' provided).")
    
    try:
        # Install dependencies
        if install_deps:
            print("Installing npm dependencies...")
            subprocess.run(["npm", "install"], cwd=frontend_dir, shell=True, check=True)
        
        # Build project
        print("Building Ionic project...")
        # Using npx to ensure we use the local ionic CLI if available, or download it
        subprocess.run(["npx", "ionic", "build", "--prod"], cwd=frontend_dir, shell=True, check=True)
        
    except subprocess.CalledProcessError as e:
        print(f"Error during frontend build: {e}")
        sys.exit(1)

    # 3. Start Python Backend
    print("\n--- Starting FastAPI Backend ---")
    try:
        # Run uvicorn
        # We use sys.executable to ensure we use the same python (venv)
        subprocess.run([sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"], cwd=root_dir, check=True)
    except KeyboardInterrupt:
        print("\nServer stopped by user.")
    except subprocess.CalledProcessError as e:
        print(f"Error running backend: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
