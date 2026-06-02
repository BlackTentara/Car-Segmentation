"""
SegWrap Run Script
Simplified launcher for the web application
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                         SegWrap - Starting Server                            ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)

    # Check for local Miniconda
    local_conda = Path("miniconda3")

    if local_conda.exists():
        print(f"✓ Using local Miniconda: {local_conda.resolve()}")
        if sys.platform == "win32":
            # Use Python from the conda environment directly
            python_exe = local_conda / "envs" / "openmmlab" / "python.exe"
            if not python_exe.exists():
                print("✗ openmmlab environment not found!")
                print("\n  Please run setup first:")
                print("    python setup.py\n")
                sys.exit(1)
        else:
            python_exe = local_conda / "envs" / "openmmlab" / "bin" / "python"
            if not python_exe.exists():
                print("✗ openmmlab environment not found!")
                print("\n  Please run setup first:")
                print("    python setup.py\n")
                sys.exit(1)

        print(f"Starting Flask server with openmmlab environment...\n")

        # Run app.py with conda environment's Python
        try:
            subprocess.run([str(python_exe), "app.py"], check=True)
        except KeyboardInterrupt:
            print("\n\n✓ Server stopped")
        except Exception as e:
            print(f"\n✗ Error running server: {e}")
            sys.exit(1)

    else:
        # Try using system conda
        result = subprocess.run("conda env list", shell=True, capture_output=True, text=True)

        if "openmmlab" not in result.stdout:
            print("✗ Conda environment 'openmmlab' not found!")
            print("\n  Please run setup first:")
            print("    python setup.py\n")
            sys.exit(1)

        print("Starting Flask server with conda environment 'openmmlab'...\n")

        # Run app.py with conda environment
        try:
            subprocess.run("conda run -n openmmlab python app.py", shell=True, check=True)
        except KeyboardInterrupt:
            print("\n\n✓ Server stopped")
        except Exception as e:
            print(f"\n✗ Error running server: {e}")
            print("\nTry running manually:")
            print("  conda activate openmmlab")
            print("  python app.py")
            sys.exit(1)

if __name__ == "__main__":
    main()
