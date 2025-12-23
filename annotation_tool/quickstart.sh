#!/bin/bash
# Quick start script for ASR Annotation Tool

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  ASR Error Annotation Tool - Quick Start                   ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"
echo ""

# Check if required packages are installed
echo "📦 Checking dependencies..."
python3 -c "import pandas" 2>/dev/null || { echo "❌ pandas not installed. Run: pip install pandas openpyxl"; exit 1; }
echo "   ✓ pandas"
python3 -c "import openpyxl" 2>/dev/null || { echo "❌ openpyxl not installed. Run: pip install openpyxl"; exit 1; }
echo "   ✓ openpyxl"
echo ""

# Get model choice
echo "🤖 Which ASR model would you like to prepare?"
echo "   1) Whisper (default)"
echo "   2) Phi-4"
echo "   3) Parakeet"
echo "   4) Granite"
echo "   5) Primock (doctor-patient conversations)"
echo ""
read -p "Enter choice (1-5) [1]: " model_choice
model_choice=${model_choice:-1}

case $model_choice in
    1)
        model="whisper"
        input_file="all_result_processed.xlsx"
        ;;
    2)
        model="phi4"
        input_file="all_result_processed.xlsx"
        ;;
    3)
        model="parakeet"
        input_file="all_result_processed.xlsx"
        ;;
    4)
        model="granite"
        input_file="all_result_processed.xlsx"
        ;;
    5)
        model="primock"
        input_file="primock_result_separate_sheets.xlsx"
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

# Check if input file exists
if [ ! -f "$input_file" ]; then
    echo "❌ Input file not found: $input_file"
    echo "   Please ensure you're in the directory with your results files."
    exit 1
fi

echo ""
echo "📋 Preparing annotation data..."
if [ "$model" = "primock" ]; then
    python3 prepare_annotations.py --primock "$input_file"
else
    python3 prepare_annotations.py --input "$input_file" --model "$model"
fi

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  Next Steps:                                               ║"
echo "║  1. Open annotation_interface.html in your web browser     ║"
echo "║  2. Click '📁 Load JSON File'                             ║"
echo "║  3. Select the generated JSON file                         ║"
echo "║  4. Start annotating errors!                              ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "💾 Don't forget to click 'Export Annotations' when done!"
