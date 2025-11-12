"""Configuration file for the OCR extraction pipeline."""

from pathlib import Path

# Project root directory
PROJECT_ROOT = Path("/home/krameshbabu/Alloy/OCR")

# GPU assignments
VLM_DEVICE = "cuda:0"  # GPU for Vision-Language Model
LLM_DEVICE = "cuda:1"  # GPU for Language Model

# Model identifiers
VLM_MODEL_NAME = "Qwen/Qwen3-VL-8B-Instruct"
LLM_MODEL_NAME = "Qwen/Qwen2.5-7B-Instruct"

# Paths
MODEL_CACHE_DIR = PROJECT_ROOT / "models"
DATA_DIR = PROJECT_ROOT / "data"
INPUT_PDF_DIR = DATA_DIR / "input_pdfs"
OUTPUT_DIR = DATA_DIR / "output"
LOG_DIR = PROJECT_ROOT / "src" / "logs"

# Default file paths
DEFAULT_PDF = INPUT_PDF_DIR / "Plasticflowinshock-loadedsilver.pdf"
OUTPUT_CSV = OUTPUT_DIR / "extracted_database.csv"
OUTPUT_FRAGMENTS = OUTPUT_DIR / "intermediate_fragments.json"
OUTPUT_INDEX = OUTPUT_DIR / "document_index.json"
LOG_FILE = LOG_DIR / "extraction.log"

# Model parameters
VLM_BATCH_SIZE = 4  # Number of pages to process at once
VLM_MAX_TOKENS = 1024  # Max tokens for VLM generation
LLM_MAX_TOKENS = 8192  # Max tokens for LLM generation
GENERATION_TEMPERATURE = 0.1  # Lower = more deterministic

# Extraction topics
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
