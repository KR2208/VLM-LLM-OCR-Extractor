#!/bin/bash
# Check model download progress

echo "========================================"
echo "Model Download Progress"
echo "========================================"
echo ""

MODEL_DIR="/home/krameshbabu/Alloy/OCR/models"

if [ -d "$MODEL_DIR" ]; then
    echo "Cache directory: $MODEL_DIR"
    echo ""
    echo "Current size:"
    du -sh $MODEL_DIR
    echo ""
    echo "Files downloaded:"
    find $MODEL_DIR -type f | wc -l
    echo ""
    echo "Latest files:"
    find $MODEL_DIR -type f -printf '%T+ %p\n' | sort -r | head -10
else
    echo "Model directory does not exist yet."
fi

echo ""
echo "========================================"
echo "To see live download log, run:"
echo "  tail -f src/logs/extraction.log"
echo "========================================"
