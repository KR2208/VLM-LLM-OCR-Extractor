#!/bin/bash
# Wrapper script to run VLM test with only GPUs 0 and 1 (avoiding GPU 3 issue)

export CUDA_VISIBLE_DEVICES=0,1

cd "$(dirname "$0")"
source .venv/bin/activate
python test_vlm.py
