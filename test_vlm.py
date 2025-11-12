"""VLM unit test script for debugging single-page extraction."""

# Note: CUDA_VISIBLE_DEVICES should be set in the shell before running this script

import logging
import torch
from pdf2image import convert_from_path
from PIL import Image
from src.model_loader import load_vlm
from qwen_vl_utils import process_vision_info

# Configuration
VLM_DEVICE = "cuda:0"
PDF_PATH = "data/input_pdfs/sample_page.pdf"  # Put a single-page PDF here for testing

# Set up basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_vlm_single_page():
    """Test VLM on a single page."""
    logger.info("=" * 80)
    logger.info("VLM UNIT TEST - Single Page Extraction")
    logger.info("=" * 80)
    
    # Load VLM
    logger.info(f"Loading VLM (Qwen3-VL-8B-Instruct) onto {VLM_DEVICE} for testing...")
    model, processor = load_vlm(VLM_DEVICE)
    logger.info("VLM loaded successfully")
    
    # Convert first page of PDF to image
    logger.info(f"Converting first page of PDF to image: {PDF_PATH}")
    try:
        images = convert_from_path(PDF_PATH, first_page=1, last_page=1)
        image = images[0]
        logger.info(f"Image loaded successfully. Size: {image.size}")
    except Exception as e:
        logger.error(f"Error loading PDF: {e}")
        logger.info("Please place a PDF file at: data/input_pdfs/sample_page.pdf")
        return
    
    # Define test prompt
    prompt_text = """Convert this document page to high-quality markdown, identifying any tables, figures, and all text content.

Extract:
1. All text content
2. Tables (in markdown table format)
3. Figures and captions
4. Any numerical data

Be thorough and accurate."""
    
    # Construct Qwen-VL message (following official documentation)
    logger.info("Constructing VLM prompt...")
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": image},
                {"type": "text", "text": prompt_text}
            ]
        }
    ]
    
    # Process inputs (using official approach - tokenize directly)
    logger.info("Processing inputs...")
    inputs = processor.apply_chat_template(
        messages,
        tokenize=True,
        add_generation_prompt=True,
        return_dict=True,
        return_tensors="pt"
    )
    inputs = inputs.to(model.device)
    
    # Run VLM inference
    logger.info("Running VLM inference...")
    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=2048,
            temperature=0.1
        )
    
    # Decode response
    logger.info("Decoding response...")
    generated_ids = [
        output_ids[len(input_ids):]
        for input_ids, output_ids in zip(inputs.input_ids, output_ids)
    ]
    response = processor.batch_decode(
        generated_ids,
        skip_special_tokens=True,
        clean_up_tokenization_spaces=False
    )[0]
    
    # Print results
    logger.info("=" * 80)
    logger.info("VLM TEST OUTPUT:")
    logger.info("=" * 80)
    print("\n" + response + "\n")
    logger.info("=" * 80)
    logger.info("VLM test complete")
    logger.info("=" * 80)


if __name__ == "__main__":
    test_vlm_single_page()
