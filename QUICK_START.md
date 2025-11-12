# Quick Start Guide - New Per-Page Extraction

## 🚀 Ready to Run!

The VLM indexer has been refactored for **per-page structured extraction**. This will give you clean table data like your example CSV!

---

## What Changed?

**Before:**
```json
{
  "test_conditions": ["[Page 1] text...", "[Page 2] text..."]
}
```

**Now:**
```json
{
  "pages": [
    {
      "page_number": 2,
      "tables": [{
        "headers": ["Sample", "Temperature_K", "Velocity_ms"],
        "rows": [
          {"Sample": "Ag", "Temperature_K": 296, "Velocity_ms": 137}
        ]
      }],
      "figures": [...],
      "text_sections": [...]
    }
  ]
}
```

---

## Run the Pipeline

### Step 1: VLM Stage (Extract Per-Page Data)
```bash
cd /home/krameshbabu/Alloy/OCR
CUDA_VISIBLE_DEVICES=0 python run_vlm_stage.py
```

**Wait ~10-15 minutes** for extraction to complete.

### Step 2: Check Output
```bash
# View per-page structure
cat data/output/intermediate_fragments.json | jq '.pages[0]'

# View first table
cat data/output/intermediate_fragments.json | jq '.pages[] | select(.tables | length > 0) | .tables[0]' | head -50

# Count elements
cat data/output/intermediate_fragments.json | jq '{
  total_pages: .document.total_pages,
  total_tables: [.pages[].tables[]] | length,
  total_figures: [.pages[].figures[]] | length,
  total_text_sections: [.pages[].text_sections[]] | length
}'
```

### Step 3: LLM Stage (TODO - Needs Update)
```bash
# After updating llm_extractor.py:
CUDA_VISIBLE_DEVICES=1 python run_llm_stage.py
```

---

## Expected Output

### VLM Stage Output: `intermediate_fragments.json`

```json
{
  "document": {
    "total_pages": 10,
    "extraction_date": "2025-11-12T..."
  },
  "pages": [
    {
      "page_number": 1,
      "element_count": 2,
      "tables": [],
      "figures": [],
      "text_sections": [
        {
          "type": "text_section",
          "description": "Abstract",
          "content": "The evolution of elastic-plastic shock waves..."
        }
      ]
    },
    {
      "page_number": 2,
      "element_count": 1,
      "tables": [
        {
          "type": "data_table",
          "description": "Experimental conditions",
          "headers": ["Sample", "Synthesis", "Initial_Temperature_K", "Yield_Stress_MPa"],
          "rows": [
            {
              "Sample": "Ag",
              "Synthesis": "obtained from Alfa Aesar Company...",
              "Initial_Temperature_K": 296,
              "Yield_Stress_MPa": 25
            },
            {
              "Sample": "Ag",
              "Synthesis": "obtained from Alfa Aesar Company...",
              "Initial_Temperature_K": 773,
              "Yield_Stress_MPa": 42
            }
          ]
        }
      ],
      "figures": [],
      "text_sections": []
    }
  ]
}
```

### LLM Stage Output: `extracted_database.csv` (Target)

| Sample | Synthesis | Treatment | Initial_Temperature_K | Yield_Stress_MPa | Sample_Thickness_mm | ... |
|--------|-----------|-----------|----------------------|------------------|---------------------|-----|
| Ag | obtained from Alfa Aesar Company... | null | 296 | 25 | 1.994 | ... |
| Ag | obtained from Alfa Aesar Company... | null | 773 | 42 | 1.986 | ... |

---

## Key Files

### Modified:
- ✅ `src/vlm_indexer.py` - Per-page extraction logic
- ✅ `src/vlm_processor.py` - Updated orchestrator
- ✅ `run_vlm_stage.py` - Updated logging

### Documentation:
- ✅ `EXTRACTION_SCHEMA.md` - Complete schema reference
- ✅ `WORKFLOW.md` - Detailed workflow guide
- ✅ `REFACTORING_SUMMARY.md` - What changed and why
- ✅ `QUICK_START.md` - This file!

### To Update (Next):
- ⏳ `src/llm_extractor.py` - Process new format, merge experiments, export CSV
- ⏳ `src/schema.py` - Define experiment model

---

## Advantages of New Approach

✅ **Preserves table structure** - Row-by-row extraction  
✅ **Maintains relationships** - Sample ↔ Temperature ↔ Velocity stay linked  
✅ **Per-page context** - Text on same page helps interpretation  
✅ **Clean data flow** - VLM extracts, LLM enriches, no parsing needed  
✅ **Direct to CSV** - One-to-one mapping from table rows to CSV rows  

---

## Troubleshooting

**VLM fails with JSON parse error:**
- The VLM output may not be valid JSON
- Check logs: `tail -f src/logs/extraction.log`
- Fallback handling is built-in (will create generic entries)

**Tables not detected:**
- VLM may not recognize complex table layouts
- Check page image quality
- Manually verify PDF page contains a table

**Missing data in tables:**
- VLM may miss columns or rows in complex tables
- LLM stage should fill from text_sections if available
- Review specific page: `cat data/output/intermediate_fragments.json | jq '.pages[N]'`

---

## Next: Update LLM Extractor

The LLM extractor needs to:

1. **Read new format:**
   ```python
   with open('data/output/intermediate_fragments.json') as f:
       data = json.load(f)
   
   # Collect all experiments
   experiments = []
   for page in data['pages']:
       for table in page.get('tables', []):
           for row in table.get('rows', []):
               experiments.append({
                   'page': page['page_number'],
                   'data': row
               })
   ```

2. **Merge experiments:**
   - Group by sample/material
   - Combine data from multiple pages

3. **Enrich from text:**
   - Fill missing "Synthesis" from text_sections
   - Fill missing "Treatment" from text_sections
   - Cross-reference page to page

4. **Export CSV:**
   ```python
   import pandas as pd
   df = pd.DataFrame(experiments)
   df.to_csv('data/output/extracted_database.csv', index=False)
   ```

---

## Ready? Let's Test!

```bash
# Run VLM stage
CUDA_VISIBLE_DEVICES=0 python run_vlm_stage.py

# Monitor progress
watch -n 5 'ls -lh data/output/ && echo "---" && tail -10 src/logs/extraction.log'
```

**Good luck! 🚀**
