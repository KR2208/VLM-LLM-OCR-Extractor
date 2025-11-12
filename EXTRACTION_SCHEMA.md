# VLM-LLM Extraction Schema

This document defines the data schema for the two-stage extraction pipeline.

## Stage 1: VLM Output (Per-Page Structured JSON)

The VLM stage outputs a JSON file with the following structure:

```json
{
  "document": {
    "total_pages": 10,
    "extraction_date": "2025-11-12T10:30:00"
  },
  "pages": [
    {
      "page_number": 1,
      "element_count": 3,
      "tables": [
        {
          "type": "data_table",
          "description": "Experimental conditions",
          "headers": ["Sample", "Thickness (mm)", "Temperature (K)", "Velocity (m/s)"],
          "rows": [
            {
              "Sample": "Ag",
              "Thickness (mm)": 1.994,
              "Temperature (K)": 296,
              "Velocity (m/s)": 137
            }
          ]
        }
      ],
      "figures": [
        {
          "type": "figure",
          "caption": "Fig. 1. Velocity profiles...",
          "x_axis": {"label": "Time", "unit": "ns", "range": [0, 100]},
          "y_axis": {"label": "Velocity", "unit": "m/s", "range": [0, 500]},
          "data_series": [
            {"name": "Series 1", "data_points": [[0, 0], [10, 100]]}
          ],
          "legend": ["Sample 1", "Sample 2"],
          "annotations": ["Peak at t=50ns"]
        }
      ],
      "text_sections": [
        {
          "type": "text_section",
          "description": "Abstract",
          "content": "Full text content..."
        }
      ],
      "error": null
    }
  ]
}
```

### Key Features:
- **Per-page organization**: Each page is processed independently
- **Structured tables**: Row-by-row extraction preserves table relationships
- **Figure data**: Extracts axis labels, data points, legends, captions
- **Text context**: Captures paragraphs for filling missing fields

## Stage 2: LLM Output (Experiment Database)

The LLM stage processes the VLM output and produces:

### A. Intermediate: Merged Experiments JSON

```json
{
  "experiments": [
    {
      "experiment_id": "exp_001",
      "sample": "Ag",
      "synthesis": "obtained from Alfa Aesar Company. Square, 12 mm×12 mm...",
      "treatment": null,
      "initial_temperature_K": 296,
      "yield_stress_MPa": 25,
      "sample_thickness_mm": 1.994,
      "flyer_material": "Cu",
      "flyer_thickness_mm": 1.0,
      "impact_velocity_ms": 137,
      "strain_rate_s": 1e5,
      "evidence": {
        "sample": "page 1, Table I",
        "synthesis": "page 2, paragraph 3",
        "temperature": "page 1, Table I",
        "yield_stress": "page 1, Table I"
      }
    }
  ],
  "metadata": {
    "total_experiments": 15,
    "papers_processed": 1,
    "extraction_date": "2025-11-12T11:00:00"
  }
}
```

### B. Final: CSV Export

| Sample | Synthesis | Treatment | Initial_Temperature_K | Yield_Stress_MPa | Sample_Thickness_mm | Flyer | Flyer_Thickness_mm | Impact_Velocity_ms | Strain_Rate_s |
|--------|-----------|-----------|----------------------|------------------|---------------------|-------|-------------------|-------------------|---------------|
| Ag | obtained from Alfa Aesar... | null | 296 | 25 | 1.994 | Cu | 1.0 | 137 | 1e5 |
| Ag | obtained from Alfa Aesar... | null | 773 | 42 | 1.986 | Cu | 0.5 | 105 | 1e5 |

### Key Features:
- **Cross-page merging**: Combines data from multiple pages
- **Field enrichment**: Fills missing values using context from text sections
- **Evidence tracking**: Records source of each data point
- **Validation**: Checks consistency and flags anomalies

## Data Flow

```
PDF → VLM Stage → Per-Page JSON → LLM Stage → Experiments JSON → CSV
```

1. **VLM**: Extracts raw structured data per page (tables, figures, text)
2. **LLM**: Merges experiments, fills missing fields, validates, exports

## Field Definitions

### Experiment Fields

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| sample | string | Sample material (e.g., "Ag", "Cu") | Table/text |
| synthesis | string | Material synthesis method | Text section |
| treatment | string/null | Heat treatment or processing | Text section |
| initial_temperature_K | float | Initial sample temperature (K) | Table |
| yield_stress_MPa | float | Yield/flow stress (MPa) | Table |
| sample_thickness_mm | float | Sample thickness (mm) | Table |
| flyer_material | string | Impactor/flyer material | Table/text |
| flyer_thickness_mm | float | Flyer thickness (mm) | Table |
| impact_velocity_ms | float | Impact velocity (m/s) | Table |
| strain_rate_s | float | Strain rate (1/s) | Table/figure |
| peak_stress_GPa | float | Peak stress (GPa) | Table/figure |
| spall_strength_MPa | float | Spall strength (MPa) | Table/figure |

### Evidence Format

```json
{
  "field_name": "page X, element_type (description)"
}
```

Examples:
- `"page 1, Table I (Experimental conditions)"`
- `"page 2, paragraph 3 (Material synthesis)"`
- `"page 5, Figure 3 (Strain rate vs stress)"`
