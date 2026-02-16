"""Main Flask application for ASR Annotation Tool."""
import json
from datetime import datetime
from pathlib import Path
from functools import wraps

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from werkzeug.utils import secure_filename

from models import db, Annotator, Annotation, AnnotationData, AnnotationProgress
from config import config
from error_extractor import ErrorExtractor


def get_available_models(app):
    """Get list of available ASR models from annotation_data directory."""
    annotation_data_dir = app.config['ANNOTATION_DATA_DIR']
    if not annotation_data_dir.exists():
        return []
    
    models = []
    for json_file in annotation_data_dir.glob('*_annotation_data.json'):
        model_name = json_file.stem.replace('_annotation_data', '')
        models.append({
            'name': model_name,
            'display_name': model_name.upper(),
            'file': json_file.name,
            'path': json_file
        })
    return sorted(models, key=lambda x: x['name'])


def load_model_data(app, model_name):
    """Load annotation data for a specific model into database."""
    annotation_data_dir = app.config['ANNOTATION_DATA_DIR']
    json_file = annotation_data_dir / f'{model_name}_annotation_data.json'
    
    if not json_file.exists():
        return {'error': f'Data file not found: {json_file.name}'}, 404
    
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        loaded_count = 0
        for item in data:
            utterance_id = item.get('utterance_id')
            if not utterance_id:
                continue
            
            # Check if already exists for this model
            existing = AnnotationData.query.filter_by(
                utterance_id=utterance_id,
                model_name=model_name
            ).first()
            
            if existing:
                continue
            
            # Extract errors with unique IDs
            asr_text = item.get('asr_reconstructed', '')
            errors = ErrorExtractor.extract_errors(asr_text)
            
            # Store errors in extra_data
            item['errors'] = errors
            item['error_count'] = len(errors)
            
            utterance = AnnotationData(
                utterance_id=utterance_id,
                model_name=model_name,
                human_transcript=item.get('human_transcript', ''),
                asr_reconstructed=asr_text,
                extra_data=item
            )
            db.session.add(utterance)
            loaded_count += 1
        
        db.session.commit()
        return {'success': True, 'loaded': loaded_count, 'total': len(data)}, 200
    
    except Exception as e:
        db.session.rollback()
        return {'error': str(e)}, 400


def load_annotators(app):
    """Load pre-registered annotators from JSON file."""
    annotators_file = app.config['ANNOTATORS_FILE']
    if not annotators_file.exists():
        return
    
    try:
        with open(annotators_file, 'r') as f:
            data = json.load(f)
            annotators_list = data.get('annotators', [])
        
        for ann_data in annotators_list:
            existing = Annotator.query.filter_by(annotator_id=ann_data['annotatorId']).first()
            if not existing:
                annotator = Annotator(
                    annotator_id=ann_data['annotatorId'],
                    name=ann_data['name'],
                    email=ann_data['email'],
                    affiliation=ann_data.get('affiliation')
                )
                db.session.add(annotator)
        
        db.session.commit()
    except Exception as e:
        print(f"Error loading annotators: {e}")


def create_app(config_name='development'):
    """Application factory."""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    
    # Create tables and load initial data
    with app.app_context():
        db.create_all()
        load_annotators(app)
    
    return app


app = create_app()


def login_required(f):
    """Decorator to require login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'annotator_id' not in session:
            flash('Please login first', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# ============================================================================
# ROUTES
# ============================================================================

@app.route('/')
def index():
    """Landing page."""
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page."""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        annotator_id = request.form.get('annotatorId', '').strip().upper()
        
        # Validate credentials
        annotator = Annotator.query.filter_by(
            email=email,
            annotator_id=annotator_id
        ).first()
        
        if annotator:
            session['annotator_id'] = annotator.annotator_id
            session['annotator_name'] = annotator.name
            session['annotator_email'] = annotator.email
            session['affiliation'] = annotator.affiliation
            session.permanent = True
            
            flash(f'Welcome, {annotator.name}!', 'success')
            return redirect(url_for('select_model'))
        else:
            flash('Invalid email or annotator ID', 'error')
    
    return render_template('login.html')


@app.route('/logout')
def logout():
    """Logout user."""
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('index'))


@app.route('/instructions')
@login_required
def instructions():
    """Instructions page."""
    return render_template('instructions.html')


@app.route('/select_model')
@login_required
def select_model():
    """Model selection page."""
    models = get_available_models(app)
    
    # Get stats for each model
    for model in models:
        total_utterances = AnnotationData.query.filter_by(model_name=model['name']).count()
        user_annotations = Annotation.query.filter_by(
            annotator_id=session['annotator_id'],
            model_name=model['name']
        ).count()
        
        model['total_utterances'] = total_utterances
        model['user_annotations'] = user_annotations
        model['loaded'] = total_utterances > 0
    
    return render_template('select_model.html', models=models)


@app.route('/annotate/<model_name>')
@login_required
def annotate(model_name):
    """Annotation interface for specific model."""
    # Auto-load model data if not already loaded
    existing_count = AnnotationData.query.filter_by(model_name=model_name).count()
    if existing_count == 0:
        result, status = load_model_data(app, model_name)
        if status != 200:
            flash(f'Error loading model data: {result.get("error")}', 'error')
            return redirect(url_for('select_model'))
        flash(f'Loaded {result["loaded"]} utterances for {model_name}', 'success')
    
    # Get or create annotation progress for this model
    progress = AnnotationProgress.query.filter_by(
        annotator_id=session['annotator_id'],
        model_name=model_name
    ).first()
    
    if not progress:
        progress = AnnotationProgress(
            annotator_id=session['annotator_id'],
            model_name=model_name
        )
        db.session.add(progress)
        db.session.commit()
    
    # Get total utterances for this model
    total_utterances = AnnotationData.query.filter_by(model_name=model_name).count()
    
    # Get annotation stats for this user and model
    total_annotations = Annotation.query.filter_by(
        annotator_id=session['annotator_id'],
        model_name=model_name
    ).count()
    
    return render_template(
        'annotate.html',
        model_name=model_name,
        current_index=progress.current_utterance_index if progress else 0,
        total_utterances=total_utterances,
        total_annotations=total_annotations
    )


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/api/utterances/<model_name>')
@login_required
def get_utterances(model_name):
    """Get all utterances for a specific model."""
    utterances = AnnotationData.query.filter_by(model_name=model_name).order_by(AnnotationData.id).all()
    return jsonify([utt.to_dict() for utt in utterances])


@app.route('/api/utterance/<model_name>/<int:index>')
@login_required
def get_utterance_by_index(model_name, index):
    """Get utterance by index for a specific model."""
    utterances = AnnotationData.query.filter_by(model_name=model_name).order_by(AnnotationData.id).all()
    if 0 <= index < len(utterances):
        return jsonify(utterances[index].to_dict())
    return jsonify({'error': 'Index out of range'}), 404


@app.route('/api/annotations/<model_name>', methods=['GET', 'POST'])
@login_required
def handle_annotations(model_name):
    """Get or save annotations for a specific model."""
    if request.method == 'GET':
        # Get all annotations for current user and model
        annotations = Annotation.query.filter_by(
            annotator_id=session['annotator_id'],
            model_name=model_name
        ).all()
        return jsonify([ann.to_dict() for ann in annotations])
    
    elif request.method == 'POST':
        # Save new annotation
        data = request.get_json()
        
        try:
            # Each error must have an error_id to support multiple annotations of the same text
            error_id = data.get('errorId')
            if not error_id:
                return jsonify({'error': 'error_id is required'}), 400
            
            # Upsert annotation using error_id as unique identifier
            existing = Annotation.query.filter_by(
                annotator_id=session['annotator_id'],
                error_id=error_id
            ).first()
            
            if existing:
                existing.taxonomy = data['taxonomy']
                existing.severity = data['severity']
                existing.timestamp = datetime.utcnow()
                existing.human_transcript = data.get('humanTranscript')
                existing.asr_transcript = data.get('asrTranscript')
                existing.asr_reconstructed = data.get('asrReconstructed')
                existing.utterance_index = data.get('utteranceIndex')
                action = 'updated'
            else:
                annotation = Annotation(
                    annotator_id=session['annotator_id'],
                    error_id=error_id,
                    model_name=model_name,
                    utterance_id=data['utteranceId'],
                    error_type=data['errorType'],
                    error_match=data['errorMatch'],
                    taxonomy=data['taxonomy'],
                    severity=data['severity'],
                    utterance_index=data.get('utteranceIndex'),
                    human_transcript=data.get('humanTranscript'),
                    asr_transcript=data.get('asrTranscript'),
                    asr_reconstructed=data.get('asrReconstructed')
                )
                db.session.add(annotation)
                action = 'created'
            
            db.session.commit()
            
            # Get updated count
            count = Annotation.query.filter_by(
                annotator_id=session['annotator_id'],
                model_name=model_name
            ).count()
            
            return jsonify({
                'success': True,
                'action': action,
                'count': count
            })
        
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 400


@app.route('/api/progress/<model_name>', methods=['GET', 'POST'])
@login_required
def handle_progress(model_name):
    """Get or update annotation progress for a specific model."""
    progress = AnnotationProgress.query.filter_by(
        annotator_id=session['annotator_id'],
        model_name=model_name
    ).first()
    
    if not progress:
        progress = AnnotationProgress(
            annotator_id=session['annotator_id'],
            model_name=model_name
        )
        db.session.add(progress)
        db.session.commit()
    
    if request.method == 'GET':
        return jsonify(progress.to_dict())
    
    elif request.method == 'POST':
        data = request.get_json()
        
        if 'currentUtteranceIndex' in data:
            progress.current_utterance_index = data['currentUtteranceIndex']
        
        if 'completedUtterances' in data:
            progress.completed_utterances = data['completedUtterances']
        
        progress.last_accessed = datetime.utcnow()
        db.session.commit()
        
        return jsonify(progress.to_dict())


@app.route('/api/stats/<model_name>')
@login_required
def get_stats(model_name):
    """Get annotation statistics for a specific model."""
    annotator_id = session['annotator_id']
    
    total_utterances = AnnotationData.query.filter_by(model_name=model_name).count()
    total_annotations = Annotation.query.filter_by(
        annotator_id=annotator_id,
        model_name=model_name
    ).count()
    
    # Count errors in all utterances for this model
    utterances = AnnotationData.query.filter_by(model_name=model_name).all()
    total_errors = 0
    for utt in utterances:
        # Count error markers
        total_errors += utt.asr_reconstructed.count('[DEL:')
        total_errors += utt.asr_reconstructed.count('[SUB:')
        total_errors += utt.asr_reconstructed.count('[INS:')
    
    progress = AnnotationProgress.query.filter_by(
        annotator_id=annotator_id,
        model_name=model_name
    ).first()
    current_index = progress.current_utterance_index if progress else 0
    
    return jsonify({
        'totalUtterances': total_utterances,
        'totalAnnotations': total_annotations,
        'totalErrors': total_errors,
        'currentIndex': current_index,
        'progress': round((total_annotations / total_errors * 100) if total_errors > 0 else 0, 1)
    })


@app.route('/api/export')
@login_required
def export_annotations():
    """Export annotations to JSON (optionally filtered by model)."""
    model_name = request.args.get('model')  # Optional model filter
    
    query = Annotation.query.filter_by(annotator_id=session['annotator_id'])
    if model_name:
        query = query.filter_by(model_name=model_name)
    
    annotations = query.all()
    
    export_data = {
        'exported_at': datetime.utcnow().isoformat(),
        'annotator_id': session['annotator_id'],
        'annotator_name': session['annotator_name'],
        'annotator_email': session['annotator_email'],
        'model_filter': model_name if model_name else 'all',
        'total_annotations': len(annotations),
        'annotations': [ann.to_dict() for ann in annotations]
    }
    
    return jsonify(export_data)


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """404 error handler."""
    return render_template('error.html', error='Page not found'), 404


@app.errorhandler(500)
def internal_error(error):
    """500 error handler."""
    db.session.rollback()
    return render_template('error.html', error='Internal server error'), 500


# ============================================================================
# CLI COMMANDS
# ============================================================================

@app.cli.command()
def init_db():
    """Initialize the database."""
    db.create_all()
    load_annotators()
    print("Database initialized successfully!")


@app.cli.command()
def load_sample_data():
    """Load sample annotation data."""
    sample_file = Path(__file__).parent / 'data' / 'whisper_annotation_data.json'
    if sample_file.exists():
        with open(sample_file) as f:
            data = json.load(f)
        
        for item in data[:10]:  # Load first 10 for testing
            utterance = AnnotationData(
                utterance_id=item['utterance_id'],
                human_transcript=item['human_transcript'],
                asr_reconstructed=item['asr_reconstructed'],
                extra_data=item
            )
            db.session.add(utterance)
        
        db.session.commit()
        print("Sample data loaded!")
    else:
        print("No sample data file found")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
