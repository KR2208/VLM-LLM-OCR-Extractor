# Scientific Paper Data Extraction Pipeline

A complete Python application for extracting structured data from scientific papers using Vision-Language Models (VLM) and Large Language Models (LLM) with multi-GPU support.

## Architecture

This pipeline uses a three-stage approach:

1. **VLM Indexing (GPU 0)**: Scans all pages to create a document index identifying what content is on which page
2. **VLM Fragmentation (GPU 0)**: Intelligently re-visits relevant pages to extract raw text/table data for each topic
3. **LLM Extraction (GPU 1)**: Correlates information across all fragments to populate structured experiment data

## Models

- **VLM (Eyes)**: `Qwen/Qwen2-VL-7B-Instruct` on GPU 0 (cuda:0)
- **LLM (Brain)**: `Qwen/Qwen2.5-7B-Instruct` on GPU 1 (cuda:1)

Both models run in full precision (bfloat16) for optimal accuracy.

## Project Structure

```
/home/krameshbabu/Alloy/OCR/
├── main.py                      # Main pipeline orchestrator
├── test_vlm.py                  # VLM unit test script
├── src/
│   ├── __init__.py
│   ├── logger_config.py         # Logging configuration
│   ├── schema.py                # Pydantic schema (33 fields + evidence)
│   ├── model_loader.py          # Model loading with GPU assignment
│   ├── vlm_indexer.py           # Two-step VLM logic
│   ├── vlm_processor.py         # VLM orchestrator
│   ├── llm_extractor.py         # LLM-based extraction
│   └── logs/
│       └── extraction.log       # Log file
├── data/
│   ├── input_pdfs/              # Place your PDFs here
│   └── output/
│       ├── document_index.json  # Generated index
│       ├── extracted_fragments.json  # Intermediate fragments
│       └── extracted_database.csv    # Final output
└── models/                      # Model cache directory
```

## Installation

### Prerequisites

1. **Python 3.9+**
2. **CUDA-capable GPUs** (2 GPUs recommended)
3. **Poppler** (for pdf2image):
   ```bash
   # Ubuntu/Debian
   sudo apt-get install poppler-utils
   
   # macOS
   brew install poppler
   ```

### Setup

```bash
# Navigate to project directory
cd /home/krameshbabu/Alloy/OCR

# Create virtual environment with uv
uv venv

# Activate virtual environment
source .venv/bin/activate

# Install dependencies (already done)
uv pip install torch transformers accelerate pydantic instructor pandas pdf2image Pillow tqdm einops qwen-vl-utils
```

## Usage

### Running the Full Pipeline

1. Place your PDF in `data/input_pdfs/Plasticflowinshock-loadedsilver.pdf` (or update the path in `main.py`)

2. Run the pipeline:
   ```bash
   source .venv/bin/activate
   python main.py
   ```

3. Check outputs:
   - CSV: `data/output/extracted_database.csv`
   - Fragments: `data/output/intermediate_fragments.json`
   - Index: `data/output/document_index.json`
   - Logs: `src/logs/extraction.log`

### Testing VLM Only

To test the VLM on a single page:

1. Place a single-page PDF at `data/input_pdfs/sample_page.pdf`

2. Run the test:
   ```bash
   source .venv/bin/activate
   python test_vlm.py
   ```

## Output Schema

The pipeline extracts 33 fields per experiment:

- **Sample Information**: Sample, Synthesis, Treatment, Temperature
- **Mechanical Properties**: Yield stress, Ultimate stress, KIC, Hardness, B, G, E, Mu, Melting point
- **Sample Dimensions**: Thickness, Diameter, Grain size, Density
- **Sound Speeds**: Longitudinal, Shear, Bulk
- **Flyer Information**: Flyer material, Processing, Thickness, Diameter
- **Experimental Conditions**: Impact velocity, Peak stress, Strain rate, Pulse duration, Experiment type, Gas gun diameter
- **Spall Results**: Spall strength, Direction
- **References**

**Important**: Each field has a corresponding `_evidence` field containing:
- The exact quote from the paper, OR
- Reasoning based on the data, OR
- "Not found in paper" if unavailable

## GPU Memory Requirements

- **GPU 0 (VLM)**: ~16-20 GB VRAM
- **GPU 1 (LLM)**: ~14-16 GB VRAM

If you have limited VRAM, you may need to:
- Use smaller batch sizes in `vlm_indexer.py`
- Reduce `max_new_tokens` in generation calls
- Use `torch.float16` instead of `torch.bfloat16`

## Model Downloads

On first run, models will be automatically downloaded to the `models/` directory:
- VLM: ~16 GB
- LLM: ~14 GB

**Total disk space needed**: ~30 GB for models + workspace

## Troubleshooting

### Out of Memory Errors
- Reduce batch size in `vlm_indexer.py` (line 49)
- Reduce `max_new_tokens` in generation calls
- Clear CUDA cache: Add `torch.cuda.empty_cache()` between stages

### PDF Conversion Issues
- Ensure poppler is installed
- Check PDF is not corrupted
- Try converting PDF manually: `pdftoppm -png file.pdf output`

### Model Loading Issues
- Check internet connection (first download)
- Verify CUDA is available: `python -c "import torch; print(torch.cuda.is_available())"`
- Check GPU visibility: `nvidia-smi`

## Notes

- The pipeline uses **full precision** (bfloat16), not quantization, for maximum accuracy
- Processing time depends on PDF length (~1-2 min per page for VLM, ~2-3 min for LLM)
- First run will download models (~30 GB total)
- Check `src/logs/extraction.log` for detailed execution logs

## Dependencies

Key packages:
- `torch`: PyTorch for GPU acceleration
- `transformers`: Hugging Face model loading
- `qwen-vl-utils`: Utilities for Qwen-VL models
- `instructor`: Structured output from LLMs
- `pydantic`: Data validation
- `pdf2image`: PDF to image conversion
- `pandas`: CSV output generation

## Citation

If you use this pipeline, please cite the relevant model papers:
- Qwen2-VL: [Hugging Face](https://huggingface.co/Qwen/Qwen2-VL-7B-Instruct)
- Qwen2.5: [Hugging Face](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct)
