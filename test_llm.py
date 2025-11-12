"""LLM unit test script to verify CUDA/PyTorch functionality."""

# Note: CUDA_VISIBLE_DEVICES should be set in the shell before running this script

import logging
import torch
from src.model_loader import load_llm

# Configuration
LLM_DEVICE = "cuda:0"

# Set up basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_llm():
    """Test LLM loading and basic inference."""
    logger.info("=" * 80)
    logger.info("LLM UNIT TEST - Basic Inference")
    logger.info("=" * 80)
    
    # Check CUDA availability first (without querying device names to avoid GPU 3 issue)
    logger.info(f"CUDA available: {torch.cuda.is_available()}")
    logger.info(f"CUDA device count: {torch.cuda.device_count()}")
    logger.info("Skipping device name queries to avoid GPU 3 driver issue...")
    
    # Load LLM
    logger.info(f"\nLoading LLM (Qwen2.5-7B-Instruct) onto {LLM_DEVICE}...")
    model, tokenizer = load_llm(LLM_DEVICE)
    logger.info("LLM loaded successfully")
    
    # Test prompt
    test_prompt = "Hello! Please respond with a short greeting."
    
    logger.info(f"\nTest prompt: {test_prompt}")
    
    # Tokenize
    logger.info("Tokenizing input...")
    messages = [
        {"role": "user", "content": test_prompt}
    ]
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )
    inputs = tokenizer([text], return_tensors="pt").to(LLM_DEVICE)
    
    # Generate
    logger.info("Running LLM inference...")
    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=50,
            temperature=0.7
        )
    
    # Decode
    logger.info("Decoding response...")
    generated_ids = [
        output_ids[len(input_ids):]
        for input_ids, output_ids in zip(inputs.input_ids, output_ids)
    ]
    response = tokenizer.batch_decode(
        generated_ids,
        skip_special_tokens=True,
        clean_up_tokenization_spaces=False
    )[0]
    
    # Print results
    logger.info("=" * 80)
    logger.info("LLM TEST OUTPUT:")
    logger.info("=" * 80)
    print(f"\n{response}\n")
    logger.info("=" * 80)
    logger.info("LLM test complete - SUCCESS!")
    logger.info("=" * 80)


if __name__ == "__main__":
    test_llm()
