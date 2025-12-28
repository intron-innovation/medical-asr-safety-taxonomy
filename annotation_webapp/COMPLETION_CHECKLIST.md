# Multi-Model ASR Annotation System - Completion Checklist

## ✅ Code Changes Complete

### Database Models (models.py)
- [x] Added `model_name` field to `AnnotationData`
- [x] Added `model_name` field to `Annotation`
- [x] Added `model_name` field to `AnnotationProgress`
- [x] Updated composite unique constraints
- [x] Updated `to_dict()` methods to include `modelName`
- [x] Removed foreign key from `Annotation.utterance_id`

### Configuration (config.py)
- [x] Added `ANNOTATION_DATA_DIR` configuration
- [x] Set path to `data/annotation_data`

### Flask Application (app.py)
- [x] Created `get_available_models()` function
- [x] Created `load_model_data()` function
- [x] Updated `/login` route to redirect to model selection
- [x] Created `/select_model` route
- [x] Updated `/annotate/<model_name>` route
- [x] Updated `/api/utterances/<model_name>` endpoint
- [x] Updated `/api/utterance/<model_name>/<index>` endpoint
- [x] Updated `/api/annotations/<model_name>` endpoint
- [x] Updated `/api/progress/<model_name>` endpoint
- [x] Updated `/api/stats/<model_name>` endpoint
- [x] Updated `/api/export` endpoint with model filter

### Templates
- [x] Created `templates/select_model.html`
- [x] Updated `templates/annotate.html` with model context
- [x] Removed file upload controls from annotate.html
- [x] Added model info header to annotate.html
- [x] Added "Switch Model" button

### JavaScript (static/js/annotate.js)
- [x] Added `modelName` variable extraction
- [x] Updated `loadUtterances()` with model parameter
- [x] Updated `loadAnnotations()` with model parameter
- [x] Updated `loadStats()` with model parameter
- [x] Updated `handleAnnotationSubmit()` with model parameter
- [x] Updated `exportAnnotations()` with model filter
- [x] Removed file upload handler
- [x] Added navigation controls (Previous/Next)

### Setup Scripts
- [x] Created `init_db.py` for database initialization
- [x] Created `setup_data.py` for data management
- [x] Created `quickstart.sh` for easy setup
- [x] Made all scripts executable

### Documentation
- [x] Created `README_MULTI_MODEL.md` with full documentation
- [x] Created `IMPLEMENTATION_SUMMARY.md` with technical details
- [x] Created this checklist

### Directory Structure
- [x] Created `data/annotation_data/` directory
- [x] Copied sample data file: `whisper_annotation_data.json`

## 🔄 Testing Checklist (To Be Done)

### Setup Testing
- [ ] Install dependencies (Flask, SQLAlchemy, etc.)
- [ ] Run `python3 init_db.py` successfully
- [ ] Database created at `data/annotation_tool.db`
- [ ] Tables created with correct schema
- [ ] Annotators loaded from JSON

### Model Discovery
- [ ] Place JSON files in `data/annotation_data/`
- [ ] Run `python3 setup_data.py list`
- [ ] Verify models are discovered
- [ ] Check JSON format validation works

### Application Startup
- [ ] Run `python3 app.py`
- [ ] Application starts without errors
- [ ] Visit http://localhost:5000
- [ ] Homepage loads

### Login Flow
- [ ] Login page displays
- [ ] Enter annotator email and ID
- [ ] Successful login redirects to model selection
- [ ] Model selection page shows all available models

### Model Selection
- [ ] All models from annotation_data/ are listed
- [ ] Each model card shows:
  - [ ] Model name
  - [ ] Total utterances count
  - [ ] User's annotation count
  - [ ] Progress bar
  - [ ] "Start/Continue" button
  - [ ] Loaded status badge

### Auto-Loading
- [ ] Click on model (first time)
- [ ] Data automatically loads
- [ ] Flash message confirms loading
- [ ] Utterances count updates
- [ ] Annotate interface displays

### Annotation Interface
- [ ] Model name shown in header
- [ ] Utterance dropdown populated
- [ ] Human transcript displays
- [ ] ASR transcript displays with errors highlighted
- [ ] Click on error opens modal
- [ ] Error context shown correctly
- [ ] Taxonomy checkboxes work
- [ ] Severity slider works
- [ ] Submit saves annotation
- [ ] Success message appears

### Auto-Save
- [ ] Annotation saves to database immediately
- [ ] No manual save button needed
- [ ] Stats update after save
- [ ] Error markers show annotated status (green)

### Progress Tracking
- [ ] Progress saved per (annotator, model)
- [ ] Current index remembered
- [ ] Switching models maintains separate progress
- [ ] Stats show per-model counts

### Model Switching
- [ ] Click "Switch Model" button
- [ ] Returns to model selection
- [ ] Can select different model
- [ ] Previous model progress preserved
- [ ] New model has independent progress

### Multiple Annotators
- [ ] Logout
- [ ] Login as different annotator
- [ ] Independent annotation data
- [ ] Independent progress per model
- [ ] No interference between annotators

### Export Functionality
- [ ] Click Export button
- [ ] File downloads
- [ ] Filename includes model name
- [ ] JSON contains annotations for that model only
- [ ] All annotation data present

### API Endpoints
- [ ] `/api/utterances/<model_name>` returns correct data
- [ ] `/api/utterance/<model_name>/<index>` works
- [ ] `/api/annotations/<model_name>` GET returns user's annotations
- [ ] `/api/annotations/<model_name>` POST saves correctly
- [ ] `/api/progress/<model_name>` GET/POST works
- [ ] `/api/stats/<model_name>` returns correct counts
- [ ] `/api/export?model=<name>` filters correctly

### Database Verification
- [ ] Run `python3 init_db.py --stats`
- [ ] Correct counts displayed
- [ ] Models listed correctly
- [ ] Annotations grouped by model

### Edge Cases
- [ ] Empty annotation_data/ directory handled
- [ ] Invalid JSON file handled gracefully
- [ ] Missing model_name in request handled
- [ ] Database errors don't crash app
- [ ] Concurrent annotations work

## 🚀 Deployment Checklist (PythonAnywhere)

### File Upload
- [ ] Upload entire `annotation_webapp/` directory
- [ ] Preserve directory structure
- [ ] All files transferred

### Configuration
- [ ] Update `config.py` with absolute paths
- [ ] Set `ProductionConfig` as default
- [ ] Database path: `/home/USERNAME/mysite/data/annotation_tool.db`

### Directory Setup
- [ ] Create `data/annotation_data/` on server
- [ ] Upload model JSON files
- [ ] Set correct permissions (755 for dirs, 644 for files)

### Dependencies
- [ ] Create virtualenv
- [ ] Install Flask
- [ ] Install Flask-SQLAlchemy
- [ ] Install flask-cors

### WSGI Configuration
- [ ] Edit WSGI file
- [ ] Add path to sys.path
- [ ] Import app as application
- [ ] Set virtualenv path in Web tab

### Database Initialization
- [ ] Run `python3 init_db.py` on server
- [ ] Verify database created
- [ ] Check tables exist
- [ ] Verify annotators loaded

### Testing
- [ ] Visit webapp URL
- [ ] Test login
- [ ] Test model selection
- [ ] Test annotation workflow
- [ ] Test export

### Monitoring
- [ ] Check error logs
- [ ] Verify auto-save working
- [ ] Monitor database size
- [ ] Check for SQLite locking issues

## 📊 Validation Queries

Run these in Python console to verify:

```python
from app import app, db
from models import *

with app.app_context():
    # Check models
    print("Models loaded:")
    models = db.session.query(AnnotationData.model_name).distinct().all()
    for m in models:
        print(f"  - {m[0]}")
    
    # Check annotations per model
    print("\nAnnotations by model:")
    from sqlalchemy import func
    stats = db.session.query(
        Annotation.model_name,
        func.count(Annotation.id)
    ).group_by(Annotation.model_name).all()
    for model, count in stats:
        print(f"  {model}: {count}")
    
    # Check progress tracking
    print("\nProgress records:")
    progress = AnnotationProgress.query.all()
    for p in progress:
        print(f"  Annotator {p.annotator_id}, Model {p.model_name}: Index {p.current_utterance_index}")
```

## 🐛 Common Issues & Solutions

### Issue: No models showing
**Solution:** 
- Check files in `data/annotation_data/`
- Verify filename pattern: `{model}_annotation_data.json`
- Run `python3 setup_data.py list`

### Issue: Database errors
**Solution:**
- Reset database: `python3 init_db.py --reset`
- Check file permissions
- Verify SQLite installed

### Issue: Auto-save not working
**Solution:**
- Check browser console for errors
- Verify API endpoints return 200
- Check model_name is passed correctly

### Issue: Progress not saving
**Solution:**
- Verify AnnotationProgress record exists
- Check composite unique constraint
- Run `init_db.py --stats` to verify schema

## 📝 Final Notes

All code changes are complete and ready for testing. The system is designed to:

1. **Auto-discover** models from `annotation_data/` directory
2. **Auto-load** model data on first access
3. **Auto-save** annotations with model context
4. **Track progress** independently per annotator per model
5. **Support** multiple models and multiple annotators simultaneously

To get started, run:
```bash
./quickstart.sh
```

Then follow the testing checklist above to verify everything works correctly.
