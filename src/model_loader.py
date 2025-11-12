"""Model loader for VLM and LLM models with GPU assignment."""

import torch
from transformers import AutoModelForCausalLM, AutoProcessor, AutoTokenizer, Qwen3VLForConditionalGeneration
from pathlib import Path
from src.logger_config import logger

# Model cache directory
MODEL_CACHE_DIR = "/home/krameshbabu/Alloy/OCR/models"

# Model URLs for reference:
# VLM: https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct
# LLM: https://huggingface.co/Qwen/Qwen2.5-7B-Instruct


def load_vlm(device: str = "cuda:0"):
    """Load the Qwen3-VL-8B-Instruct vision-language model.
    
    Args:
        device: Target device (e.g., 'cuda:0')
        
    Returns:
        tuple: (model, processor)
    """
    logger.info(f"Loading VLM (Qwen3-VL-8B-Instruct) to {device}...")
    
    model_name = "Qwen/Qwen3-VL-8B-Instruct"
    
    try:
        # Load processor
        processor = AutoProcessor.from_pretrained(
            model_name,
            cache_dir=MODEL_CACHE_DIR,
            trust_remote_code=True
        )
        
        # Load model using the correct Qwen3VLForConditionalGeneration class
        # Load on CPU first, then move to GPU to avoid device_map issues
        model = Qwen3VLForConditionalGeneration.from_pretrained(
            model_name,
            cache_dir=MODEL_CACHE_DIR,
            torch_dtype=torch.bfloat16,
            trust_remote_code=True,
            device_map=None  # Load on CPU first
        )
        
        # Force CUDA re-initialization before moving model
        if torch.cuda.is_available():
            torch.cuda.init()
            torch.cuda.empty_cache()
            logger.info(f"CUDA re-initialized. Available devices: {torch.cuda.device_count()}")
        
        # Move model to the specified device
        model = model.to(device)
        model.eval()
        
        logger.info(f"VLM loaded successfully on {device}")
        return model, processor
        
    except Exception as e:
        logger.error(f"Error loading VLM: {e}")
        raise


def load_llm(device: str = "cuda:1"):
    """Load the Qwen2.5-7B-Instruct language model in full precision.
    
    Args:
        device: Target device (e.g., 'cuda:1')
        
    Returns:
        tuple: (model, tokenizer)
    """
    logger.info(f"Loading LLM (Qwen2.5-7B-Instruct) to {device}...")
    
    model_name = "Qwen/Qwen2.5-7B-Instruct"
    
    try:
        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            cache_dir=MODEL_CACHE_DIR,
            trust_remote_code=True
        )
        
        # Load model in bfloat16 (full precision, not 4-bit)
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            cache_dir=MODEL_CACHE_DIR,
            torch_dtype=torch.bfloat16,
            trust_remote_code=True,
            device_map=None  # We'll manually move to device
        )
        
        # Move model to specified device
        model = model.to(device)
        model.eval()
        
        logger.info(f"LLM loaded successfully on {device}")
        return model, tokenizer
        
    except Exception as e:
        logger.error(f"Error loading LLM: {e}")
        raise
