#!/usr/bin/env python
"""System verification script - checks if environment is ready."""

import sys
from pathlib import Path

def check_system():
    """Verify system requirements and setup."""
    print("=" * 80)
    print("OCR EXTRACTION PIPELINE - SYSTEM VERIFICATION")
    print("=" * 80)
    print()
    
    all_good = True
    
    # Check Python version
    print("1. Checking Python version...")
    python_version = sys.version_info
    if python_version.major >= 3 and python_version.minor >= 9:
        print(f"   ✓ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    else:
        print(f"   ✗ Python version too old: {python_version.major}.{python_version.minor}")
        print("     Requires Python 3.9+")
        all_good = False
    print()
    
    # Check PyTorch and CUDA
    print("2. Checking PyTorch and CUDA...")
    try:
        import torch
        print(f"   ✓ PyTorch version: {torch.__version__}")
        
        if torch.cuda.is_available():
            print(f"   ✓ CUDA available: True")
            print(f"   ✓ CUDA version: {torch.version.cuda}")
            num_gpus = torch.cuda.device_count()
            print(f"   ✓ Number of GPUs: {num_gpus}")
            try:
                for i in range(min(num_gpus, 8)):  # Limit to reasonable number
                    props = torch.cuda.get_device_properties(i)
                    memory_gb = props.total_memory / (1024**3)
                    print(f"     - GPU {i}: {props.name} ({memory_gb:.1f} GB)")
            except Exception as e:
                print(f"     Note: Could not query all GPU details: {e}")
        else:
            print("   ✗ CUDA not available")
            all_good = False
    except ImportError:
        print("   ✗ PyTorch not installed")
        all_good = False
    print()
    
    # Check required packages
    print("3. Checking required packages...")
    required_packages = [
        'transformers',
        'accelerate',
        'pydantic',
        'instructor',
        'pandas',
        'pdf2image',
        'PIL',
        'tqdm',
        'einops',
        'qwen_vl_utils'
    ]
    
    for package in required_packages:
        try:
            if package == 'PIL':
                __import__('PIL')
            elif package == 'qwen_vl_utils':
                __import__('qwen_vl_utils')
            else:
                __import__(package)
            print(f"   ✓ {package}")
        except ImportError:
            print(f"   ✗ {package} not installed")
            all_good = False
    print()
    
    # Check directory structure
    print("4. Checking directory structure...")
    required_dirs = [
        'src',
        'src/logs',
        'data',
        'data/input_pdfs',
        'data/output',
        'models'
    ]
    
    for dir_path in required_dirs:
        full_path = Path(dir_path)
        if full_path.exists():
            print(f"   ✓ {dir_path}/")
        else:
            print(f"   ✗ {dir_path}/ missing")
            all_good = False
    print()
    
    # Check for poppler (pdf2image dependency)
    print("5. Checking poppler (pdf2image dependency)...")
    try:
        from pdf2image import convert_from_path
        # Try to import the backend
        print("   ✓ pdf2image can be imported")
        print("   Note: Poppler must be installed separately:")
        print("     Ubuntu/Debian: sudo apt-get install poppler-utils")
        print("     macOS: brew install poppler")
    except Exception as e:
        print(f"   ✗ Error with pdf2image: {e}")
        all_good = False
    print()
    
    # Check for input PDF
    print("6. Checking for input PDF...")
    pdf_path = Path("data/input_pdfs/Plasticflowinshock-loadedsilver.pdf")
    if pdf_path.exists():
        print(f"   ✓ Found: {pdf_path}")
        print(f"     Size: {pdf_path.stat().st_size / (1024*1024):.2f} MB")
    else:
        print(f"   ⚠ Default PDF not found: {pdf_path}")
        print("     You can place your PDF in data/input_pdfs/ or update main.py")
    print()
    
    # Final summary
    print("=" * 80)
    if all_good:
        print("✓ ALL CHECKS PASSED - System is ready!")
        print()
        print("To run the pipeline:")
        print("  1. Place your PDF in data/input_pdfs/")
        print("  2. Run: python main.py")
        print("  or")
        print("  2. Run: ./run_pipeline.sh")
    else:
        print("✗ SOME CHECKS FAILED - Please fix the issues above")
    print("=" * 80)
    
    return all_good


if __name__ == "__main__":
    check_system()
