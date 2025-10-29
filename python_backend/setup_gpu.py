"""
GPU Setup and Verification Script
Run this to check if GPU is working properly
"""

import os
import sys

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Reduce TensorFlow logging

# Try importing TensorFlow
try:
    import tensorflow as tf
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    print("\n⚠️  TensorFlow not installed!")
    print("   Run: pip install --upgrade tensorflow")

# Try importing PyTorch
try:
    import torch
    PYTORCH_AVAILABLE = True
except ImportError:
    PYTORCH_AVAILABLE = False
    print("\n⚠️  PyTorch not installed!")
    print("   Run: pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118")

def check_tensorflow_gpu():
    if not TENSORFLOW_AVAILABLE:
        print("\n" + "="*60)
        print("TensorFlow GPU Check")
        print("="*60)
        print("\n❌ TensorFlow is not installed")
        print("   Install with: pip install --upgrade tensorflow")
        return False
    
    print("\n" + "="*60)
    print("TensorFlow GPU Check")
    print("="*60)
    
    print(f"\nTensorFlow Version: {tf.__version__}")
    
    gpus = tf.config.list_physical_devices('GPU')
    print(f"\nGPUs Available: {len(gpus)}")
    
    for gpu in gpus:
        print(f"  - {gpu.name}")
        try:
            details = tf.config.experimental.get_device_details(gpu)
            print(f"    Device: {details.get('device_name', 'Unknown')}")
        except:
            print(f"    Device: GPU detected")
    
    if gpus:
        print("\n✅ TensorFlow CAN use GPU!")
        
        # Test GPU computation
        print("\nTesting GPU computation...")
        try:
            with tf.device('/GPU:0'):
                a = tf.random.normal([1000, 1000])
                b = tf.random.normal([1000, 1000])
                c = tf.matmul(a, b)
            print("✅ GPU computation successful!")
        except Exception as e:
            print(f"⚠️  GPU computation test failed: {e}")
        
        return True
    else:
        print("\n❌ No GPU detected by TensorFlow")
        print("   TensorFlow might still work on CPU")
        return False

def check_pytorch_gpu():
    if not PYTORCH_AVAILABLE:
        print("\n" + "="*60)
        print("PyTorch GPU Check")
        print("="*60)
        print("\n❌ PyTorch is not installed")
        print("   Install with: pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118")
        return False
    
    print("\n" + "="*60)
    print("PyTorch GPU Check")
    print("="*60)
    
    print(f"\nPyTorch Version: {torch.__version__}")
    print(f"CUDA Available: {torch.cuda.is_available()}")
    
    if torch.cuda.is_available():
        print(f"CUDA Version: {torch.version.cuda}")
        print(f"GPU Count: {torch.cuda.device_count()}")
        
        for i in range(torch.cuda.device_count()):
            print(f"\nGPU {i}:")
            print(f"  Name: {torch.cuda.get_device_name(i)}")
            print(f"  Memory: {torch.cuda.get_device_properties(i).total_memory / 1024**3:.2f} GB")
        
        # Test GPU computation
        print("\nTesting GPU computation...")
        device = torch.device('cuda')
        x = torch.randn(1000, 1000).to(device)
        y = torch.randn(1000, 1000).to(device)
        z = torch.mm(x, y)
        print("✅ GPU computation successful!")
        
        return True
    else:
        print("\n❌ CUDA not available")
        print("Install: pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118")
        return False

def check_nvidia_driver():
    print("\n" + "="*60)
    print("NVIDIA Driver Check")
    print("="*60)
    
    import subprocess
    try:
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
        print(result.stdout)
        return True
    except FileNotFoundError:
        print("\n❌ nvidia-smi not found")
        print("Install NVIDIA drivers from: https://www.nvidia.com/Download/index.aspx")
        return False

if __name__ == "__main__":
    print("\n🔍 Checking GPU Setup for Face Recognition System")
    print("="*60)
    
    # Check NVIDIA driver
    nvidia_ok = check_nvidia_driver()
    
    # Check TensorFlow GPU
    tf_ok = check_tensorflow_gpu()
    
    # Check PyTorch GPU
    pytorch_ok = check_pytorch_gpu()
    
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    print(f"NVIDIA Driver: {'✅' if nvidia_ok else '❌'}")
    print(f"TensorFlow GPU: {'✅' if tf_ok else '❌'}")
    print(f"PyTorch GPU: {'✅' if pytorch_ok else '❌'}")
    
    if nvidia_ok and (tf_ok or pytorch_ok):
        print("\n🎉 GPU is ready for face recognition!")
        print("Your NVIDIA RTX 3050 will provide 20-50x speedup!")
    else:
        print("\n⚠️ GPU setup incomplete. Follow installation instructions above.")
