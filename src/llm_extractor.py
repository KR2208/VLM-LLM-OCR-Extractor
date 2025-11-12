"""LLM-based data extractor with structured JSON output."""

import json
import torch
from typing import List
from src.logger_config import logger
from src.model_loader import load_llm
from src.schema import SpallExperiment


class DataExtractor:
    """Extracts structured experiment data from text fragments using LLM."""
    
    def __init__(self, device: str = "cuda:1"):
        """Initialize the data extractor with LLM.
        
        Args:
            device: GPU device for LLM
        """
        logger.info(f"Initializing DataExtractor on {device}")
        self.device = device
        self.model, self.tokenizer = load_llm(device)
        
        logger.info("DataExtractor initialized successfully")
    
    def extract_data(self, fragments_dict: dict) -> List[SpallExperiment]:
        """Extract structured experiment data from fragments.
        
        Args:
            fragments_dict: Dictionary mapping topics to text fragments
            
        Returns:
            List of SpallExperiment objects
        """
        logger.info("Starting LLM-based data extraction...")
        
        # Get the JSON schema from the Pydantic model
        schema = SpallExperiment.model_json_schema()
        
        # Create system prompt
        system_prompt = f"""You are an expert materials scientist specializing in spall experiments and shock physics. You will extract structured data from text fragments.

**Your Task:**
1. Read ALL fragments carefully
2. CORRELATE information between topics (e.g., use 'sample_info' on Page 2 to fill in details for an experiment mentioned in 'spall_results' on Page 4)
3. Find ALL distinct experiments described in the paper
4. Return a JSON array of experiments matching this exact schema:

{json.dumps(schema, indent=2)}

**CRITICAL RULES:**
1. For EVERY single field, you MUST fill in the corresponding '_evidence' field with:
   - The exact quote from the fragments, OR
   - Your reasoning based on the data, OR
   - 'Not found in paper' if no information is available
2. If no information is found for a data field, set it to null
3. Be precise with units and numerical values
4. Cross-reference information across different topics to build complete experiment records
5. Return ONLY valid JSON - no markdown, no explanations, just the JSON array

**Example Output Format:**
[
  {{
    "Sample": "Silver (Ag)",
    "Sample_evidence": "Found in 'sample_info' on Page 2: 'All samples were made of 99.9% purity silver.'",
    "Synthesis": "Annealed foils",
    "Synthesis_evidence": "Found in 'sample_info' on Page 2: 'Annealed silver foils were used...'",
    "Treatment": "Preheated",
    "Treatment_evidence": "Found in 'test_conditions' on Page 3: 'Samples were preheated to various temperatures'",
    "Initial sample temperature (K)": 296,
    "Initial sample temperature (K)_evidence": "Found in 'test_conditions' table on Page 2, row 'AGA1'.",
    "Yield stress (Mpa)": null,
    "Yield stress (Mpa)_evidence": "Not found in paper",
    "G (Gpa)": 30.3,
    "G (Gpa)_evidence": "Found in 'mechanical_properties' on Page 2: 'Shear modulus G = 30.3 GPa'",
    "Melting point (K)": 1234,
    "Melting point (K)_evidence": "Found in 'sample_info' on Page 1: 'Silver melting point: 1234 K'",
    "Sample thickness (mm)": 2.0,
    "Sample thickness (mm)_evidence": "Found in 'test_conditions' table on Page 2",
    "Flyer": "Copper",
    "Flyer_evidence": "Found in 'flyer_info' on Page 3: 'Copper flyer plates'",
    "Flyer thickness (mm)": 3.0,
    "Flyer thickness (mm)_evidence": "Found in 'test_conditions' table on Page 2",
    "impact velocity (m/s)": 125,
    "impact velocity (m/s)_evidence": "Found in 'test_conditions' table on Page 2, row 'AGA1'",
    "Peak Stress (GPa)": 3.7,
    "Peak Stress (GPa)_evidence": "Found in 'results' on Page 4: 'Peak stress of 3.7 GPa'",
    "Type of experiment": "Plate impact",
    "Type of experiment_evidence": "Found in 'methods' on Page 1: 'Planar plate impact experiments'",
    "Spall (GPa)": 0.57,
    "Spall (GPa)_evidence": "Correlated from 'spall_results' Page 4: '0.57 ± 0.04 GPa at 296 K'",
    "Spall direction": "Longitudinal",
    "Spall direction_evidence": "Found in 'spall_results' on Page 4: 'Longitudinal spall strength'",
    "Refereces": "Smith et al. (2020)",
    "Refereces_evidence": "Found in references section"
  }}
]

**Output must start with `[` and end with `]`**"""
        
        # Prepare user message with fragments
        user_message = f"""Here are the extracted fragments from the scientific paper:

{json.dumps(fragments_dict, indent=2)}

Please analyze these fragments and extract all spall experiments as a JSON array."""
        
        try:
            logger.info("Sending fragments to LLM for structured extraction...")
            
            # Tokenize
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
            text = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
            inputs = self.tokenizer([text], return_tensors="pt").to(self.device)
            
            # Generate
            with torch.no_grad():
                output_ids = self.model.generate(
                    **inputs,
                    max_new_tokens=8192,
                    temperature=0.1,
                    do_sample=False
                )
            
            # Decode
            generated_ids = [
                output_ids[len(input_ids):]
                for input_ids, output_ids in zip(inputs.input_ids, output_ids)
            ]
            response = self.tokenizer.batch_decode(
                generated_ids,
                skip_special_tokens=True,
                clean_up_tokenization_spaces=False
            )[0]
            
            logger.info(f"LLM response length: {len(response)} characters")
            
            # Parse JSON response
            # Find JSON array in response (handle markdown code blocks)
            response = response.strip()
            if response.startswith("```"):
                # Remove markdown code block
                lines = response.split("\n")
                response = "\n".join(lines[1:-1]) if len(lines) > 2 else response
                response = response.replace("```json", "").replace("```", "").strip()
            
            # Parse JSON
            experiments_data = json.loads(response)
            
            # Convert to Pydantic objects
            experiments = [SpallExperiment(**exp) for exp in experiments_data]
            
            logger.info(f"Successfully extracted {len(experiments)} experiments")
            return experiments
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response was: {response[:500]}...")
            raise
        except Exception as e:
            logger.error(f"Error during LLM extraction: {e}")
            raise
