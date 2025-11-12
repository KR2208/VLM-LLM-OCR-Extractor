"""Stage 2: LLM Extraction - Extract structured data from fragments using Language Model."""

import json
import pandas as pd
from pathlib import Path
from src.logger_config import logger
from src.llm_extractor import DataExtractor

# GPU assignment
LLM_DEVICE = "cuda:1"  # LLM on GPU 1

# File paths
FRAGMENTS_INPUT_PATH = 'data/output/intermediate_fragments.json'
CSV_OUTPUT_PATH = 'data/output/extracted_database.csv'


def main():
    """Run LLM extraction stage only."""
    
    logger.info("=" * 80)
    logger.info("STAGE 2: LLM EXTRACTION")
    logger.info("=" * 80)
    logger.info(f"LLM Device: {LLM_DEVICE}")
    logger.info(f"Input: {FRAGMENTS_INPUT_PATH}")
    logger.info(f"Output: {CSV_OUTPUT_PATH}")
    logger.info("=" * 80)
    
    # Check if fragments file exists
    if not Path(FRAGMENTS_INPUT_PATH).exists():
        logger.error(f"Fragments file not found: {FRAGMENTS_INPUT_PATH}")
        logger.info("Please run the VLM stage first (run_vlm_stage.py)")
        return
    
    # Load fragments
    logger.info(f"Loading fragments from {FRAGMENTS_INPUT_PATH}...")
    try:
        with open(FRAGMENTS_INPUT_PATH, 'r') as f:
            fragments_dict = json.load(f)
        total_fragments = sum(len(v) for v in fragments_dict.values() if isinstance(v, list))
        logger.info(f"Loaded {total_fragments} fragments")
    except Exception as e:
        logger.error(f"Error loading fragments: {e}")
        raise
    
    # Initialize LLM
    logger.info(f"Initializing LLM (Qwen2.5-7B) on {LLM_DEVICE}...")
    extractor = DataExtractor(device=LLM_DEVICE)
    logger.info("LLM initialization complete")
    
    # Run extraction with batching to avoid OOM
    logger.info("Extracting structured data with LLM...")
    try:
        extracted_data = extractor.extract_data(fragments_dict)
        logger.info(f"LLM extraction complete. Found {len(extracted_data)} experiments")
    except Exception as e:
        logger.error(f"Error during LLM extraction: {e}")
        raise
    
    # Save results
    logger.info(f"Saving results to {CSV_OUTPUT_PATH}...")
    try:
        # Convert Pydantic models to dictionaries with CSV headers
        data_dicts = [item.model_dump(by_alias=True) for item in extracted_data]
        
        # Create DataFrame and save to CSV
        Path(CSV_OUTPUT_PATH).parent.mkdir(parents=True, exist_ok=True)
        df = pd.DataFrame(data_dicts)
        df.to_csv(CSV_OUTPUT_PATH, index=False)
        logger.info(f"Data saved successfully to {CSV_OUTPUT_PATH}")
        
        # Print summary
        logger.info("=" * 80)
        logger.info("LLM STAGE SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total experiments extracted: {len(extracted_data)}")
        logger.info(f"Total columns: {len(df.columns)}")
        logger.info(f"Output CSV: {CSV_OUTPUT_PATH}")
        logger.info("=" * 80)
        logger.info("LLM stage complete!")
        
    except Exception as e:
        logger.error(f"Error saving results: {e}")
        raise


if __name__ == "__main__":
    main()
