"""VLM-based PDF indexer and fragment extractor (two-step process)."""

import json
from typing import List, Dict, Any
from PIL import Image
from tqdm import tqdm
from src.logger_config import logger
from src.model_loader import load_vlm
from qwen_vl_utils import process_vision_info


# Define extraction topics
EXTRACTION_TOPICS = [
    'mechanical_properties',
    'sample_info',
    'experimental_conditions',
    'spall_results',
    'test_conditions',
    'impactor_thickness',
    'sample_thickness',
    'grain_size',
    'initial_density',
    'sound_speeds',
    'flyer_information',
    'impact_velocity',
    'peak_stress',
    'strain_rate',
    'pulse_duration',
    'gas_gun_details',
    'temperature_conditions',
    'material_treatment',
    'synthesis_method',
    'references'
]


class PDFIndexer:
    """Handles two-step VLM processing: indexing and fragment extraction."""
    
    def __init__(self, device: str = "cuda:0"):
        """Initialize the indexer with VLM model.
        
        Args:
            device: GPU device for VLM
        """
        logger.info(f"Initializing PDFIndexer on {device}")
        self.device = device
        self.model, self.processor = load_vlm(device)
        logger.info("PDFIndexer initialized successfully")
    
    def create_index(self, images: List[Image.Image]) -> List[Dict[str, Any]]:
        """Step 1: Create a document index identifying what's on each page.
        
        Args:
            images: List of PIL Images (one per page)
            
        Returns:
            List of dictionaries describing document elements
        """
        logger.info(f"Creating document index for {len(images)} pages...")
        document_index = []
        
        # Process pages in batches
        batch_size = 4
        for batch_start in tqdm(range(0, len(images), batch_size), desc="Indexing pages"):
            batch_end = min(batch_start + batch_size, len(images))
            batch_images = images[batch_start:batch_end]
            
            # Create indexing prompt
            topics_str = ", ".join(EXTRACTION_TOPICS)
            prompt = f"""Analyze the layout of this document page. Identify all major elements (text sections, tables, figures, captions) and describe what topics they contain from this list: {topics_str}.

For each significant element, provide:
- page_number: The page number (1-indexed)
- element_type: 'table', 'figure', 'text_section', 'caption', etc.
- description: Brief description of the element
- topics: List of relevant topics from the provided list

Return a JSON array of objects. Example:
[{{"page_number": 1, "element_type": "table", "description": "Table of test conditions", "topics": ["test_conditions", "sample_thickness"]}}]"""
            
            # Process each page in the batch
            for idx, image in enumerate(batch_images):
                page_number = batch_start + idx + 1
                
                try:
                    # Prepare messages for Qwen2-VL
                    messages = [
                        {
                            "role": "user",
                            "content": [
                                {"type": "image", "image": image},
                                {"type": "text", "text": prompt}
                            ]
                        }
                    ]
                    
                    # Process inputs
                    text = self.processor.apply_chat_template(
                        messages, tokenize=False, add_generation_prompt=True
                    )
                    image_inputs, video_inputs = process_vision_info(messages)
                    inputs = self.processor(
                        text=[text],
                        images=image_inputs,
                        videos=video_inputs,
                        padding=True,
                        return_tensors="pt",
                    )
                    inputs = inputs.to(self.device)
                    
                    # Generate response
                    with torch.no_grad():
                        output_ids = self.model.generate(
                            **inputs,
                            max_new_tokens=512,
                            temperature=0.1
                        )
                    
                    # Decode response
                    generated_ids = [
                        output_ids[len(input_ids):]
                        for input_ids, output_ids in zip(inputs.input_ids, output_ids)
                    ]
                    response = self.processor.batch_decode(
                        generated_ids,
                        skip_special_tokens=True,
                        clean_up_tokenization_spaces=False
                    )[0]
                    
                    # Parse JSON response
                    try:
                        page_elements = json.loads(response)
                        if isinstance(page_elements, list):
                            document_index.extend(page_elements)
                        else:
                            document_index.append(page_elements)
                    except json.JSONDecodeError:
                        logger.warning(f"Could not parse JSON from page {page_number}, storing raw response")
                        document_index.append({
                            "page_number": page_number,
                            "element_type": "raw_text",
                            "description": "Full page analysis",
                            "topics": ["general"],
                            "raw_response": response
                        })
                    
                    logger.info(f"Indexed page {page_number}")
                    
                except Exception as e:
                    logger.error(f"Error indexing page {page_number}: {e}")
                    document_index.append({
                        "page_number": page_number,
                        "element_type": "error",
                        "description": f"Error during indexing: {str(e)}",
                        "topics": []
                    })
        
        logger.info(f"Document index created with {len(document_index)} elements")
        return document_index
    
    def extract_fragments(self, images: List[Image.Image], document_index: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Step 2: Extract content fragments based on the document index.
        
        Args:
            images: List of PIL Images (one per page)
            document_index: The index created by create_index()
            
        Returns:
            Dictionary mapping topics to lists of text fragments
        """
        logger.info("Extracting content fragments based on document index...")
        
        # Initialize fragments dictionary
        fragments_dict = {topic: [] for topic in EXTRACTION_TOPICS}
        
        # Process each indexed element
        for idx, element in enumerate(tqdm(document_index, desc="Extracting fragments")):
            page_number = element.get("page_number", 1)
            element_type = element.get("element_type", "unknown")
            description = element.get("description", "")
            topics = element.get("topics", [])
            
            # Skip error entries
            if element_type == "error":
                continue
            
            # Get the corresponding page image
            if page_number < 1 or page_number > len(images):
                logger.warning(f"Invalid page number {page_number} in index, skipping")
                continue
            
            image = images[page_number - 1]
            
            try:
                # Create extraction prompt
                prompt = f"""Extract the full text and data from this page element:
                
Element Type: {element_type}
Description: {description}

Provide the complete text content, including all data, numbers, and labels. If it's a table, extract it in a structured format. If it's a figure, describe it in detail."""
                
                # Prepare messages
                messages = [
                    {
                        "role": "user",
                        "content": [
                            {"type": "image", "image": image},
                            {"type": "text", "text": prompt}
                        ]
                    }
                ]
                
                # Process inputs
                text = self.processor.apply_chat_template(
                    messages, tokenize=False, add_generation_prompt=True
                )
                image_inputs, video_inputs = process_vision_info(messages)
                inputs = self.processor(
                    text=[text],
                    images=image_inputs,
                    videos=video_inputs,
                    padding=True,
                    return_tensors="pt",
                )
                inputs = inputs.to(self.device)
                
                # Generate response
                import torch
                with torch.no_grad():
                    output_ids = self.model.generate(
                        **inputs,
                        max_new_tokens=1024,
                        temperature=0.1
                    )
                
                # Decode response
                generated_ids = [
                    output_ids[len(input_ids):]
                    for input_ids, output_ids in zip(inputs.input_ids, output_ids)
                ]
                extracted_text = self.processor.batch_decode(
                    generated_ids,
                    skip_special_tokens=True,
                    clean_up_tokenization_spaces=False
                )[0]
                
                # Add page reference to extracted text
                fragment = f"[Page {page_number}] {extracted_text}"
                
                # Append to all relevant topics
                for topic in topics:
                    if topic in fragments_dict:
                        fragments_dict[topic].append(fragment)
                
                logger.info(f"Extracted fragment {idx+1}/{len(document_index)} from page {page_number}")
                
            except Exception as e:
                logger.error(f"Error extracting fragment from page {page_number}: {e}")
        
        logger.info("Fragment extraction complete")
        return fragments_dict
