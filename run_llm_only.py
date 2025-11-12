#!/usr/bin/env python3
"""Run ONLY the LLM extraction stage (assumes fragments already exist)."""

import json
import sys
from pathlib import Path
from src.logger_config import logger
from src.llm_extractor import DataExtractor
from src.schema import SpallExperiment
import pandas as pd


def main():
    """Run LLM extraction on existing fragments."""
    
    logger.info("="*80)
    logger.info("LLM-ONLY EXTRACTION STAGE")
    logger.info("="*80)
    
    # Paths
    fragments_path = Path("data/output/intermediate_fragments.json")
    output_csv = Path("data/output/extracted_database.csv")
    
    # Check if fragments exist
    if not fragments_path.exists():
        logger.error(f"Fragments file not found: {fragments_path}")
        logger.error("Run the VLM stage first with: python run_vlm_stage.py")
        sys.exit(1)
    
    # Load fragments
    logger.info(f"Loading fragments from: {fragments_path}")
    with open(fragments_path, 'r') as f:
        fragments_dict = json.load(f)
    
    logger.info(f"Loaded fragments for {len(fragments_dict)} topics")
    total_fragments = sum(len(frags) for frags in fragments_dict.values())
    logger.info(f"Total fragments: {total_fragments}")
    
    # Initialize LLM extractor (will use GPU 0 since VLM is not loaded)
    logger.info("Initializing LLM on cuda:0...")
    extractor = DataExtractor(device="cuda:0")
    
    # Extract structured data
    logger.info("="*80)
    logger.info("Extracting structured data with LLM...")
    logger.info("="*80)
    
    try:
        experiments = extractor.extract_data(fragments_dict)
        
        if not experiments:
            logger.warning("No experiments extracted!")
            sys.exit(1)
        
        logger.info(f"Extracted {len(experiments)} experiments")
        
        # Convert to DataFrame
        logger.info("Converting to CSV...")
        df = pd.DataFrame([exp.dict() for exp in experiments])
        
        # Save to CSV
        output_csv.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_csv, index=False)
        logger.info(f"Saved results to: {output_csv}")
        
        # Print summary
        logger.info("="*80)
        logger.info("EXTRACTION COMPLETE")
        logger.info("="*80)
        logger.info(f"Total experiments: {len(experiments)}")
        logger.info(f"Output file: {output_csv}")
        
        # Print first few rows
        print("\nFirst few experiments:")
        print(df.head().to_string())
        
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
