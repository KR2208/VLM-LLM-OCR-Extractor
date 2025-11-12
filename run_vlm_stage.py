"""Stage 1: VLM Analysis - Extract fragments from PDF using Vision Language Model."""

import json
import gc
import torch
from pathlib import Path
from src.logger_config import logger
from src.vlm_processor import PDFAnalyzer

# GPU assignment
VLM_DEVICE = "cuda:0"  # VLM on GPU 0

# File paths
PDF_INPUT_PATH = 'data/input_pdfs/paper1.pdf'
FRAGMENTS_OUTPUT_PATH = 'data/output/intermediate_fragments.json'


def main():
    """Run VLM analysis stage only."""
    
    logger.info("=" * 80)
    logger.info("STAGE 1: VLM ANALYSIS")
    logger.info("=" * 80)
    logger.info(f"VLM Device: {VLM_DEVICE}")
    logger.info(f"Input PDF: {PDF_INPUT_PATH}")
    logger.info(f"Output: {FRAGMENTS_OUTPUT_PATH}")
    logger.info("=" * 80)
    
    # Check if input PDF exists
    if not Path(PDF_INPUT_PATH).exists():
        logger.error(f"Input PDF not found: {PDF_INPUT_PATH}")
        logger.info("Please place your PDF file in the data/input_pdfs/ directory")
        return
    
    # Initialize VLM
    logger.info(f"Initializing VLM (Qwen3-VL-8B) on {VLM_DEVICE}...")
    analyzer = PDFAnalyzer(device=VLM_DEVICE)
    logger.info("VLM initialization complete")
    
    # Run VLM analysis
    logger.info(f"Analyzing PDF: {PDF_INPUT_PATH}")
    try:
        structured_data = analyzer.run_analysis(PDF_INPUT_PATH)
        logger.info("VLM analysis complete")
    except Exception as e:
        logger.error(f"Error during VLM analysis: {e}")
        raise
    
    # Save structured data
    logger.info(f"Saving structured data to {FRAGMENTS_OUTPUT_PATH}...")
    try:
        Path(FRAGMENTS_OUTPUT_PATH).parent.mkdir(parents=True, exist_ok=True)
        with open(FRAGMENTS_OUTPUT_PATH, 'w') as f:
            json.dump(structured_data, f, indent=2)
        logger.info("Structured data saved successfully")
        
        # Print summary
        pages_data = structured_data.get("pages", [])
        total_tables = sum(len(p.get("tables", [])) for p in pages_data)
        total_figures = sum(len(p.get("figures", [])) for p in pages_data)
        total_text = sum(len(p.get("text_sections", [])) for p in pages_data)
        
        logger.info("=" * 80)
        logger.info("VLM STAGE SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total pages processed: {len(pages_data)}")
        logger.info(f"Tables extracted: {total_tables}")
        logger.info(f"Figures extracted: {total_figures}")
        logger.info(f"Text sections extracted: {total_text}")
        logger.info(f"Output: {FRAGMENTS_OUTPUT_PATH}")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"Could not save fragments: {e}")
        raise
    
    # Clean up GPU memory
    del analyzer
    gc.collect()
    torch.cuda.empty_cache()
    logger.info("GPU memory cleared")
    logger.info("VLM stage complete!")


if __name__ == "__main__":
    main()
