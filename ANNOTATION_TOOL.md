# ASR Error Annotation Tool - Quick Navigation

## 📍 Location
All annotation tool files have been organized in the **`annotation_tool/`** directory.

## 🚀 Quick Start

### Step 1: Navigate to the annotation tool
```bash
cd annotation_tool
```

### Step 2: Prepare your data
```bash
python prepare_annotations.py --input ../all_result_processed.xlsx --model whisper
```

### Step 3: Open the annotation interface
Open `annotation_interface.html` in your web browser

### Step 4: Process results
```bash
python process_annotations.py --annotations asr_annotations_*.json --original ../all_result_processed.xlsx
```

## 📂 Directory Structure
```
bio_ramp_asr/
├── annotation_tool/                    ← ALL ANNOTATION TOOLS HERE
│   ├── annotation_interface.html        (Web interface)
│   ├── prepare_annotations.py           (Excel → JSON)
│   ├── process_annotations.py           (Annotations → Excel)
│   ├── example_annotation_analysis.py   (Analysis examples)
│   ├── quickstart.sh                    (Auto setup)
│   ├── START_HERE.txt                   (Read this first!)
│   ├── QUICK_REFERENCE.txt              (Visual guide)
│   ├── SETUP_GUIDE.md                   (Workflow guide)
│   ├── ANNOTATION_TOOL_README.md        (Full manual)
│   ├── INDEX.md                         (File inventory)
│   └── FILES_CREATED.md                 (Detailed descriptions)
│
├── all_result_processed.xlsx            (Your original results)
├── all_result_separate_sheets.xlsx
├── primock_result_separate_sheets.xlsx
├── result_process.ipynb                 (Your notebook)
└── ... (other files)
```

## 📖 Documentation

Start with one of these guides:

1. **START_HERE.txt** - Visual quick-start
2. **QUICK_REFERENCE.txt** - ASCII art workflow and examples
3. **SETUP_GUIDE.md** - Complete workflow explanation
4. **ANNOTATION_TOOL_README.md** - Full user manual
5. **INDEX.md** - File inventory

## ⚡ Quick Commands

```bash
# From bio_ramp_asr/ directory:

# Prepare Whisper data
cd annotation_tool && python prepare_annotations.py --input ../all_result_processed.xlsx --model whisper

# Prepare other models
cd annotation_tool && python prepare_annotations.py --input ../all_result_processed.xlsx --model phi4

# Process results (after annotation)
cd annotation_tool && python process_annotations.py --annotations asr_annotations_*.json --original ../all_result_processed.xlsx --report

# Run analysis script
cd annotation_tool && python example_annotation_analysis.py
```

## 💾 Input/Output Files

### Input (stays in bio_ramp_asr/):
- `all_result_processed.xlsx` - Your original processed results

### Output (created in annotation_tool/):
- `{model}_annotation_data.json` - Prepared data for annotation
- `asr_annotations_TIMESTAMP.json` - Your annotations (export from web interface)
- `results_with_annotations.xlsx` - Final results with annotations
- `annotation_report.csv` - Optional detailed report

## 🎯 3-Step Workflow

```
1. PREPARE                 2. ANNOTATE              3. PROCESS
┌──────────────────┐      ┌──────────────────┐    ┌──────────────────┐
│ Excel → JSON     │ ──→  │ Web Interface    │ ──→│ JSON → Excel     │
│ 1 minute        │      │ Annotate errors  │    │ 1 minute        │
│ prepare_*.py    │      │ HTML interface   │    │ process_*.py    │
└──────────────────┘      └──────────────────┘    └──────────────────┘
```

## ✨ Everything You Need

✅ Professional web interface (no installation)
✅ Python utilities for data prep/processing
✅ Comprehensive documentation (8000+ lines)
✅ Example analysis code
✅ Quick-start guides and references

## 🎉 Ready to Use!

```bash
cd annotation_tool
python prepare_annotations.py --input ../all_result_processed.xlsx --model whisper
# Then open annotation_interface.html in your browser
```

For detailed help, see the documentation files in `annotation_tool/`
