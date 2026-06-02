"""
SegWrap Setup Script
Automatically sets up conda environment and dependencies for web application
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Run a shell command and handle errors"""
    print(f"\n{'='*80}")
    print(f"{description}")
    print(f"{'='*80}")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Error: {e}")
        if e.stderr:
            print(e.stderr)
        return False

def main():
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                         SegWrap Setup - Web Application                      ║
║                                                                              ║
║  This will install all dependencies for the web application                 ║
║  Estimated time: 5-10 minutes                                                ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)

    # Check for local Miniconda first
    local_conda = Path("miniconda3")
    if local_conda.exists():
        print(f"✓ Using local Miniconda: {local_conda.resolve()}")
        if sys.platform == "win32":
            conda_exe = str(local_conda / "Scripts" / "conda.exe")
        else:
            conda_exe = str(local_conda / "bin" / "conda")
    else:
        # Try system conda
        try:
            subprocess.run("conda --version", shell=True, check=True, capture_output=True)
            conda_exe = "conda"
            print("✓ Using system Conda")
        except:
            print("✗ Conda not found! Please install Miniconda first:")
            print("  https://docs.conda.io/en/latest/miniconda.html")
            sys.exit(1)

    # Check if openmmlab environment exists
    result = subprocess.run(f'"{conda_exe}" env list', shell=True, capture_output=True, text=True)
    env_exists = "openmmlab" in result.stdout

    if not env_exists:
        print("\n📦 Creating conda environment 'openmmlab'...")
        if not run_command("conda create --name openmmlab python=3.8 -y", "Creating Python 3.8 environment"):
            sys.exit(1)
    else:
        print("\n✓ Conda environment 'openmmlab' already exists")

    # Install PyTorch
    print("\n🔥 Installing PyTorch...")
    if not run_command(
        "conda run -n openmmlab pip install torch==2.1.2 torchvision==0.16.2 torchaudio==2.1.2 --index-url https://download.pytorch.org/whl/cu121",
        "Installing PyTorch 2.1.2 with CUDA 12.1"
    ):
        print("⚠️  Warning: PyTorch installation failed, trying CPU version...")
        run_command(
            "conda run -n openmmlab pip install torch torchvision torchaudio",
            "Installing PyTorch (CPU version)"
        )

    # Install basic dependencies
    print("\n📦 Installing basic dependencies...")
    run_command(
        'conda run -n openmmlab pip install "numpy<2" ninja setuptools wheel',
        "Installing build tools"
    )

    # Install MMCV
    print("\n🔧 Installing MMCV...")
    if not run_command(
        "conda run -n openmmlab pip install https://download.openmmlab.com/mmcv/dist/cu121/torch2.1.0/mmcv-2.1.0-cp38-cp38-manylinux1_x86_64.whl",
        "Installing MMCV 2.1.0"
    ):
        print("⚠️  Warning: MMCV wheel failed, trying pip install...")
        run_command(
            "conda run -n openmmlab pip install openmim",
            "Installing OpenMIM"
        )
        run_command(
            "conda run -n openmmlab mim install mmengine mmcv",
            "Installing MMCV via MIM"
        )

    # Install MMDetection
    mmdet_path = Path("mmdetection")
    if mmdet_path.exists():
        print("\n🎯 Installing MMDetection from local folder...")
        run_command(
            "conda run -n openmmlab pip install -e mmdetection",
            "Installing MMDetection (editable)"
        )
    else:
        print("\n🎯 Cloning and installing MMDetection...")
        run_command(
            "git clone https://github.com/open-mmlab/mmdetection.git",
            "Cloning MMDetection repository"
        )
        run_command(
            "conda run -n openmmlab pip install -e mmdetection",
            "Installing MMDetection (editable)"
        )

    # Install other dependencies
    print("\n📦 Installing other dependencies...")
    run_command(
        "conda run -n openmmlab pip install flask flask-cors ultralytics rembg pycocotools",
        "Installing Flask, YOLO, rembg, and COCO tools"
    )

    # Install EfficientSAM
    print("\n🎨 Installing EfficientSAM...")
    run_command(
        "conda run -n openmmlab pip install git+https://github.com/yformer/EfficientSAM.git",
        "Installing EfficientSAM from GitHub"
    )

    print(f"\n{'='*80}")
    print("✅ Setup complete!")
    print(f"{'='*80}")
    print("\nTo run the application:")
    print("  python run.py")
    print("\nOr manually:")
    print("  conda activate openmmlab")
    print("  python app.py")
    print(f"\n{'='*80}\n")

if __name__ == "__main__":
    main()
