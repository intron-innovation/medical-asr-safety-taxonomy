# 📍 ASR Error Annotation Tool - INDEX

## What Was Created For You

This directory now contains a **complete, production-ready annotation system** for analyzing ASR errors. Here's the complete inventory:

---

## 🎯 START HERE

**New to this tool?** Start with one of these:

1. **[QUICK_REFERENCE.txt](QUICK_REFERENCE.txt)** ⭐ **← START HERE**
   - Visual workflow diagram
   - ASCII art guides
   - 3-step quick start
   - Example annotations
   - Severity scale

2. **[SETUP_GUIDE.md](SETUP_GUIDE.md)** 
   - Component overview
   - Complete workflow explanation
   - File structure
   - Best practices

3. **[ANNOTATION_TOOL_README.md](ANNOTATION_TOOL_README.md)**
   - Comprehensive user guide
   - Feature explanations
   - Troubleshooting FAQ
   - Advanced usage

---

## 📦 CORE FILES

### Annotation Interface
- **`annotation_interface.html`** (7000+ lines)
  - The web-based annotation tool
  - Open in any modern web browser
  - No installation needed
  - Full-featured interface with error highlighting, severity slider, statistics

### Python Utilities  
- **`prepare_annotations.py`** (200+ lines)
  - Converts Excel → JSON for the annotation tool
  - Supports: Whisper, Phi-4, Parakeet, Granite, Primock
  - Command: `python prepare_annotations.py --input all_result_processed.xlsx --model whisper`

- **`process_annotations.py`** (250+ lines)
  - Converts annotations → Excel/CSV
  - Merges results back into pandas DataFrames
  - Command: `python process_annotations.py --annotations asr_annotations_*.json --original all_result_processed.xlsx`

### Utilities
- **`quickstart.sh`**
  - Automated setup script
  - Interactive menu for model selection
  - Command: `bash quickstart.sh`

- **`example_annotation_analysis.py`** (300+ lines)
  - Example code for analyzing annotated results
  - Statistics, filtering, visualization examples
  - Inter-annotator agreement calculations

---

## 📚 DOCUMENTATION

### Quick Start Guides
- **`QUICK_REFERENCE.txt`** - Visual, ASCII-art based reference
- **`SETUP_GUIDE.md`** - Workflow and setup instructions  
- **`ANNOTATION_TOOL_README.md`** - Comprehensive user manual

### This File
- **`INDEX.md`** - You are here! Complete file inventory

### Summary
- **`FILES_CREATED.md`** - Detailed description of everything created

---

## 🚀 THREE-STEP WORKFLOW

```
Step 1: PREPARE (1 minute)
   $ python prepare_annotations.py --input all_result_processed.xlsx --model whisper
   └─ Creates: whisper_annotation_data.json

Step 2: ANNOTATE (depends on data volume)
   1. Open annotation_interface.html in web browser
   2. Load the JSON file
   3. Click errors to assign taxonomy + severity
   4. Export annotations → asr_annotations_TIMESTAMP.json

Step 3: PROCESS (1 minute)  
   $ python process_annotations.py --annotations asr_annotations_*.json --original all_result_processed.xlsx
   └─ Creates: results_with_annotations.xlsx (ready for analysis!)
```

---

## 📋 FEATURE SUMMARY

### Error Taxonomy (5 Categories)
- 💊 **Medication** - Drug names, dosages
- 🏥 **Clinical Concepts** - Medical terms
- ⏱️ **Temporal** - Dates, times
- 🔢 **Numerics** - Numbers, measurements
- 👤 **Identity** - Names, IDs

### Severity Scale (0-5)
- **0**: None (no impact)
- **1**: Minor (minimal impact)
- **2**: Low (some impact)
- **3**: Medium (notable impact)
- **4**: High (significant clinical impact)
- **5**: Critical (patient safety concerns)

### Error Types
- 🔴 **[DEL: word]** - Deletion (red)
- 🟡 **[SUB: word]** - Substitution (orange)
- 🔵 **[INS: word]** - Insertion (cyan)

---

## 💾 EXAMPLE WORKFLOW COMMANDS

### Quick Start (One Model)
```bash
# Prepare Whisper data
python prepare_annotations.py --input all_result_processed.xlsx --model whisper

# Then open annotation_interface.html and annotate

# Process results
python process_annotations.py --annotations asr_annotations_*.json --original all_result_processed.xlsx
```

### All Models
```bash
for model in whisper phi4 parakeet granite; do
    python prepare_annotations.py --input all_result_processed.xlsx --model $model
done
```

### With Report Generation
```bash
python process_annotations.py \
  --annotations asr_annotations_*.json \
  --original all_result_processed.xlsx \
  --report \
  --report-output detailed_errors.csv
```

### Primock Data
```bash
python prepare_annotations.py --primock primock_result_separate_sheets.xlsx
# Annotate...
python process_annotations.py --annotations asr_annotations_*.json --original all_result_processed.xlsx
```

---

## 📊 OUTPUT FILES

After processing, you get:

| File | Content |
|------|---------|
| `results_with_annotations.xlsx` | Original data + annotation columns |
| `annotation_report.csv` (optional) | One row per error with details |
| `annotation_summary.json` | Overall statistics |

### New Columns in results_with_annotations.xlsx
- `error_taxonomy_annotations` - Full annotation objects
- `error_annotation_summary` - Summary statistics
- `deletion_annotations` - DEL-specific annotations
- `substitution_annotations` - SUB-specific annotations  
- `insertion_annotations` - INS-specific annotations

---

## ✅ REQUIREMENTS

### Python
```bash
pip install pandas openpyxl
```

### Browser
- Chrome 60+
- Firefox 55+
- Safari 12+
- Edge 79+

---

## 🎯 KEY FEATURES

✅ No installation - Open HTML in browser  
✅ Professional UI with error highlighting  
✅ Multi-select taxonomy categorization  
✅ 5-level severity scoring  
✅ Real-time progress tracking  
✅ Statistics and visualization  
✅ Data export/import (JSON)  
✅ Local browser storage  
✅ Supports 4 ASR models + Primock  
✅ Comprehensive documentation  

---

## 🔍 QUICK FILE REFERENCE

| File | Purpose | Type | Lines |
|------|---------|------|-------|
| `annotation_interface.html` | Main annotation tool | HTML/JS | 7000+ |
| `prepare_annotations.py` | Excel → JSON | Python | 200+ |
| `process_annotations.py` | Annotations → Excel | Python | 250+ |
| `example_annotation_analysis.py` | Analysis examples | Python | 300+ |
| `QUICK_REFERENCE.txt` | Visual reference | Text | 250+ |
| `SETUP_GUIDE.md` | Setup & workflow | Markdown | 200+ |
| `ANNOTATION_TOOL_README.md` | Full documentation | Markdown | 400+ |
| `FILES_CREATED.md` | What was created | Markdown | 300+ |
| `quickstart.sh` | Auto setup | Bash | 100+ |

**Total: 8000+ lines of code and documentation**

---

## 🚀 GETTING STARTED IN 30 SECONDS

```bash
# Step 1: Prepare data
python prepare_annotations.py --input all_result_processed.xlsx --model whisper

# Step 2: Open the interface
# → Double-click annotation_interface.html
# → Load the JSON file
# → Start annotating!

# Step 3: Process results
python process_annotations.py --annotations asr_annotations_*.json --original all_result_processed.xlsx
```

---

## 📞 NEED HELP?

1. **Quick answers**: Check [QUICK_REFERENCE.txt](QUICK_REFERENCE.txt)
2. **Setup issues**: See [SETUP_GUIDE.md](SETUP_GUIDE.md)
3. **Feature details**: Read [ANNOTATION_TOOL_README.md](ANNOTATION_TOOL_README.md)
4. **Analysis examples**: Look at [example_annotation_analysis.py](example_annotation_analysis.py)
5. **Troubleshooting**: See "Troubleshooting" section in README

---

## 📈 ANALYSIS CAPABILITIES

After annotating, you can:
- Generate error statistics and reports
- Visualize error distributions
- Compare models (Whisper vs Phi-4 vs Parakeet vs Granite)
- Analyze by taxonomy category
- Focus on critical errors
- Calculate inter-annotator agreement
- Export custom reports

See [example_annotation_analysis.py](example_annotation_analysis.py) for code examples.

---

## 🎉 YOU'RE READY!

Everything is set up and ready to use. Just run:

```bash
python prepare_annotations.py --input all_result_processed.xlsx --model whisper
```

Then open `annotation_interface.html` in your browser.

**Happy annotating!** 🚀

---

**Last Updated**: December 22, 2024  
**Version**: 1.0 Complete  
**Status**: ✅ Ready for use
