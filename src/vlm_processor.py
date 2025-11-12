"""VLM processor orchestrator for PDF analysis."""

import json
from pdf2image import convert_from_path
from src.logger_config import logger
from src.vlm_indexer import PDFIndexer


class PDFAnalyzer:
    """Orchestrates the two-step VLM analysis: indexing and extraction."""
    
    def __init__(self, device: str = "cuda:0"):
        """Initialize the PDF analyzer.
        
        Args:
            device: GPU device for VLM
        """
        logger.info(f"Initializing PDFAnalyzer on {device}")
        self.indexer = PDFIndexer(device)
        logger.info("PDFAnalyzer initialized successfully")
    
    def run_analysis(self, pdf_path: str) -> dict:
        """Run the complete two-step VLM analysis on a PDF.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary mapping topics to text fragments
        """
        logger.info(f"Starting PDF analysis for: {pdf_path}")
        
        # Step 0: Convert PDF to images
        logger.info("Converting PDF to images...")
        images = convert_from_path(pdf_path)
        logger.info(f"PDF converted to {len(images)} pages")
        
        # Step 1: Create document index
        logger.info("Step 1: Creating document index...")
        document_index = self.indexer.create_index(images)
        logger.info(f"Index created with {len(document_index)} elements")
        
        # Optional: Save the index
        try:
            with open('data/output/document_index.json', 'w') as f:
                json.dump(document_index, f, indent=2)
            logger.info("Document index saved to data/output/document_index.json")
        except Exception as e:
            logger.warning(f"Could not save document index: {e}")
        
        # Step 2: Extract content fragments
        logger.info("Step 2: Extracting content fragments...")
        fragments_dict = self.indexer.extract_fragments(images, document_index)
        logger.info("Fragmentation complete")
        
        # Log statistics
        total_fragments = sum(len(frags) for frags in fragments_dict.values())
        logger.info(f"Extracted {total_fragments} total fragments across {len(fragments_dict)} topics")
        
        return fragments_dict
