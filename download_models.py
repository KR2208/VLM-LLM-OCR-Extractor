"""Script to download and cache models before running the pipeline."""

import os
# Set CUDA devices before importing torch
os.environ['CUDA_VISIBLE_DEVICES'] = '0,1,2,3,4,5,6,7'

import torch
from transformers import AutoModelForCausalLM, AutoProcessor, AutoTokenizer, AutoModel
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Model cache directory
MODEL_CACHE_DIR = "/home/krameshbabu/Alloy/OCR/models"

# Model names
VLM_MODEL = "Qwen/Qwen3-VL-8B-Instruct"
LLM_MODEL = "Qwen/Qwen2.5-7B-Instruct"


def download_vlm():
    """Download the VLM model and processor."""
    logger.info("=" * 80)
    logger.info(f"Downloading VLM: {VLM_MODEL}")
    logger.info("=" * 80)
    logger.info("This will download ~16-18 GB. Please be patient...")
    logger.info(f"Cache directory: {MODEL_CACHE_DIR}")
    
    try:
        # Download processor
        logger.info("Downloading VLM processor...")
        processor = AutoProcessor.from_pretrained(
            VLM_MODEL,
            cache_dir=MODEL_CACHE_DIR,
            trust_remote_code=True
        )
        logger.info("✓ VLM processor downloaded")
        
        # Download model
        logger.info("Downloading VLM model (this may take 10-30 minutes)...")
        model = AutoModel.from_pretrained(
            VLM_MODEL,
            cache_dir=MODEL_CACHE_DIR,
            torch_dtype=torch.bfloat16,
            trust_remote_code=True
        )
        logger.info("✓ VLM model downloaded successfully")
        
        # Clean up memory
        del model
        del processor
        torch.cuda.empty_cache()
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Error downloading VLM: {e}")
        return False


def download_llm():
    """Download the LLM model and tokenizer."""
    logger.info("=" * 80)
    logger.info(f"Downloading LLM: {LLM_MODEL}")
    logger.info("=" * 80)
    logger.info("This will download ~14-16 GB. Please be patient...")
    logger.info(f"Cache directory: {MODEL_CACHE_DIR}")
    
    try:
        # Download tokenizer
        logger.info("Downloading LLM tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(
            LLM_MODEL,
            cache_dir=MODEL_CACHE_DIR,
            trust_remote_code=True
        )
        logger.info("✓ LLM tokenizer downloaded")
        
        # Download model
        logger.info("Downloading LLM model (this may take 10-30 minutes)...")
        model = AutoModelForCausalLM.from_pretrained(
            LLM_MODEL,
            cache_dir=MODEL_CACHE_DIR,
            torch_dtype=torch.bfloat16,
            trust_remote_code=True
        )
        logger.info("✓ LLM model downloaded successfully")
        
        # Clean up memory
        del model
        del tokenizer
        torch.cuda.empty_cache()
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Error downloading LLM: {e}")
        return False


def check_disk_space():
    """Check if there's enough disk space."""
    import shutil
    
    stat = shutil.disk_usage(MODEL_CACHE_DIR)
    free_gb = stat.free / (1024**3)
    
    logger.info(f"Available disk space: {free_gb:.1f} GB")
    
    if free_gb < 35:
        logger.warning(f"⚠️  Low disk space! You need at least 35 GB free.")
        logger.warning(f"   Currently available: {free_gb:.1f} GB")
        return False
    else:
        logger.info("✓ Sufficient disk space available")
        return True


def main():
    """Download both models."""
    logger.info("=" * 80)
    logger.info("MODEL DOWNLOAD SCRIPT")
    logger.info("=" * 80)
    logger.info("This script will download:")
    logger.info(f"  1. VLM: {VLM_MODEL} (~16-18 GB)")
    logger.info(f"  2. LLM: {LLM_MODEL} (~14-16 GB)")
    logger.info(f"  Total: ~30-35 GB")
    logger.info("=" * 80)
    
    # Check disk space
    if not check_disk_space():
        logger.error("Insufficient disk space. Please free up space and try again.")
        return
    
    # Check CUDA
    logger.info(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        logger.info(f"Number of GPUs: {torch.cuda.device_count()}")
    logger.info("")
    
    # Download VLM
    logger.info("Step 1/2: Downloading VLM...")
    vlm_success = download_vlm()
    logger.info("")
    
    if not vlm_success:
        logger.error("VLM download failed. Please check the error and try again.")
        return
    
    # Download LLM
    logger.info("Step 2/2: Downloading LLM...")
    llm_success = download_llm()
    logger.info("")
    
    if not llm_success:
        logger.error("LLM download failed. Please check the error and try again.")
        return
    
    # Summary
    logger.info("=" * 80)
    logger.info("✓ ALL MODELS DOWNLOADED SUCCESSFULLY!")
    logger.info("=" * 80)
    logger.info(f"Models cached in: {MODEL_CACHE_DIR}")
    logger.info("")
    logger.info("Next steps:")
    logger.info("  1. Place your PDF in: data/input_pdfs/paper1.pdf")
    logger.info("  2. Run the pipeline: python main.py")
    logger.info("     or use: ./run_pipeline.sh")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
