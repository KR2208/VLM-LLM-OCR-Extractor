# VLM-LLM OCR Extraction Pipeline Architecture

## Overview
Two-stage pipeline for extracting structured data from scientific PDFs using Vision-Language Models (VLM) and Large Language Models (LLM).

---

## Pipeline Flow

```
PDF (Images) 
    ↓
[STAGE 1: VLM - Qwen3-VL-8B-Instruct on GPU 0]
    ├─ Step 1: Index pages → Identify tables, figures, text sections
    └─ Step 2: Extract content → Read and transcribe everything to text
    ↓
Text Fragments (JSON)
    ↓
[STAGE 2: LLM - Qwen2.5-7B-Instruct on GPU 1]
    ├─ Parse text descriptions of tables
    ├─ Extract data from figure descriptions
    ├─ Cross-reference information across pages
    └─ Structure into database schema
    ↓
Structured Experiments (CSV)
```

---

## Stage 1: VLM Analysis (Vision → Text)

### Purpose
Extract ALL visual content from PDF pages as structured text

### Model
- **Qwen3-VL-8B-Instruct** (8B parameters)
- Multimodal: Processes images + text
- GPU: cuda:0

### Two-Step Process

#### Step 1: Document Indexing
- **Input**: PDF page images
- **Process**: Identify and classify page elements
  - Tables (with structure hints)
  - Figures/Diagrams (with captions)
  - Text sections (methods, results, etc.)
- **Output**: `document_index.json`
  ```json
  [
    {
      "page_number": 2,
      "element_type": "table",
      "description": "Test conditions table",
      "topics": ["test_conditions", "sample_info"]
    }
  ]
  ```

#### Step 2: Content Extraction
- **Input**: Page images + Document index
- **Process**: For each indexed element:
  - Tables → Extract full table as text (rows, columns, values)
  - Figures → Describe plots + extract data points
  - Text → Read paragraphs completely
- **Output**: `intermediate_fragments.json`
  ```json
  {
    "test_conditions": [
      "[Page 2] Table 1: Sample AGA1: Temp=296K, Thickness=2.0mm, Velocity=125m/s",
      "[Page 2] Table 1: Sample AGA2: Temp=573K, Thickness=2.0mm, Velocity=127m/s"
    ],
    "spall_results": [
      "[Page 5] Figure 3 caption: Spall strength of 0.57 ± 0.04 GPa at 296K"
    ]
  }
  ```

---

## Stage 2: LLM Extraction (Text → Structured Data)

### Purpose
Parse text fragments and extract structured experiment records

### Model
- **Qwen2.5-7B-Instruct** (7B parameters)
- Text-only model (no vision)
- GPU: cuda:1

### Process
1. **Read all fragments** (no images, just text descriptions)
2. **Identify experiments** (often one per table row)
3. **Cross-reference data** across topics and pages
4. **Extract fields** matching database schema
5. **Provide evidence** for every extracted value

### Key Features
- **Batching**: Splits large inputs to avoid OOM
- **JSON parsing**: Robust handling of model output
- **Validation**: Pydantic schema enforcement
- **Deduplication**: Removes duplicate experiments

### Output
`extracted_database.csv` with columns:
- Sample, Sample_evidence
- Initial sample temperature (K), evidence
- Sample thickness (mm), evidence
- Impact velocity (m/s), evidence
- Peak Stress (GPa), evidence
- Spall (GPa), evidence
- ... (all fields + evidence)

---

## File Structure

```
OCR/
├── main.py                          # Full pipeline orchestrator
├── run_vlm_stage.py                 # Run VLM only
├── run_llm_stage.py                 # Run LLM only
├── download_models.py               # Model downloader
├── requirements.txt                 # Dependencies
├── README.md                        # User guide
├── ARCHITECTURE.md                  # This file
│
├── src/
│   ├── vlm_processor.py            # VLM orchestrator
│   ├── vlm_indexer.py              # VLM indexing & extraction logic
│   ├── llm_extractor.py            # LLM extraction logic
│   ├── model_loader.py             # Model loading utilities
│   ├── schema.py                   # Pydantic data schema
│   └── logger_config.py            # Logging configuration
│
├── data/
│   ├── input_pdfs/
│   │   └── paper1.pdf              # Input PDF
│   └── output/
│       ├── document_index.json      # VLM Step 1 output
│       ├── intermediate_fragments.json  # VLM Step 2 output
│       └── extracted_database.csv   # LLM output (final)
│
└── models/
    ├── Qwen3-VL-8B-Instruct/       # VLM model files (~18GB)
    └── Qwen2.5-7B-Instruct/        # LLM model files (~15GB)
```

---

## Running the Pipeline

### Full Pipeline (VLM + LLM)
```bash
CUDA_VISIBLE_DEVICES=0,1 python main.py
```

### Stage 1 Only (VLM)
```bash
CUDA_VISIBLE_DEVICES=0 python run_vlm_stage.py
```

### Stage 2 Only (LLM)
```bash
CUDA_VISIBLE_DEVICES=1 python run_llm_stage.py
```

---

## GPU Memory Management

### Why Separate Stages?
- **VLM (8B)**: ~18GB VRAM + KV cache
- **LLM (7B)**: ~15GB VRAM + activation memory
- **Together**: Can exceed 24GB VRAM on single GPU
- **Solution**: Use 2 GPUs OR run stages separately

### Current Setup
- GPU 0: VLM only
- GPU 1: LLM only
- GPU 3: Disabled (hardware issue)

### If OOM Occurs
1. Run stages separately (clears GPU between stages)
2. Reduce batch sizes in code
3. Use fewer GPUs with `CUDA_VISIBLE_DEVICES=0`

---

## Key Improvements vs Old Approach

### Old Approach (Problematic)
❌ VLM tried to output structured JSON directly  
❌ Models couldn't handle full document at once  
❌ Both models loaded simultaneously → OOM  
❌ No batching for large inputs  

### New Approach (Working)
✅ VLM outputs unstructured text (what it's good at)  
✅ LLM structures the text (what it's good at)  
✅ Two-step indexing → Better context awareness  
✅ Batching support for large documents  
✅ Separate GPU assignments → No OOM  
✅ Evidence tracking for every field  

---

## Instructor Library

**Q: Would instructor help?**  
**A: Yes, but requires Python 3.10+**

Current system (Python 3.9):
- Manual JSON parsing with fallbacks
- Regex-based salvaging of partial outputs
- Pydantic validation post-parse

With instructor (Python 3.10+):
- Automatic retry on invalid JSON
- Guided generation with schema
- Better error messages
- Type-safe outputs

**Recommendation**: Upgrade to Python 3.10+ if instructor features are needed.

---

## Common Issues & Solutions

### VLM outputs non-JSON
- Improved prompts force JSON output
- Code strips markdown code blocks
- Regex fallback extracts JSON arrays
- Creates fallback entries if parse fails

### LLM OOM during generation
- Input chunked by topic
- GPU cache cleared between batches
- Max 15,000 chars per batch
- Experiments deduplicated after

### Missing data in output
- Check `*_evidence` fields to see what was found
- VLM may need better prompts for specific elements
- LLM may need examples in system prompt

---

## Future Enhancements

1. **Python 3.10+ Migration** → Use instructor for structured extraction
2. **Parallel Processing** → Process pages in parallel with multiple VLM instances
3. **Fine-tuning** → Train models on scientific paper format
4. **RAG Integration** → Add vector DB for better cross-referencing
5. **Active Learning** → User feedback loop for improving extraction

---

## GitHub Repository
https://github.com/KR2208/VLM-LLM-OCR-Extractor
