#!/bin/bash
# Quick start script for the OCR extraction pipeline

echo "=========================================="
echo "OCR Extraction Pipeline - Quick Start"
echo "=========================================="
echo ""

# Set CUDA devices (using only GPUs 0 and 1 to avoid GPU 3 hardware issue)
export CUDA_VISIBLE_DEVICES=0,1

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

# Check if PDF exists
PDF_PATH="data/input_pdfs/paper1.pdf"
if [ ! -f "$PDF_PATH" ]; then
    echo "⚠️  Warning: Input PDF not found at $PDF_PATH"
    echo "Please place your PDF file in data/input_pdfs/"
    echo ""
    read -p "Press Enter to continue anyway or Ctrl+C to exit..."
fi

# Check CUDA availability
echo "Checking CUDA availability..."
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}'); print(f'Number of GPUs: {torch.cuda.device_count()}')"
echo ""

# Run the pipeline
echo "Starting extraction pipeline..."
echo "This may take 10-30 minutes depending on PDF length"
echo ""
python main.py

echo ""
echo "=========================================="
echo "Pipeline complete!"
echo "Check outputs in data/output/"
echo "=========================================="
