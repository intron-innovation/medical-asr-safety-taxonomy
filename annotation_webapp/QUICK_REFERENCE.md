# Quick Reference: Error ID Implementation

## Files Changed
- ✅ `models.py` - Added `error_id` column and updated constraints
- ✅ `app.py` - Updated data loading and annotation handling
- ✅ `error_extractor.py` - NEW: Error extraction with UUID generation
- ✅ `static/js/annotate.js` - Updated frontend error handling
- ✅ `MULTI_ERROR_ANNOTATION.md` - Detailed documentation

## Key Differences: Before vs After

### Before (Error Duplicate Problem)
```
Text: "hello [INS:okay] world [INS:okay] test"

Unique Keys:
- "utt1_INS_[INS:okay]"  ← SAME KEY for both occurrences
- "utt1_INS_[INS:okay]"  ← Cannot annotate each separately!
```

### After (With Error IDs)
```
Text: "hello [INS:okay] world [INS:okay] test"

Unique Keys:
- error_id: "550e8400-e29b-41d4-a716-446655440000" ← First [INS:okay]
- error_id: "6ba7b810-9dad-11d1-80b4-00c04fd430c8" ← Second [INS:okay]

Result: ✅ Each can be annotated independently
```

## Database Schema Changes

### Annotation Table
```python
# NEW COLUMN
error_id = db.Column(db.String(36), nullable=False, index=True)  # UUID

# NEW UNIQUE CONSTRAINT
__table_args__ = (
    db.UniqueConstraint('annotator_id', 'error_id', 
                       name='_annotator_error_instance_uc'),
)

# OLD CONSTRAINT (REMOVED)
# db.UniqueConstraint('annotator_id', 'model_name', 'utterance_id', 
#                     'error_type', 'error_match')
```

## API Changes

### POST /api/annotations/<model_name>

**Before:**
```json
{
  "utteranceId": "RES0141",
  "errorType": "INS",
  "errorMatch": "[INS:okay]",
  "taxonomy": ["phonetic"],
  "severity": 3
}
```

**After:**
```json
{
  "errorId": "550e8400-e29b-41d4-a716-446655440000",
  "utteranceId": "RES0141",
  "errorType": "INS",
  "errorMatch": "[INS:okay]",
  "taxonomy": ["phonetic"],
  "severity": 3
}
```

**Required:** `errorId` must be provided (will fail with 400 if missing)

### GET /api/annotations/<model_name>

**Response now includes:**
```json
{
  "errorId": "550e8400-e29b-41d4-a716-446655440000",
  "annotatorId": "ann001",
  "errorType": "INS",
  "errorMatch": "[INS:okay]",
  "...": "other fields"
}
```

## JavaScript Changes

### Error Indexing
```javascript
// OLD
const key = `${utteranceId}_${errorType}_${errorMatch}`;
userAnnotations[key] = annotation;

// NEW  
const errorId = annotation.error_id;
userAnnotations[errorId] = annotation;
```

### Modal Opening
```javascript
// OLD
openAnnotationModal(errorType, fullMatch, errorText)

// NEW
openAnnotationModal(errorId, errorType, fullMatch, errorText)
```

### Error Lookup
```javascript
// NEW: Find error by ID
const errorData = errors.find(e => e.error_id === currentErrorId);
```

## Error Extraction Process

### Step 1: Text Input
```
"hello [DEL:world] [INS:okay] test [INS:okay]"
```

### Step 2: Regex Matching
```
Pattern: \[([A-Z]+):([^\]]+)\]
Matches:
- [DEL:world]     → type=DEL, text=world
- [INS:okay]      → type=INS, text=okay  
- [INS:okay]      → type=INS, text=okay  (duplicate text)
```

### Step 3: UUID Generation & Return
```json
[
  {
    "error_id": "uuid-1",
    "error_type": "DEL",
    "error_match": "[DEL:world]",
    "error_text": "world",
    "position": 0
  },
  {
    "error_id": "uuid-2",
    "error_type": "INS",
    "error_match": "[INS:okay]",
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

## Usage Examples

### Python: Extract Errors
```python
from error_extractor import ErrorExtractor

text = "hello [INS:world] [INS:world] test"
errors = ErrorExtractor.extract_errors(text)

for error in errors:
    print(f"ID: {error['error_id']}")
    print(f"Type: {error['error_type']}")
    print(f"Text: {error['error_text']}")
    # Output: Prints 2 errors with different IDs
```

### JavaScript: Submit Annotation
```javascript
// In handleAnnotationSubmit():
const errorId = currentErrorId;  // UUID from error_id field
const payload = {
    errorId: errorId,  // ← Required!
    errorType: "INS",
    errorMatch: "[INS:okay]",
    taxonomy: ["phonetic"],
    severity: 3
};

await fetch(`/api/annotations/${modelName}`, {
    method: 'POST',
    body: JSON.stringify(payload)
});
```

### Database Query: Find Annotations
```python
# Get all annotations for a specific error
annotations = Annotation.query.filter_by(
    error_id='550e8400-e29b-41d4-a716-446655440000'
).all()

# Get annotations for specific annotator and error
annotation = Annotation.query.filter_by(
    annotator_id='ann001',
    error_id='550e8400-e29b-41d4-a716-446655440000'
).first()
```

## Debugging Checklist

- [ ] Error IDs are UUIDs (36 characters, hyphens)
- [ ] Each error occurrence gets a unique ID
- [ ] Duplicate error texts have different IDs
- [ ] Database constraint is `(annotator_id, error_id)`
- [ ] API requires `errorId` in payload
- [ ] Frontend passes `errorId` when submitting
- [ ] Annotations are keyed by `error_id` in cache

## Performance Considerations

- **Index:** `error_id` is indexed for fast lookups
- **UUID:** Generated once at load time, cached
- **Memory:** Error metadata stored in `extra_data` JSON
- **Query:** Single-column unique constraint is faster than composite

## Rollback Instructions

If you need to revert:

1. Drop the `error_id` column from Annotation table
2. Revert unique constraint to composite key
3. Remove import of ErrorExtractor from app.py
4. Revert JavaScript changes in annotate.js
5. Restore old annotation handling logic

## Migration to Production

1. **Backup database** before making changes
2. **Test** with a small subset of data first
3. **Deploy** the new files
4. **Run** `python init_db.py --reset` to reload with error IDs
5. **Verify** that errors are extracted with unique IDs
6. **Check** that annotations work correctly with new format
