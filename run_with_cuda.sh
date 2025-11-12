#!/bin/bash
# Wrapper script to run Python commands with correct CUDA settings

export CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7

# Activate virtual environment
source .venv/bin/activate

# Run the provided command
"$@"
