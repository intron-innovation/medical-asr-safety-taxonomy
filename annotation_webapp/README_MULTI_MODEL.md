# ASR Annotation Web Application - Multi-Model Version

A Flask-based web application for annotating ASR (Automatic Speech Recognition) errors with support for multiple models.

## Features

- **Multi-Model Support**: Annotators can select from multiple ASR models (whisper, phi4, etc.)
- **Auto-Loading**: Model data is automatically loaded from JSON files
- **User Authentication**: Separate accounts for multiple annotators
- **Progress Tracking**: Track annotation progress per annotator per model
- **Auto-Save**: Annotations are automatically saved to the database
- **Export**: Export annotations filtered by model

## Directory Structure

```
annotation_webapp/
├── app.py                      # Main Flask application
├── models.py                   # Database models
├── config.py                   # Configuration
├── init_db.py                  # Database initialization script
├── setup_data.py               # Data setup helper script
├── data/
│   ├── annotation_data/        # Model JSON files (NEW)
│   │   ├── whisper_annotation_data.json
│   │   ├── phi4_annotation_data.json
│   │   └── {model}_annotation_data.json
│   ├── annotators.json         # Annotator credentials
│   └── annotation_tool.db      # SQLite database
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── select_model.html       # Model selection page (NEW)
│   ├── annotate.html           # Annotation interface
│   └── ...
└── static/
    ├── css/
    └── js/
        └── annotate.js
```

## Setup Instructions

### 1. Install Dependencies

```bash
cd /home/kelechi/bio_ramp_asr/annotation_webapp
pip install -r requirements.txt
```

### 2. Prepare Annotation Data

The app expects model data files in the format: `{model_name}_annotation_data.json`

**Option A: Use the setup script (recommended)**
```bash
python setup_data.py
```

This interactive script will:
- Search for existing annotation JSON files
- Let you copy/rename them to the annotation_data directory
- Validate the JSON format

**Option B: Manual setup**
```bash
# Create directory
mkdir -p data/annotation_data

# Copy your model JSON files
cp /path/to/whisper_annotation_data.json data/annotation_data/
cp /path/to/phi4_annotation_data.json data/annotation_data/
```

### 3. JSON File Format

Each model JSON file should be an array of utterances:

```json
[
  {
    "utterance_id": "unique_id_001",
    "human_transcript": "this is the correct text",
    "asr_reconstructed": "this is [DEL:the] [SUB:correct|currect] text",
    "other_metadata": "optional fields..."
  },
  ...
]
```

**Error Markers:**
- `[DEL:word]` - Deletion (word missing from ASR)
- `[SUB:correct|wrong]` - Substitution (ASR got it wrong)
- `[INS:word]` - Insertion (ASR added extra word)

### 4. Initialize Database

```bash
# First time setup
python init_db.py

# Reset database (deletes all data)
python init_db.py --reset

# View statistics
python init_db.py --stats
```

### 5. Configure Annotators

Edit `data/annotators.json`:

```json
[
  {
    "name": "Alice Smith",
    "email": "alice@example.com",
    "annotator_id": "ANN001"
  },
  {
    "name": "Bob Johnson",
    "email": "bob@example.com",
    "annotator_id": "ANN002"
  }
]
```

### 6. Run the Application

**Development:**
```bash
python app.py
```

Visit: http://localhost:5000

**Production (PythonAnywhere):**
See deployment instructions below.

## Usage Workflow

### For Annotators

1. **Login** - Enter your email and annotator ID
2. **Select Model** - Choose an ASR model to annotate from the list
3. **Annotate Errors**:
   - Click on highlighted errors in the ASR output
   - Select taxonomy categories (phonological, orthographic, etc.)
   - Rate severity (0-5)
   - Submit (auto-saves to database)
4. **Progress** - Your progress is tracked per model
5. **Export** - Export your annotations for a specific model

### For Administrators

**List available models:**
```bash
python setup_data.py list
```

**Add new model:**
```bash
# Copy the JSON file
cp new_model_annotation_data.json data/annotation_data/

# Restart the app
# Annotators will now see the new model in the selection page
```

**View database stats:**
```bash
python init_db.py --stats
```

## Database Schema

### AnnotationData
- Stores utterances per model
- Composite unique constraint: `(utterance_id, model_name)`
- Allows same utterance across different models

### Annotation
- Stores annotations per annotator per model
- Composite unique: `(annotator_id, model_name, utterance_id, error_type, error_match)`
- One annotation per error per annotator per model

### AnnotationProgress
- Tracks annotation position per annotator per model
- Composite unique: `(annotator_id, model_name)`
- Separate progress for each model

## API Endpoints

All endpoints now include `model_name` parameter:

```
GET  /api/utterances/<model_name>           # Get utterances for model
GET  /api/utterance/<model_name>/<index>    # Get specific utterance
GET  /api/annotations/<model_name>          # Get user's annotations
POST /api/annotations/<model_name>          # Save annotation (auto-save)
GET  /api/progress/<model_name>             # Get progress
POST /api/progress/<model_name>             # Update progress
GET  /api/stats/<model_name>                # Get stats for model
GET  /api/export?model=<model_name>         # Export (optional filter)
```

## Deployment to PythonAnywhere

### 1. Update Config

In `config.py`, set absolute paths for production:

```python
class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:////home/YOUR_USERNAME/mysite/data/annotation_tool.db'
```

### 2. Upload Files

Upload the entire `annotation_webapp` directory to PythonAnywhere.

### 3. Configure WSGI

Edit `/var/www/YOUR_USERNAME_pythonanywhere_com_wsgi.py`:

```python
import sys
path = '/home/YOUR_USERNAME/mysite'
if path not in sys.path:
    sys.path.insert(0, path)

from app import app as application
```

### 4. Set Environment

In PythonAnywhere Web tab:
- Virtualenv: `/home/YOUR_USERNAME/.virtualenvs/annotation_env`
- Python version: 3.10

### 5. Create Directories

```bash
cd ~/mysite
mkdir -p data/annotation_data
```

### 6. Initialize Database

```bash
cd ~/mysite
python init_db.py
```

### 7. Upload Data Files

Copy your model JSON files to `data/annotation_data/`

### 8. Reload

Click "Reload" in PythonAnywhere Web tab.

## Troubleshooting

### No models showing up
- Check that JSON files are in `data/annotation_data/`
- Files must match pattern: `*_annotation_data.json`
- Run `python setup_data.py list` to verify

### Database errors
- Run `python init_db.py --reset` to recreate tables
- Check file permissions on `data/annotation_tool.db`

### Auto-save not working
- Check browser console for JavaScript errors
- Verify API endpoints are accessible
- Check that model_name is correctly passed

### Progress not saving
- Ensure AnnotationProgress record exists for (annotator, model)
- Check database schema has model_name field

## Development Notes

### Adding New Models

1. Place JSON file in `data/annotation_data/`
2. Name it: `{model_name}_annotation_data.json`
3. Restart app (auto-discovery on login)

### Database Migrations

If changing schema after deployment:

```python
# In Python console
from app import app, db
with app.app_context():
    db.drop_all()
    db.create_all()
# Then re-run init_db.py
```

### Testing

```python
# Test model discovery
from app import app, get_available_models
with app.app_context():
    models = get_available_models(app)
    print(models)

# Test model loading
from app import load_model_data
with app.app_context():
    result, status = load_model_data(app, 'whisper')
    print(result)
```

## License

MIT License - Feel free to modify for your research needs.

## Contact

For issues or questions, contact the development team.
