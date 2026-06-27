# Car Segmentation Setup Journal

## Step 1 — Clone the Repository

```bash
git clone https://github.com/BlackTentara/Car-Segmentation
cd Car-Segmentation
```

## Step 2 — Navigate to the Web Demo Folder

```bash
cd web_skripsi
```

## Step 3 — Install Miniconda3 (local, inside web_skripsi)

Run this from inside `web_skripsi/`:

```powershell
curl https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe -o miniconda_installer.exe; Start-Process -Wait -FilePath ".\miniconda_installer.exe" -ArgumentList "/S /D=$PWD\miniconda3"
```

## Step 4 — Run Setup

```bash
python setup.py
```

## Step 5 — Copy Model Configs

After setup, MMDetection is cloned into `web_skripsi/mmdetection/`. You need to copy the provided config files into it:

```powershell
mkdir mmdetection\configs\testing
copy testing_configs\* mmdetection\configs\testing\
```

## Step 6 — Run the App

```bash
python run.py
```

Open your browser at: http://localhost:5000
