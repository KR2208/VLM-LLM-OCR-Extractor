"""LLM-based data extractor with structured JSON output - handles tables, diagrams, and text."""

import json
import torch
from typing import List, Dict, Any
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
    
    def _estimate_token_count(self, text: str) -> int:
        """Rough estimate of token count (1 token ≈ 4 chars)."""
        return len(text) // 4
    
    def _chunk_fragments(self, fragments_dict: Dict[str, List[str]], max_tokens: int = 24000) -> List[Dict[str, List[str]]]:
        """Split fragments into smaller chunks to avoid OOM.
        
        Args:
            fragments_dict: Full fragments dictionary
            max_tokens: Maximum tokens per chunk (leave room for system prompt and output)
            
        Returns:
            List of fragment dictionaries (chunks)
        """
        # Estimate total size
        total_text = json.dumps(fragments_dict)
        total_tokens = self._estimate_token_count(total_text)
        
        logger.info(f"Total fragments size: ~{total_tokens} tokens")
        
        if total_tokens < max_tokens:
            logger.info("Fragments fit in single batch")
            return [fragments_dict]
        
        # Need to split - divide by topics
        chunks = []
        current_chunk = {}
        current_size = 0
        
        for topic, fragments in fragments_dict.items():
            topic_text = json.dumps({topic: fragments})
            topic_size = self._estimate_token_count(topic_text)
            
            if current_size + topic_size > max_tokens and current_chunk:
                # Start new chunk
                chunks.append(current_chunk)
                current_chunk = {}
                current_size = 0
            
            current_chunk[topic] = fragments
            current_size += topic_size
        
        if current_chunk:
            chunks.append(current_chunk)
        
        logger.info(f"Split fragments into {len(chunks)} chunks")
        return chunks
    
    def extract_data(self, fragments_dict: Dict[str, List[str]]) -> List[SpallExperiment]:
        """Extract structured experiment data from fragments.
        
        Args:
            fragments_dict: Dictionary mapping topics to text fragments
            
        Returns:
            List of SpallExperiment objects
        """
        logger.info("Starting LLM-based data extraction...")
        
        # Get the JSON schema from the Pydantic model
        schema = SpallExperiment.model_json_schema()
        
        # Create enhanced system prompt that understands different element types
        system_prompt = f"""You are a JSON-only API for extracting spall experiment data from scientific papers.

**Input Types You'll Receive:**
1. **Text sections**: Paragraphs describing methods, results, discussions
2. **Tables**: Structured data with test conditions, measurements, sample properties
3. **Figures/Diagrams**: Descriptions of plots, graphs, and experimental setups
4. **Raw text**: OCR-extracted content from pages

**Schema (each experiment must match):**
{json.dumps(schema, indent=2)}

**Extraction Strategy:**
1. **From Tables**: Extract numerical data (velocities, stresses, temperatures, dimensions)
2. **From Text**: Extract material names, methods, treatments, interpretations
3. **From Figures**: Extract trends, comparisons, visual data descriptions
4. **Cross-reference**: Correlate data across different element types and pages
   - Example: Table on Page 2 gives sample thickness → Text on Page 4 describes spall results for that sample → Combine into one experiment

**Critical Rules:**
1. For EVERY field, fill its '_evidence' field with:
   - "Page X, Table Y: [exact quote or data]"
   - "Page X, Figure Y: [description]"
   - "Page X, text section: [quote]"
   - "Calculated from [source]"
   - "Not found in paper"
2. Use null for missing data values (not "N/A" or empty strings)
3. Find ALL distinct experiments (multiple rows in tables = multiple experiments)
4. Be precise with units (convert if needed: GPa, MPa, mm, μm, m/s, K)
5. Correlate information across pages and element types

**Output Format:**
- Start with [ and end with ]
- NO markdown, NO explanations, NO code blocks
- ONLY valid JSON array

**Example (abbreviated):**
[
  {{
    "Sample": "Silver",
    "Sample_evidence": "Page 2, Table 1, column 'Material': Silver (Ag)",
    "Initial sample temperature (K)": 296,
    "Initial sample temperature (K)_evidence": "Page 2, Table 1, row 'AGA1', column 'Temp (K)': 296",
    "Sample thickness (mm)": 2.0,
    "Sample thickness (mm)_evidence": "Page 3, Table 2: 'Sample thickness: 2.0 mm'",
    "Flyer": "Copper",
    "Flyer_evidence": "Page 3, text section: 'Copper flyer plates were used in all experiments'",
    "impact velocity (m/s)": 125,
    "impact velocity (m/s)_evidence": "Page 2, Table 1, row 'AGA1': 125 m/s",
    "Peak Stress (GPa)": 3.7,
    "Peak Stress (GPa)_evidence": "Calculated from Hugoniot: ρ₀ × C₀ × u_p = 3.7 GPa",
    "Spall (GPa)": 0.57,
    "Spall (GPa)_evidence": "Page 5, Figure 3 caption: 'Spall strength 0.57 ± 0.04 GPa at 296 K'",
    "Type of experiment": "Plate impact",
    "Type of experiment_evidence": "Page 1: 'Planar plate impact experiments'"
  }}
]

BEGIN JSON ARRAY:"""
        
        # Prepare user message with fragments
        def create_user_message(fragments_chunk: Dict[str, List[str]]) -> str:
            return f"""Here are the extracted fragments from the scientific paper. Each fragment is labeled with its page number and may come from tables, figures, or text sections:

{json.dumps(fragments_chunk, indent=2)}

**Instructions:**
1. Identify all distinct experiments (look for multiple test conditions, samples, or measurements)
2. For tables: each row often represents a separate experiment
3. Cross-reference data across different topics and pages
4. Extract ALL experiments as a JSON array

Output the JSON array now:"""
        
        # Split fragments into chunks if needed
        chunks = self._chunk_fragments(fragments_dict, max_tokens=24000)
        
        all_experiments = []
        
        for chunk_idx, fragments_chunk in enumerate(chunks):
            logger.info(f"Processing chunk {chunk_idx + 1}/{len(chunks)}...")
            user_message = create_user_message(fragments_chunk)
            
            try:
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
                
                input_tokens = inputs.input_ids.shape[1]
                logger.info(f"Input tokens: {input_tokens}")
                
                # Generate with memory-efficient settings
                with torch.no_grad():
                    output_ids = self.model.generate(
                        **inputs,
                        max_new_tokens=6144,  # Reduced to save memory
                        temperature=0.1,
                        do_sample=False,
                        pad_token_id=self.tokenizer.eos_token_id
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
                
                # Parse JSON response with robust cleaning
                response_clean = response.strip()
                
                # Remove markdown code blocks
                if response_clean.startswith("```"):
                    lines = response_clean.split("\n")
                    response_clean = "\n".join(lines[1:-1]) if len(lines) > 2 else response_clean
                    response_clean = response_clean.replace("```json", "").replace("```", "").strip()
                
                # Find JSON array bounds
                start_idx = response_clean.find('[')
                end_idx = response_clean.rfind(']')
                
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    response_clean = response_clean[start_idx:end_idx+1]
                    logger.info(f"Extracted JSON array from response (chars {start_idx} to {end_idx})")
                else:
                    logger.warning("Could not find JSON array bounds in response")
                    logger.warning(f"Response preview: {response_clean[:500]}...")
                
                # Parse JSON
                try:
                    experiments_data = json.loads(response_clean)
                    
                    if not isinstance(experiments_data, list):
                        logger.warning("Parsed JSON is not a list, wrapping in array")
                        experiments_data = [experiments_data]
                    
                    # Convert to Pydantic objects
                    for idx, exp_data in enumerate(experiments_data):
                        try:
                            all_experiments.append(SpallExperiment(**exp_data))
                            logger.info(f"Validated experiment {len(all_experiments)}")
                        except Exception as e:
                            logger.warning(f"Failed to validate experiment {idx} in chunk {chunk_idx + 1}: {e}")
                            logger.warning(f"Data: {json.dumps(exp_data, indent=2)[:200]}...")
                            continue
                    
                except json.JSONDecodeError as e:
                    logger.error(f"JSON parse failed at position {e.pos}: {e.msg}")
                    logger.error(f"Problematic section: ...{response_clean[max(0, e.pos-100):e.pos+100]}...")
                    
                    # Try to salvage partial data
                    logger.info("Attempting to extract partial JSON objects...")
                    
                    # Try to find individual JSON objects
                    import re
                    json_objects = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_clean)
                    logger.info(f"Found {len(json_objects)} potential JSON objects via regex")
                    
                    for obj_str in json_objects:
                        try:
                            obj = json.loads(obj_str)
                            all_experiments.append(SpallExperiment(**obj))
                            logger.info("Successfully salvaged one experiment")
                        except:
                            continue
                
                # Free memory after each chunk
                del inputs, output_ids, generated_ids
                torch.cuda.empty_cache()
                
            except torch.cuda.OutOfMemoryError as e:
                logger.error(f"CUDA OOM on chunk {chunk_idx + 1}: {e}")
                logger.error("Try reducing max_tokens in _chunk_fragments or max_new_tokens in generate")
                # Free memory and continue with next chunk
                torch.cuda.empty_cache()
                continue
            except Exception as e:
                logger.error(f"Error during LLM extraction on chunk {chunk_idx + 1}: {e}")
                raise
        
        logger.info(f"Successfully extracted {len(all_experiments)} total experiments from all chunks")
        return all_experiments
