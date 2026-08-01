"""Main Flask application for ASR Annotation Tool."""
import json
import os
from datetime import datetime
from pathlib import Path
from functools import wraps

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, send_file
from sqlalchemy.orm.attributes import flag_modified
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
            
            # Extract errors with unique IDs. human_transcript_ner (inline
            # [PROBLEM: ...]/[MEDICINE: ...]/etc tags) flags which errors are
            # medically relevant via is_medical - annotators are only required
            # to annotate those, not every trivial word-level diff.
            asr_text = item.get('asr_reconstructed', '')
            errors = ErrorExtractor.extract_errors(asr_text, item.get('human_transcript_ner'))
            
            # Store errors in extra_data
            item['errors'] = errors
            item['error_count'] = len(errors)
            
            utterance = AnnotationData(
                utterance_id=utterance_id,
                model_name=model_name,
                human_transcript=item.get('human_transcript', ''),
                asr_transcript=item.get('asr_transcript', ''),
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
    """Load pre-registered annotators from JSON file.

    The JSON file remains the source of truth for *bootstrapping* accounts
    (including granting admin rights via "isAdmin": true) but is only read at
    startup. New annotators added afterwards should be created via the Admin
    > Annotators page, which writes straight to the database.
    """
    annotators_file = app.config['ANNOTATORS_FILE']
    if not annotators_file.exists():
        return
    
    try:
        with open(annotators_file, 'r') as f:
            data = json.load(f)
            annotators_list = data.get('annotators', [])
        
        for ann_data in annotators_list:
            existing = Annotator.query.filter_by(annotator_id=ann_data['annotatorId']).first()
            is_admin_flag = bool(ann_data.get('isAdmin', False))
            if not existing:
                annotator = Annotator(
                    annotator_id=ann_data['annotatorId'],
                    name=ann_data['name'],
                    email=ann_data['email'],
                    affiliation=ann_data.get('affiliation'),
                    is_admin=is_admin_flag,
                    is_active=True
                )
                db.session.add(annotator)
            elif is_admin_flag and not existing.is_admin:
                # Seed file grants admin but the DB row predates the flag - promote it.
                existing.is_admin = True
        
        db.session.commit()
    except Exception as e:
        print(f"Error loading annotators: {e}")


def ensure_schema_upgrades(app):
    """Lightweight in-place migration for SQLite: add new columns if missing.

    Flask-SQLAlchemy's db.create_all() only creates missing tables, it will not
    alter a table that already exists. This adds any new columns introduced
    after the initial schema (e.g. Annotation.error_class) without requiring a
    full migration tool for local/sqlite deployments.
    """
    with app.app_context():
        if db.engine.dialect.name != 'sqlite':
            return
        with db.engine.connect() as conn:
            existing_cols = {row[1] for row in conn.execute(db.text("PRAGMA table_info(annotations)"))}
            if existing_cols and 'error_class' not in existing_cols:
                conn.execute(db.text("ALTER TABLE annotations ADD COLUMN error_class JSON"))
                conn.commit()
            
            annotator_cols = {row[1] for row in conn.execute(db.text("PRAGMA table_info(annotators)"))}
            if annotator_cols and 'is_admin' not in annotator_cols:
                conn.execute(db.text("ALTER TABLE annotators ADD COLUMN is_admin BOOLEAN DEFAULT 0"))
                conn.commit()
            if annotator_cols and 'is_active' not in annotator_cols:
                conn.execute(db.text("ALTER TABLE annotators ADD COLUMN is_active BOOLEAN DEFAULT 1"))
                conn.commit()


def create_app(config_name='development'):
    """Application factory."""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    
    # Create tables, apply lightweight schema upgrades, then load initial data.
    # Order matters: load_annotators() queries the new is_admin/is_active columns,
    # so the upgrade must run before it.
    with app.app_context():
        db.create_all()
    
    ensure_schema_upgrades(app)
    
    with app.app_context():
        load_annotators(app)
    
    return app


app = create_app(os.environ.get('APP_CONFIG', 'development'))


def login_required(f):
    """Decorator to require login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'annotator_id' not in session:
            flash('Please login first', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to require an admin session in addition to being logged in."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'annotator_id' not in session:
            flash('Please login first', 'error')
            return redirect(url_for('login'))
        if not session.get('is_admin'):
            flash('Admin access required', 'error')
            return redirect(url_for('select_model'))
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
        
        if annotator and not annotator.is_active:
            flash('This account has been disabled. Contact your research administrator.', 'error')
        elif annotator:
            session['annotator_id'] = annotator.annotator_id
            session['annotator_name'] = annotator.name
            session['annotator_email'] = annotator.email
            session['affiliation'] = annotator.affiliation
            session['is_admin'] = annotator.is_admin
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


# ============================================================================
# ADMIN
# ============================================================================

def compute_progress_overview():
    """Build a per-model, per-annotator progress summary for the admin dashboard.

    "Complete" for a session means every auto-detected error in it has an
    Annotation row from that annotator (mirrors the client-side completion
    gate in annotate.js).
    """
    models = get_available_models(app)
    annotators = Annotator.query.order_by(Annotator.name).all()
    overview = []
    
    for model in models:
        utterances = AnnotationData.query.filter_by(model_name=model['name']).order_by(AnnotationData.id).all()
        session_error_ids = {}
        total_errors = 0
        for utt in utterances:
            # Only medically-relevant errors are required/counted, matching the
            # client-side completion gate in annotate.js.
            error_ids = [
                e['error_id'] for e in (utt.extra_data or {}).get('errors', [])
                if e.get('is_medical')
            ]
            session_error_ids[utt.utterance_id] = error_ids
            total_errors += len(error_ids)
        
        model_row = {
            'name': model['name'],
            'display_name': model['display_name'],
            'total_sessions': len(utterances),
            'total_errors': total_errors,
            'annotators': []
        }
        
        for annotator in annotators:
            anns = Annotation.query.filter_by(
                annotator_id=annotator.annotator_id, model_name=model['name']
            ).all()
            annotated_error_ids = {a.error_id for a in anns}
            
            sessions_complete = 0
            for error_ids in session_error_ids.values():
                if all(eid in annotated_error_ids for eid in error_ids):
                    sessions_complete += 1
            
            unique_annotated = len(annotated_error_ids & {eid for ids in session_error_ids.values() for eid in ids})
            model_row['annotators'].append({
                'annotator_id': annotator.annotator_id,
                'name': annotator.name,
                'is_active': annotator.is_active,
                'total_annotations': len(anns),
                'sessions_complete': sessions_complete,
                'sessions_total': len(utterances),
                'progress_pct': round((unique_annotated / total_errors * 100) if total_errors else 0, 1)
            })
        
        overview.append(model_row)
    
    return overview


@app.route('/admin')
@admin_required
def admin_dashboard():
    """Admin overview: annotator counts + per-model/per-annotator progress."""
    overview = compute_progress_overview()
    return render_template(
        'admin_dashboard.html',
        overview=overview,
        total_annotators=Annotator.query.count(),
        active_annotators=Annotator.query.filter_by(is_active=True).count(),
        total_annotations=Annotation.query.count()
    )


@app.route('/admin/annotators', methods=['GET', 'POST'])
@admin_required
def admin_annotators():
    """List annotators, add new ones, and toggle active/admin status."""
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add':
            annotator_id = request.form.get('annotatorId', '').strip().upper()
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip().lower()
            affiliation = request.form.get('affiliation', '').strip()
            make_admin = request.form.get('isAdmin') == 'on'
            
            if not (annotator_id and name and email):
                flash('Annotator ID, name, and email are required', 'error')
            elif Annotator.query.filter_by(annotator_id=annotator_id).first():
                flash(f'Annotator ID {annotator_id} already exists', 'error')
            elif Annotator.query.filter_by(email=email).first():
                flash(f'Email {email} is already registered', 'error')
            else:
                annotator = Annotator(
                    annotator_id=annotator_id,
                    name=name,
                    email=email,
                    affiliation=affiliation or None,
                    is_admin=make_admin,
                    is_active=True
                )
                db.session.add(annotator)
                db.session.commit()
                flash(f'Annotator {annotator_id} ({name}) added and enabled', 'success')
        
        elif action == 'toggle_active':
            target = Annotator.query.filter_by(annotator_id=request.form.get('annotatorId')).first()
            if target:
                if target.annotator_id == session['annotator_id'] and target.is_active:
                    flash('You cannot disable your own account', 'error')
                else:
                    target.is_active = not target.is_active
                    db.session.commit()
                    flash(f"{target.name} is now {'enabled' if target.is_active else 'disabled'}", 'success')
        
        elif action == 'toggle_admin':
            target = Annotator.query.filter_by(annotator_id=request.form.get('annotatorId')).first()
            if target:
                if target.annotator_id == session['annotator_id']:
                    flash('You cannot change your own admin status', 'error')
                else:
                    target.is_admin = not target.is_admin
                    db.session.commit()
                    flash(f"Admin access {'granted to' if target.is_admin else 'revoked from'} {target.name}", 'success')
        
        return redirect(url_for('admin_annotators'))
    
    annotators = Annotator.query.order_by(Annotator.name).all()
    return render_template('admin_annotators.html', annotators=annotators)


@app.route('/admin/annotations')
@admin_required
def admin_annotations():
    """Browse/filter completed annotations across all annotators."""
    model_filter = request.args.get('model', '')
    annotator_filter = request.args.get('annotator', '')
    
    query = Annotation.query
    if model_filter:
        query = query.filter_by(model_name=model_filter)
    if annotator_filter:
        query = query.filter_by(annotator_id=annotator_filter)
    
    annotations = query.order_by(Annotation.timestamp.desc()).limit(500).all()
    
    return render_template(
        'admin_annotations.html',
        annotations=annotations,
        models=get_available_models(app),
        annotators=Annotator.query.order_by(Annotator.name).all(),
        model_filter=model_filter,
        annotator_filter=annotator_filter,
        truncated=query.count() > 500
    )


@app.route('/admin/export')
@admin_required
def admin_export():
    """Export annotations across all annotators (optionally filtered) as JSON."""
    model_filter = request.args.get('model')
    annotator_filter = request.args.get('annotator')
    
    query = Annotation.query
    if model_filter:
        query = query.filter_by(model_name=model_filter)
    if annotator_filter:
        query = query.filter_by(annotator_id=annotator_filter)
    
    annotations = query.all()
    
    return jsonify({
        'exported_at': datetime.utcnow().isoformat(),
        'exported_by': session['annotator_id'],
        'model_filter': model_filter or 'all',
        'annotator_filter': annotator_filter or 'all',
        'total_annotations': len(annotations),
        'annotations': [a.to_dict() for a in annotations]
    })


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


@app.route('/api/audio')
@login_required
def get_audio():
    """Serve a session audio file from within the configured audio base directory."""
    rel_path = request.args.get('path', '').strip()
    if not rel_path:
        return jsonify({'error': 'path is required'}), 400

    audio_base = app.config['AUDIO_BASE_DIR']
    requested = (audio_base / rel_path).resolve()

    # Prevent path traversal outside the audio base directory
    if not requested.is_relative_to(audio_base):
        return jsonify({'error': 'Invalid audio path'}), 403

    if not requested.is_file():
        return jsonify({'error': 'Audio file not found'}), 404

    return send_file(requested, mimetype='audio/wav', conditional=True)


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
                existing.error_class = data.get('errorClass', [])
                existing.severity = data['severity']
                existing.timestamp = datetime.utcnow()
                existing.human_transcript = data.get('humanTranscript')
                existing.human_transcript_ner = data.get('humanTranscriptNER')
                existing.asr_transcript = data.get('asrTranscript')
                existing.asr_reconstructed = data.get('asrReconstructed')
                existing.utterance_index = data.get('utteranceIndex')
                existing.start_idx = data.get('startIdx')
                existing.end_idx = data.get('endIdx')
                existing.source = data.get('source', 'auto')
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
                    error_class=data.get('errorClass', []),
                    severity=data['severity'],
                    utterance_index=data.get('utteranceIndex'),
                    human_transcript=data.get('humanTranscript'),
                    human_transcript_ner=data.get('humanTranscriptNER'),
                    asr_transcript=data.get('asrTranscript'),
                    asr_reconstructed=data.get('asrReconstructed'),
                    start_idx=data.get('startIdx'),
                    end_idx=data.get('endIdx'),
                    source=data.get('source', 'auto')
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
def backfill_medical_flags():
    """Add is_medical to already-loaded AnnotationData rows' error metadata.

    Needed because load_model_data() only computes errors (with is_medical)
    for newly-ingested utterances - existing rows keep whatever was stored at
    ingestion time. This updates extra_data['errors'] in place, preserving the
    original error_id/start_idx/etc for every error so previously-submitted
    Annotation rows (which reference error_id) are never orphaned; it only
    adds/refreshes the is_medical key.
    """
    updated_utterances = 0
    updated_errors = 0
    for utt in AnnotationData.query.all():
        extra_data = utt.extra_data or {}
        errors = extra_data.get('errors')
        if not errors:
            continue
        medical_vocab = ErrorExtractor.build_medical_vocab(extra_data.get('human_transcript_ner'))
        changed = False
        for error in errors:
            is_medical = ErrorExtractor._is_medical_error(
                error.get('error_type'), error.get('error_text', ''), medical_vocab
            )
            if error.get('is_medical') != is_medical:
                error['is_medical'] = is_medical
                changed = True
                updated_errors += 1
        if changed:
            extra_data['errors'] = errors
            utt.extra_data = extra_data
            flag_modified(utt, 'extra_data')
            db.session.add(utt)
            updated_utterances += 1
    db.session.commit()
    print(f"Backfilled is_medical on {updated_errors} error(s) across {updated_utterances} utterance(s).")


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
