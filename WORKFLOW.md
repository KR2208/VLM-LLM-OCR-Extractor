# Running the NEW VLM-LLM Pipeline (Per-Page Structured Extraction)

## Current Status
✅ Repository cleaned (removed old files & pycache)  
✅ **VLM indexer refactored to per-page structured extraction**  
✅ **New schema: Tables → Experiments → CSV**  
� **Ready to run!**

---

## New Architecture: Per-Page Structured JSON

### What Changed?
**OLD (Topic-Based):**
```json
{
  "strain_rate": ["[Page 5] text...", "[Page 6] text..."],
  "temperature": ["[Page 1] text...", "[Page 5] text..."]
}
```
❌ Mixed pages, hard to link table rows, lost context

**NEW (Per-Page Structured):**
```json
{
  "pages": [
    {
      "page_number": 2,
      "tables": [
        {
          "headers": ["Sample", "Temperature_K", "Velocity_ms"],
          "rows": [
            {"Sample": "Ag", "Temperature_K": 296, "Velocity_ms": 137}
          ]
        }
      ],
      "figures": [...],
      "text_sections": [...]
    }
  ]
}
```
✅ Preserves table structure, maintains context, enables row-by-row extraction

---

## Stage 1: VLM Analysis (Per-Page)

**For EACH page, the VLM:**

1. **Identifies elements:**
   - data_table, figure, diagram, text_paragraph, equation, caption

2. **Extracts tables as structured JSON:**
   ```json
   {
     "description": "Experimental conditions",
     "headers": ["Sample", "Thickness_mm", "Temperature_K", "Velocity_ms"],
     "rows": [
       {"Sample": "Ag", "Thickness_mm": 1.994, "Temperature_K": 296, "Velocity_ms": 137}
     ]
   }
   ```

3. **Extracts figures with data:**
   ```json
   {
     "caption": "Fig. 6. Plastic strain rate vs shear stress",
     "x_axis": {"label": "Shear stress τ", "unit": "GPa"},
     "y_axis": {"label": "Plastic strain rate", "unit": "s⁻¹"},
     "data_series": [{"name": "973K", "data_points": [[0.1, 1e4], [0.2, 1e5]]}]
   }
   ```

4. **Extracts text for context:**
   ```json
   {
     "description": "Material synthesis",
     "content": "Silver samples obtained from Alfa Aesar Company..."
   }
   ```

**Output:** `intermediate_fragments.json` with per-page structured data

---

## Stage 2: LLM Processing (Merge & Export)

**The LLM will:**

1. **Parse per-page data:**
   - Iterate through all pages
   - Collect all table rows (experiments)
   - Collect figure data points
   - Collect text context

2. **Merge experiments:**
   - Combine rows from multiple tables
   - Group by sample/material
   - Remove duplicates

3. **Enrich with context:**
   - Fill missing "Synthesis" from text sections
   - Fill missing "Treatment" from text
   - Add strain rate from figures if missing
   - Cross-reference page to page

4. **Validate & export:**
   - Check required fields
   - Flag anomalies
   - Export to CSV (like your example!)

**Output:** `extracted_database.csv`

```csv
Sample,Synthesis,Treatment,Initial_Temperature_K,Yield_Stress_MPa,...
Ag,obtained from Alfa Aesar Company...,null,296,25,...
Ag,obtained from Alfa Aesar Company...,null,773,42,...
```

---

## Commands

### Run Stage 1 (VLM - Per-Page Extraction):
```bash
CUDA_VISIBLE_DEVICES=0 python run_vlm_stage.py
```

### Run Stage 2 (LLM - Merge & Export):
```bash
CUDA_VISIBLE_DEVICES=1 python run_llm_stage.py
```

### Run Full Pipeline (if enough memory):
```bash
CUDA_VISIBLE_DEVICES=0,1 python main.py
```

---

## Expected Output Files

After VLM:
- ✅ `data/output/intermediate_fragments.json` - Per-page structured data

After LLM:
- ✅ `data/output/extracted_database.csv` - Experiment records (CSV)

---

## New Pipeline Architecture

```
PDF Pages
    ↓
[VLM Stage] Per-Page Extraction
    ├─ For each page:
    │   ├─ Identify elements (table/figure/text)
    │   ├─ Extract table → structured JSON (row-by-row)
    │   ├─ Extract figure → axis/data/caption
    │   └─ Extract text → full content
    ↓
intermediate_fragments.json
{
  "pages": [
    {
      "page_number": 2,
      "tables": [{headers: [...], rows: [...]}],
      "figures": [...],
      "text_sections": [...]
    }
  ]
}
    ↓
[LLM Stage] Merge & Export
    ├─ Collect all table rows (experiments)
    ├─ Merge related experiments
    ├─ Fill missing fields from text/figures
    ├─ Validate consistency
    └─ Export CSV
    ↓
extracted_database.csv
```

---

## Why This Approach Works

✅ **Preserves table structure:** VLM sees the table, extracts row-by-row  
✅ **Maintains relationships:** Sample ↔ Temperature ↔ Velocity stay linked  
✅ **Per-page context:** Text on same page helps interpret table values  
✅ **LLM just enriches:** Fills gaps, merges, validates (not parsing)  
✅ **Direct to CSV:** No complex text-to-table conversion needed

---

## Next: Update LLM Stage

The LLM extractor needs to be updated to:
1. Read the new per-page JSON format
2. Collect all table rows from all pages
3. Merge and enrich experiments
4. Export to CSV

See `EXTRACTION_SCHEMA.md` for the complete data schema.

---

## Troubleshooting

**If VLM extraction fails:**
- Check GPU memory: `nvidia-smi`
- Check logs for JSON parse errors
- Reduce batch size in vlm_indexer.py if needed

**If table extraction is incomplete:**
- VLM may miss multi-page tables
- LLM stage should handle merging across pages

**If CSV is missing fields:**
- Check text_sections for context
- LLM should fill from text when table cells are empty

---

## Monitoring Progress

```bash
# Watch VLM stage logs
tail -f src/logs/extraction.log

# Check output files
ls -lh data/output/

# Inspect per-page structure (after VLM completes)
cat data/output/intermediate_fragments.json | jq '.pages[0]'
```
