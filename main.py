"""Main orchestrator for the three-stage PDF extraction pipeline."""

# Note: CUDA_VISIBLE_DEVICES should be set in the shell before running this script
# to avoid GPU 3 hardware issue

import json
import pandas as pd
from pathlib import Path
from src.logger_config import logger
from src.vlm_processor import PDFAnalyzer
from src.llm_extractor import DataExtractor

# GPU assignments
VLM_DEVICE = "cuda:0"  # VLM on GPU 0
LLM_DEVICE = "cuda:1"  # LLM on GPU 1

# File paths
PDF_INPUT_PATH = 'data/input_pdfs/paper1.pdf'
CSV_OUTPUT_PATH = 'data/output/extracted_database.csv'
FRAGMENTS_OUTPUT_PATH = 'data/output/intermediate_fragments.json'


def main():
    """Run the complete three-stage extraction pipeline."""
    
    logger.info("=" * 80)
    logger.info("SCIENTIFIC PAPER DATA EXTRACTION PIPELINE")
    logger.info("=" * 80)
    logger.info(f"VLM Device: {VLM_DEVICE}")
    logger.info(f"LLM Device: {LLM_DEVICE}")
    logger.info(f"Input PDF: {PDF_INPUT_PATH}")
    logger.info("=" * 80)
    
    # Check if input PDF exists
    if not Path(PDF_INPUT_PATH).exists():
        logger.error(f"Input PDF not found: {PDF_INPUT_PATH}")
        logger.info("Please place your PDF file in the data/input_pdfs/ directory")
        return
    
    # Initialize components
    logger.info(f"Initializing VLM (Qwen3-VL-8B) on {VLM_DEVICE} and LLM (Qwen2.5-7B) on {LLM_DEVICE}...")
    analyzer = PDFAnalyzer(device=VLM_DEVICE)
    extractor = DataExtractor(device=LLM_DEVICE)
    logger.info("Initialization complete")
    
    # STAGE 1: VLM Analysis (Index + Fragment Extraction)
    logger.info("=" * 80)
    logger.info(f"STAGE 1: Analyzing PDF with VLM: {PDF_INPUT_PATH}")
    logger.info("=" * 80)
    
    try:
        fragments_dict = analyzer.run_analysis(PDF_INPUT_PATH)
        logger.info("VLM analysis complete")
    except Exception as e:
        logger.error(f"Error during VLM analysis: {e}")
        raise
    
    # Save intermediate fragments
    logger.info(f"Saving fragments to {FRAGMENTS_OUTPUT_PATH}...")
    try:
        with open(FRAGMENTS_OUTPUT_PATH, 'w') as f:
            json.dump(fragments_dict, f, indent=2)
        logger.info("Fragments saved successfully")
    except Exception as e:
        logger.warning(f"Could not save fragments: {e}")
    
    # STAGE 2: LLM Extraction
    logger.info("=" * 80)
    logger.info("STAGE 2: Extracting structured data with LLM")
    logger.info("=" * 80)
    
    try:
        extracted_data = extractor.extract_data(fragments_dict)
        logger.info(f"LLM extraction complete. Found {len(extracted_data)} experiments")
    except Exception as e:
        logger.error(f"Error during LLM extraction: {e}")
        raise
    
    # STAGE 3: Save results
    logger.info("=" * 80)
    logger.info(f"STAGE 3: Saving results to {CSV_OUTPUT_PATH}")
    logger.info("=" * 80)
    
    try:
        # Convert Pydantic models to dictionaries with CSV headers
        data_dicts = [item.model_dump(by_alias=True) for item in extracted_data]
        
        # Create DataFrame and save to CSV
        df = pd.DataFrame(data_dicts)
        df.to_csv(CSV_OUTPUT_PATH, index=False)
        logger.info(f"Data saved successfully to {CSV_OUTPUT_PATH}")
        
        # Print summary
        logger.info("=" * 80)
        logger.info("EXTRACTION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total experiments extracted: {len(extracted_data)}")
        logger.info(f"Total columns: {len(df.columns)}")
        logger.info(f"Output CSV: {CSV_OUTPUT_PATH}")
        logger.info(f"Intermediate fragments: {FRAGMENTS_OUTPUT_PATH}")
        logger.info("=" * 80)
        logger.info("Pipeline complete!")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"Error saving results: {e}")
        raise


if __name__ == "__main__":
    main()
