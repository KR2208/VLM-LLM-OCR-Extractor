#!/bin/bash
# Wrapper script to run LLM test with only GPUs 0 and 1

export CUDA_VISIBLE_DEVICES=0,1

cd "$(dirname "$0")"
source .venv/bin/activate
python test_llm.py
