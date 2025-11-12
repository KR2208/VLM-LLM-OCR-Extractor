"""VLM-based PDF indexer - Per-page structured extraction."""

import json
import torch
from typing import List, Dict, Any
from PIL import Image
from tqdm import tqdm
from src.logger_config import logger
from src.model_loader import load_vlm
from qwen_vl_utils import process_vision_info


class PDFIndexer:
    """Extracts structured data per page (tables, figures, text)."""
    
    def __init__(self, device: str = "cuda:0"):
        """Initialize the indexer with VLM model.
        
        Args:
            device: GPU device for VLM
        """
        logger.info(f"Initializing PDFIndexer on {device}")
        self.device = device
        self.model, self.processor = load_vlm(device)
        logger.info("PDFIndexer initialized successfully")
    
    def extract_page_structure(self, images: List[Image.Image]) -> List[Dict[str, Any]]:
        """Extract structured data from each page (tables, figures, text).
        
        Args:
            images: List of PIL Images (one per page)
            
        Returns:
            List of per-page structured data dictionaries
        """
        logger.info(f"Extracting structured data from {len(images)} pages...")
        pages_data = []
        
        # Process each page individually
        for page_idx in tqdm(range(len(images)), desc="Processing pages"):
            image = images[page_idx]
            page_number = page_idx + 1
            
            logger.info(f"Processing page {page_number}...")
            
            # Extract page structure
            page_data = self._extract_single_page(image, page_number)
            pages_data.append(page_data)
            
            logger.info(f"Page {page_number} complete: {page_data.get('element_count', 0)} elements extracted")
        
        logger.info(f"Extraction complete: {len(pages_data)} pages processed")
        return pages_data
    
    def _extract_single_page(self, image: Image.Image, page_number: int) -> Dict[str, Any]:
        """Extract all elements from a single page.
        
        Args:
            image: PIL Image of the page
            page_number: Page number
            
        Returns:
            Structured data for this page
        """
        page_data = {
            "page_number": page_number,
            "tables": [],
            "figures": [],
            "text_sections": [],
            "element_count": 0
        }
        
        # Step 1: Identify what's on the page
        identification_prompt = """Carefully scan this ENTIRE page and list EVERY element you see.

Look for:
- Data tables (with rows/columns of experimental values)
- Figures/graphs (with plots, axes, data curves)
- Text paragraphs (introduction, methods, results, discussion)
- Figure captions (labeled as "FIG. X" or "Figure X")
- Equations

For EACH element found, output:
{"type": "data_table/figure/text_paragraph/caption/equation", "description": "brief description", "contains_data": true/false}

IMPORTANT:
- List EVERY element, even if page seems simple
- Don't skip text sections or captions
- If page has title/abstract/introduction, mark as "text_paragraph"

Output as JSON array:
[{"type": "text_paragraph", "description": "Abstract and introduction", "contains_data": false}]

Output ONLY valid JSON array, no markdown:"""
        
        try:
            # Identify elements on the page
            elements = self._query_vlm(image, identification_prompt, max_tokens=512)
            
            # Parse element list
            element_list = self._parse_json_response(elements)
            if not isinstance(element_list, list):
                element_list = [element_list] if element_list else []
            
            page_data["element_count"] = len(element_list)
            
            # Step 2: Extract each element based on type
            for element in element_list:
                element_type = element.get("type", "").lower()
                description = element.get("description", "")
                contains_data = element.get("contains_data", False)
                
                if "table" in element_type and contains_data:
                    # Extract table data
                    table_data = self._extract_table(image, description)
                    if table_data:
                        page_data["tables"].append(table_data)
                
                elif "figure" in element_type or "diagram" in element_type:
                    # Extract figure data
                    figure_data = self._extract_figure(image, description)
                    if figure_data:
                        page_data["figures"].append(figure_data)
                
                elif "text" in element_type or "caption" in element_type:
                    # Extract text content
                    text_data = self._extract_text(image, description)
                    if text_data:
                        page_data["text_sections"].append(text_data)
        
        except Exception as e:
            logger.error(f"Error processing page {page_number}: {e}")
            page_data["error"] = str(e)
        
        return page_data
    
    def _extract_table(self, image: Image.Image, description: str) -> Dict[str, Any]:
        """Extract structured data from a table.
        
        Args:
            image: Page image
            description: Table description
            
        Returns:
            Dictionary with table data
        """
        prompt = f"""Extract the COMPLETE table as structured JSON.

Table: {description}

Output format:
{{
  "description": "Brief description",
  "headers": ["Column1", "Column2", ...],
  "rows": [
    {{"Column1": "value1", "Column2": "value2", "Column3": "value3", ...}},
    {{"Column1": "value1", "Column2": "value2", "Column3": "value3", ...}}
  ]
}}

CRITICAL RULES:
- Extract EVERY ROW completely (all columns for each row)
- If a cell is empty, use null - but include ALL column keys
- Read carefully - don't skip columns or merge cells
- Preserve units in headers (mm, m/s, K, GPa, etc.)
- Keep all numerical precision
- Count rows carefully and extract each one

Example of complete row:
{{"TEST": "AGA3a", "Impactor/thickness, mm": "Al, 1", "Sample thickness, mm": "1.986", "Impact velocity, m/s": "105", "Initial temperature K": "296"}}

Output ONLY valid JSON, no markdown, no explanations:"""
        
        try:
            response = self._query_vlm(image, prompt, max_tokens=2048)
            table_data = self._parse_json_response(response)
            
            if table_data and isinstance(table_data, dict):
                table_data["type"] = "data_table"
                return table_data
            
        except Exception as e:
            logger.warning(f"Table extraction failed: {e}")
        
        return None
    
    def _extract_figure(self, image: Image.Image, description: str) -> Dict[str, Any]:
        """Extract information from a figure/diagram.
        
        Args:
            image: Page image
            description: Figure description
            
        Returns:
            Dictionary with figure data
        """
        prompt = f"""Carefully analyze this figure/graph and extract data as JSON.

Figure: {description}

Output format:
{{
  "caption": "Full caption text from the figure",
  "type": "line_graph/bar_chart/scatter_plot/diagram",
  "x_axis": {{"label": "X axis label", "unit": "unit (e.g., mm, s, K)", "range": [min_value, max_value]}},
  "y_axis": {{"label": "Y axis label", "unit": "unit (e.g., MPa, m/s)", "range": [min_value, max_value]}},
  "data_series": [
    {{
      "name": "Series/curve name or temperature",
      "data_points": [[x1, y1], [x2, y2], [x3, y3], [x4, y4], [x5, y5]]
    }}
  ],
  "legend": ["legend item 1", "legend item 2"],
  "annotations": ["annotation text 1", "annotation text 2"]
}}

CRITICAL INSTRUCTIONS:
- Read the axis scales and units CAREFULLY
- Extract at least 5-10 data points per curve/series
- For each data_points array, provide actual [x, y] coordinate pairs
- If multiple curves, create separate entries in data_series
- Include ALL legend items
- Capture any text annotations on the plot

Example data_points (DO THIS):
"data_points": [[0, 0], [0.1, 50], [0.2, 100], [0.3, 150], [0.4, 200]]

NOT like this:
"data_points": [[0], [0], []]

Output ONLY valid JSON, no markdown:"""
        
        try:
            response = self._query_vlm(image, prompt, max_tokens=2048)
            figure_data = self._parse_json_response(response)
            
            if figure_data and isinstance(figure_data, dict):
                figure_data["type"] = "figure"
                return figure_data
            
        except Exception as e:
            logger.warning(f"Figure extraction failed: {e}")
        
        return None
    
    def _extract_text(self, image: Image.Image, description: str) -> Dict[str, Any]:
        """Extract text content from a section.
        
        Args:
            image: Page image
            description: Section description
            
        Returns:
            Dictionary with text data
        """
        prompt = f"""Extract ALL text from this section:

Section: {description}

Transcribe complete text including:
- All paragraphs
- Material descriptions
- Experimental details
- Numerical values and units
- Equations or formulas

Preserve structure and precision. Output the text directly:"""
        
        try:
            response = self._query_vlm(image, prompt, max_tokens=2048)
            
            if response and len(response.strip()) > 10:
                return {
                    "type": "text_section",
                    "description": description,
                    "content": response.strip()
                }
            
        except Exception as e:
            logger.warning(f"Text extraction failed: {e}")
        
        return None
    
    def _query_vlm(self, image: Image.Image, prompt: str, max_tokens: int = 1024) -> str:
        """Query the VLM with an image and prompt.
        
        Args:
            image: Input image
            prompt: Text prompt
            max_tokens: Maximum tokens to generate
            
        Returns:
            Model response text
        """
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
                max_new_tokens=max_tokens,
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
        
        return response.strip()
    
    def _parse_json_response(self, response: str) -> Any:
        """Parse JSON from VLM response with cleaning.
        
        Args:
            response: Raw VLM response
            
        Returns:
            Parsed JSON object or None
        """
        try:
            # Clean response - remove markdown code blocks
            response_clean = response.strip()
            
            if response_clean.startswith("```"):
                lines = response_clean.split("\n")
                response_clean = "\n".join(lines[1:-1]) if len(lines) > 2 else response_clean
                response_clean = response_clean.replace("```json", "").replace("```", "").strip()
            
            # Find JSON bounds
            if response_clean.startswith('['):
                start_idx = response_clean.find('[')
                end_idx = response_clean.rfind(']')
            elif response_clean.startswith('{'):
                start_idx = response_clean.find('{')
                end_idx = response_clean.rfind('}')
            else:
                # Try to find JSON anywhere in response
                start_idx = max(response_clean.find('['), response_clean.find('{'))
                if '[' in response_clean and '{' in response_clean:
                    start_idx = min(response_clean.find('['), response_clean.find('{'))
                end_idx = max(response_clean.rfind(']'), response_clean.rfind('}'))
            
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                response_clean = response_clean[start_idx:end_idx+1]
            
            return json.loads(response_clean)
            
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse error: {e}")
            logger.debug(f"Response: {response[:200]}...")
            return None
