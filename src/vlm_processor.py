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
        """Run per-page structured extraction on a PDF.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary with per-page structured data
        """
        logger.info(f"Starting PDF analysis for: {pdf_path}")
        
        # Step 0: Convert PDF to images
        logger.info("Converting PDF to images...")
        images = convert_from_path(pdf_path)
        logger.info(f"PDF converted to {len(images)} pages")
        
        # Step 1: Extract structured data per page
        logger.info("Extracting structured data per page...")
        pages_data = self.indexer.extract_page_structure(images)
        logger.info(f"Extraction complete: {len(pages_data)} pages processed")
        
        # Create output structure
        output = {
            "document": {
                "total_pages": len(images),
                "extraction_date": self._get_timestamp()
            },
            "pages": pages_data
        }
        
        # Log statistics
        total_tables = sum(len(p.get("tables", [])) for p in pages_data)
        total_figures = sum(len(p.get("figures", [])) for p in pages_data)
        total_text = sum(len(p.get("text_sections", [])) for p in pages_data)
        
        logger.info(f"Extraction summary:")
        logger.info(f"  - Tables: {total_tables}")
        logger.info(f"  - Figures: {total_figures}")
        logger.info(f"  - Text sections: {total_text}")
        
        return output
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()
