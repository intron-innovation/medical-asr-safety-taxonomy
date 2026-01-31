# Multi-Error Annotation Implementation Guide

## Problem Statement

Previously, when an error text occurred multiple times in an utterance (e.g., `[INS:okay]` appearing 3 times), the system treated all occurrences as identical. This prevented proper annotation of each occurrence separately because they all shared the same key identifier.

## Solution Overview

The system now generates **unique identifiers (UUIDs)** for each error occurrence, allowing multiple annotations of the same error text at different positions within the same utterance.

## Files Modified

### 1. **Database Models** (`models.py`)

**Changes:**
- Added `error_id` field to the `Annotation` model (UUID, indexed)
- Modified unique constraint from:
  ```python
  ('annotator_id', 'model_name', 'utterance_id', 'error_type', 'error_match')
  ```
  to:
  ```python
  ('annotator_id', 'error_id')
  ```
- Updated `to_dict()` method to include `errorId` in API responses

**Impact:**
- Each error now has a unique identifier independent of its text content
- Multiple annotations of the same error text are now possible
- Annotators can only annotate each specific error instance once (enforced by the constraint)

### 2. **Error Extraction Module** (`error_extractor.py`) - NEW FILE

**What it does:**
- Extracts all errors from ASR reconstructed text using regex patterns
- Assigns a unique UUID to each error occurrence
- Preserves error metadata (type, position, text content)

**Key Classes:**
- `ErrorExtractor`: Static utility class for error extraction

**Key Methods:**
```python
@staticmethod
def extract_errors(asr_text: str) -> List[Dict]:
    """Extract all errors with unique IDs"""
    
@staticmethod  
def enrich_annotation_data(data_list: List[Dict]) -> List[Dict]:
    """Add error extraction to annotation data items"""
```

**Error Structure Returned:**
```json
{
  "error_id": "550e8400-e29b-41d4-a716-446655440000",
  "error_type": "INS",
  "error_match": "[INS:okay]",
  "error_text": "okay",
  "position": 0,
  "start_idx": 12,
  "end_idx": 24
}
```

### 3. **Flask Application** (`app.py`)

**Changes:**

#### Import Addition:
```python
from error_extractor import ErrorExtractor
```

#### `load_model_data()` Function:
- Now calls `ErrorExtractor.extract_errors()` when loading annotation data
- Stores extracted errors with unique IDs in the `extra_data` field
- Each utterance now includes an `errors` list and `error_count`

#### Annotation Handling Endpoint:
- Modified POST handler to require `errorId` parameter
- Changed query filter to use `error_id` instead of combined error fields:
  ```python
  # OLD: Uses multiple fields
  existing = Annotation.query.filter_by(
      annotator_id=session['annotator_id'],
      model_name=model_name,
      utterance_id=data['utteranceId'],
      error_type=data['errorType'],
      error_match=data['errorMatch']
  ).first()
  
  # NEW: Uses single error_id
  existing = Annotation.query.filter_by(
      annotator_id=session['annotator_id'],
      error_id=error_id
  ).first()
  ```
- Validates that `errorId` is provided in the request

### 4. **Frontend JavaScript** (`static/js/annotate.js`)

**Global Variables Updated:**
- `currentErrorKey` → `currentErrorId` (now stores UUID instead of composite key)
- Added `errorIdMap` to track error metadata

**Key Function Changes:**

#### `highlightErrors(text, utteranceId)`:
- Now uses error data from `utterance.metadata.errors` 
- Falls back to legacy method if errors not in metadata
- Associates each highlighted error with its unique `error_id`
- Handles multiple occurrences of the same error text correctly

#### `openAnnotationModal(errorId, errorType, fullMatch, errorText)`:
- Now takes `errorId` as first parameter
- Displays the error ID in the modal for transparency
- Retrieves error data from the backend errors array

#### `handleAnnotationSubmit(e)`:
- Includes `errorId` in the payload sent to the server
- Finds error metadata by looking up the error_id in the errors array
- Stores annotations indexed by `error_id` in local cache

#### `loadAnnotations()`:
- Now indexes annotations by `error_id` for efficient lookup
- Maintains legacy keys for backward compatibility

### 5. **API Response Format** (`models.py`)

The annotation `to_dict()` method now returns:
```json
{
  "id": 123,
  "errorId": "550e8400-e29b-41d4-a716-446655440000",
  "annotatorId": "ann001",
  "modelName": "whisper",
  "utteranceId": "RES0141",
  "errorType": "INS",
  "errorMatch": "[INS:okay]",
  "taxonomy": ["mispronunciation", "phonetic"],
  "severity": 3,
  "timestamp": "2026-01-30T10:45:00",
  "utteranceIndex": 0,
  "context": {
    "humanTranscript": "...",
    "asrReconstructed": "..."
  }
}
```

## How It Works - End-to-End

### 1. **Data Loading Phase**
```
JSON File → ErrorExtractor.extract_errors() → Unique Error IDs
                                               ↓
                                          Store in DB with metadata
```

### 2. **Frontend Display Phase**
```
Load Utterance → Get errors array with IDs → highlightErrors() 
                                               ↓
                                     Create clickable spans
                                     each linked to error_id
```

### 3. **Annotation Phase**
```
Click Error → openAnnotationModal(errorId) → Show form with UUID
                                              ↓
                                     Submit annotation with errorId
                                              ↓
                                     Save to DB indexed by errorId
```

### 4. **Retrieval Phase**
```
Load page → Fetch annotations → Index by error_id → Mark as annotated
```

## Example: Multiple Occurrences of Same Error

**Input ASR Text:**
```
"okay [INS:okay] world [DEL:okay] test [INS:okay] done"
```

**Extracted Errors:**
```json
[
  {
    "error_id": "uuid-1",
    "error_type": "INS",
    "error_match": "[INS:okay]",
    "error_text": "okay",
    "position": 0
  },
  {
    "error_id": "uuid-2",
    "error_type": "DEL",
    "error_match": "[DEL:okay]",
    "error_text": "okay",
    "position": 1
  },
  {
    "error_id": "uuid-3",
    "error_type": "INS",
    "error_match": "[INS:okay]",
    "error_text": "okay",
    "position": 2
  }
]
```

**Result:**
- Annotator can annotate `uuid-1`, `uuid-2`, and `uuid-3` independently
- Each has its own annotation record in the database
- No conflicts even though two are `[INS:okay]`

## Backward Compatibility

- If uploaded JSON files don't have error IDs, they're generated on first load
- Frontend falls back to legacy highlighting if errors aren't in metadata
- Existing annotation queries maintain compatibility through dual indexing

## Migration Notes

**If you have existing data:**

1. The new system will automatically generate error IDs when data is reloaded
2. Old annotations remain unchanged (they have their own records)
3. To consolidate, you may need to re-annotate utterances for full benefit

**To reset and reload:**
```bash
# Reset the database
python init_db.py --reset

# This will automatically extract errors with new UUIDs
# during the data loading process
```

## Testing

Test file locations:
- Error extractor tests: Run `error_extractor.py` directly
- Integration tests: See `error_extractor.py` example at bottom

Example test in `error_extractor.py`:
```python
test_text = "hello [DEL:world] [INS:okay] world [DEL:okay] [INS:okay] test"
errors = ErrorExtractor.extract_errors(test_text)
# Returns 5 errors with unique IDs, even though 2 are [INS:okay]
```

## Future Enhancements

1. **Batch Operations**: Process multiple errors at once
2. **Error Metrics**: Track annotation agreement per error_id
3. **Error Patterns**: Identify common error combinations
4. **Performance**: Add caching for frequently accessed error IDs
5. **Export**: Include error_id in export/reporting
