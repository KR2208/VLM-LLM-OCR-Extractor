#!/bin/bash
# Simple VLM test with proper CUDA environment

# Use first 2 GPUs only (VLM on 0, LLM on 1)
export CUDA_VISIBLE_DEVICES=0,1

# Activate virtual environment
source .venv/bin/activate

# Run test
echo "=========================================="
echo "Running VLM Test (Simple)"
echo "CUDA_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES"
echo "=========================================="

python3 -c "
import torch
print(f'PyTorch CUDA available: {torch.cuda.is_available()}')
print(f'Number of GPUs visible: {torch.cuda.device_count()}')
for i in range(torch.cuda.device_count()):
    print(f'  GPU {i}: {torch.cuda.get_device_name(i)}')
"

echo ""
echo "Running VLM inference test..."
python3 test_vlm.py
