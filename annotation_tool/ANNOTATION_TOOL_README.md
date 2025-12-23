# ASR Error Annotation Tool

A comprehensive web-based interface for annotating ASR errors with error taxonomy classification and severity scoring.

## Overview

This tool allows human annotators to:
- View human transcripts and ASR reconstructed output side-by-side
- Identify and examine errors (Deletions, Substitutions, Insertions)
- Classify errors into taxonomy categories:
  - **Medication** 💊
  - **Clinical Concepts** 🏥
  - **Temporal** ⏱️
  - **Numerics** 🔢
  - **Identity** 👤
- Assign severity scores (0-5) to each error
- Export annotations for further analysis

## Files

### Main Interface
- **`annotation_interface.html`** - The web-based annotation interface (open in any modern browser)

### Python Utilities
- **`prepare_annotations.py`** - Converts processed Excel results into JSON format for the annotation tool
- **`process_annotations.py`** - Merges annotation results back into your pandas DataFrame

## Quick Start

### Step 1: Prepare Your Data

Convert your processed ASR results into annotation format:

```bash
# For a single model (default: Whisper)
python prepare_annotations.py --input all_result_processed.xlsx --model whisper

# For other models
python prepare_annotations.py --input all_result_processed.xlsx --model phi4
python prepare_annotations.py --input all_result_processed.xlsx --model parakeet
python prepare_annotations.py --input all_result_processed.xlsx --model granite

# For Primock data (doctor-patient conversations)
python prepare_annotations.py --primock primock_result_separate_sheets.xlsx
```

This creates a JSON file (e.g., `whisper_annotation_data.json`) ready for annotation.

### Step 2: Open the Annotation Interface

1. Open `annotation_interface.html` in your web browser (Chrome, Firefox, Safari, Edge recommended)
2. Click **📁 Load JSON File**
3. Select the JSON file created in Step 1
4. The interface loads all utterances

### Step 3: Annotate Errors

1. **Browse utterances** using the dropdown selector
2. **View transcripts** side-by-side:
   - Left: Human transcript (reference)
   - Right: ASR output with errors highlighted
3. **Click on any error** (colored text) to open the annotation modal
4. **Classify the error**:
   - Select one or more taxonomy categories (checkbox)
   - Assign a severity score (0-5 slider)
5. **Save** and move to the next error

### Error Types (Highlighted)

- 🔴 **[DEL: word]** - Words deleted by ASR (shown in red)
- 🟡 **[SUB: word]** - Words substituted by ASR (shown in orange)
- 🔵 **[INS: word]** - Words inserted by ASR (shown in cyan)

### Severity Scale

- **0 - None**: No impact on understanding
- **1 - Minor**: Minimal impact, easily overlooked
- **2 - Low**: Some impact but context preserved
- **3 - Medium**: Notable impact on meaning
- **4 - High**: Significant impact on clinical information
- **5 - Critical**: Severe impact, patient safety or care concerns

## Features

### Visual Indicators
- **Green dot** 🟢: Error has been annotated
- **Orange dot** 🟠: Error needs annotation
- **Progress bar**: Shows annotation completion percentage

### Statistics Dashboard
- Total utterances and errors
- Annotation progress
- Error distribution (types, taxonomy, severity)

### Summary Tab
- Visual charts showing:
  - Error type distribution (pie chart)
  - Taxonomy usage (bar chart)
  - Severity distribution (bar chart)

### Export & Save
- Click **💾 Export Annotations** to download `asr_annotations_TIMESTAMP.json`
- Annotations auto-save in browser while working
- Use browser's "Save Page As" for backup

## Processing Results

### Step 4: Merge Annotations Back

After annotation, process results back into your DataFrame:

```bash
# Merge annotations with original data
python process_annotations.py --annotations asr_annotations_1234567890.json --original all_result_processed.xlsx

# Also create a detailed CSV report
python process_annotations.py --annotations asr_annotations_1234567890.json --original all_result_processed.xlsx --report

# Custom output filename
python process_annotations.py --annotations asr_annotations_1234567890.json --original all_result_processed.xlsx --output custom_results.xlsx
```

This creates:
- **`results_with_annotations.xlsx`** - Your original data with annotation columns added:
  - `error_taxonomy_annotations` - Full annotation objects
  - `error_annotation_summary` - Summary statistics
  - `deletion_annotations` - Deletion-specific annotations
  - `substitution_annotations` - Substitution-specific annotations
  - `insertion_annotations` - Insertion-specific annotations

- **`annotation_report.csv`** (optional) - Detailed report with one row per annotated error

## Data Format

### Input JSON Format (from prepare_annotations.py)
```json
[
  {
    "utterance_id": "utt_001",
    "human_transcript": "how can i help you",
    "asr_reconstructed": "how [INS: ++can++] i help you [DEL: __today__]",
    "model": "whisper",
    "wer": 0.25,
    "index": 0
  },
  ...
]
```

### Output JSON Format (from annotation interface)
```json
{
  "exported_at": "2024-12-22T10:30:00Z",
  "total_annotations": 45,
  "annotations": {
    "0": [
      {
        "utterance_id": "utt_001",
        "error_type": "INS",
        "error_match": "[INS: ++can++]",
        "taxonomy": ["Clinical Concepts"],
        "severity": 2,
        "timestamp": "2024-12-22T10:25:30Z"
      }
    ]
  }
}
```

## Keyboard Shortcuts

- **Arrow Keys** ← → : Navigate between utterances
- **Escape** : Close annotation modal
- **Ctrl+S** / **Cmd+S** : Browser save (exports current state)

## Browser Requirements

- Modern browser with ES6+ support:
  - Chrome 60+
  - Firefox 55+
  - Safari 12+
  - Edge 79+

## Tips for Annotators

1. **Read both transcripts carefully** before annotating
2. **Consider clinical context** when assigning severity
3. **Use multiple taxonomy tags** if an error affects multiple categories
4. **Track patterns** - look for recurring issues
5. **Take breaks** to avoid fatigue during long sessions
6. **Export frequently** to save your progress

## Example Workflow

```bash
# Prepare data
python prepare_annotations.py --input all_result_processed.xlsx --model whisper

# Open annotation_interface.html
# ... annotate errors ...
# Export as asr_annotations_1234567890.json

# Process results
python process_annotations.py \
  --annotations asr_annotations_1234567890.json \
  --original all_result_processed.xlsx \
  --report

# Now use results_with_annotations.xlsx in your analysis!
```

## Troubleshooting

### "JSON file won't load"
- Ensure file is valid JSON (check prepare_annotations.py output)
- Try a different browser
- Check browser console for errors (F12)

### "Missing columns in Excel"
- Ensure you're using all_result_processed.xlsx or the correctly prepared file
- Run prepare_annotations.py with correct --model parameter

### "Annotations not saving"
- Check browser's local storage (may have storage limits)
- Always click "Export Annotations" to save work
- Some browsers clear storage on close - use incognito/private mode carefully

### "Visualization charts not showing"
- Ensure internet connection (Chart.js is CDN-hosted)
- Try refreshing the page
- Check if JavaScript is enabled

## Advanced Usage

### Custom Taxonomy Categories

To add or modify taxonomy categories, edit the `taxonomyLabels` object in the HTML:

```javascript
const taxonomyLabels = {
    'Medication': '💊',
    'Clinical Concepts': '🏥',
    'Temporal': '⏱️',
    'Numerics': '🔢',
    'Identity': '👤',
    'YourNewCategory': '✨' // Add new category
};
```

And add corresponding HTML checkboxes in the modal.

### Batch Processing Multiple Models

```bash
for model in whisper phi4 parakeet granite; do
    python prepare_annotations.py --input all_result_processed.xlsx --model $model
done
```

## Support

For issues, ensure:
1. You're using the latest version of the tool
2. Your Excel file contains all required columns
3. Browser console shows no JavaScript errors (F12)
4. File paths are absolute or relative to current directory

## Citation

If you use this tool in your research, please cite:

```bibtex
@software{asr_annotation_tool,
  title={ASR Error Annotation Tool},
  year={2024},
  url={https://github.com/yourusername/asr-annotation-tool}
}
```

---

**Last Updated**: December 2024
