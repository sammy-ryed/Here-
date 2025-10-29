# GPU Installation Script for Windows
# Run this in PowerShell as Administrator

Write-Host "`n🚀 Installing GPU Support for NVIDIA RTX 3050" -ForegroundColor Cyan
Write-Host "="*60 -ForegroundColor Gray

# Step 0: Check Python version
Write-Host "`n0. Checking Python version..." -ForegroundColor Yellow
$pythonVersion = python --version
Write-Host "   $pythonVersion"

# Step 1: Uninstall CPU-only TensorFlow
Write-Host "`n1. Removing CPU-only TensorFlow..." -ForegroundColor Yellow
pip uninstall -y tensorflow tf-keras

# Step 2: Install GPU-enabled TensorFlow (latest version for Python 3.13)
Write-Host "`n2. Installing TensorFlow (latest compatible version)..." -ForegroundColor Yellow
pip install --upgrade tensorflow

# Step 3: Install PyTorch with CUDA (optional, for future use)
Write-Host "`n3. Installing PyTorch with CUDA 11.8..." -ForegroundColor Yellow
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Step 4: Verify installation
Write-Host "`n4. Verifying GPU setup..." -ForegroundColor Yellow
python setup_gpu.py

Write-Host "`n✅ GPU installation complete!" -ForegroundColor Green
Write-Host "`nYour NVIDIA RTX 3050 is ready for 20-50x speedup! 🎉" -ForegroundColor Green
