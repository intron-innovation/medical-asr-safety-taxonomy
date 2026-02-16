"""Database models for ASR Annotation Tool."""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSON

db = SQLAlchemy()


class Annotator(db.Model):
    """Pre-registered annotators."""
    __tablename__ = 'annotators'
    
    id = db.Column(db.Integer, primary_key=True)
    annotator_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=False, index=True)
    affiliation = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    annotations = db.relationship('Annotation', backref='annotator', lazy='dynamic')
    progress = db.relationship('AnnotationProgress', backref='annotator', uselist=False)
    
    def to_dict(self):
        return {
            'annotatorId': self.annotator_id,
            'name': self.name,
            'email': self.email,
            'affiliation': self.affiliation
        }


class AnnotationData(db.Model):
    """Utterances to be annotated."""
    __tablename__ = 'annotation_data'
    
    id = db.Column(db.Integer, primary_key=True)
    utterance_id = db.Column(db.String(200), nullable=False, index=True)
    model_name = db.Column(db.String(50), nullable=False, index=True)  # whisper, phi4, etc.
    human_transcript = db.Column(db.Text, nullable=False)
    asr_transcript = db.Column(db.Text, nullable=False)
    asr_reconstructed = db.Column(db.Text, nullable=False)
    extra_data = db.Column(JSON)  # Store additional fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Composite unique constraint: same utterance can exist for different models
    __table_args__ = (
        db.UniqueConstraint('utterance_id', 'model_name', name='uix_utterance_model'),
    )
    
    def to_dict(self):
        return {
            'utterance_id': self.utterance_id,
            'model_name': self.model_name,
            'human_transcript': self.human_transcript,
            'asr_transcript': self.asr_transcript,
            'asr_reconstructed': self.asr_reconstructed,
            'metadata': self.extra_data or {}
        }


class Annotation(db.Model):
    """Individual error annotations."""
    __tablename__ = 'annotations'
    
    id = db.Column(db.Integer, primary_key=True)
    error_id = db.Column(db.String(36), nullable=False, index=True)  # UUID: unique ID for each error occurrence
    annotator_id = db.Column(db.String(50), db.ForeignKey('annotators.annotator_id'), nullable=False, index=True)
    model_name = db.Column(db.String(50), nullable=False, index=True)  # whisper, phi4, etc.
    utterance_id = db.Column(db.String(200), nullable=False, index=True)
    error_type = db.Column(db.String(10), nullable=False)  # DEL, SUB, INS
    error_match = db.Column(db.String(500), nullable=False)
    taxonomy = db.Column(JSON, nullable=False)  # List of taxonomy categories
    severity = db.Column(db.Integer, nullable=False)  # 0-5
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Context information
    utterance_index = db.Column(db.Integer)
    human_transcript = db.Column(db.Text)
    asr_transcript = db.Column(db.Text)
    asr_reconstructed = db.Column(db.Text)
    
    # Unique constraint: one annotation per error instance per annotator
    # error_id allows multiple occurrences of the same word to be annotated separately
    __table_args__ = (
        db.UniqueConstraint('annotator_id', 'error_id', 
                           name='_annotator_error_instance_uc'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'errorId': self.error_id,
            'annotatorId': self.annotator_id,
            'modelName': self.model_name,
            'utteranceId': self.utterance_id,
            'errorType': self.error_type,
            'errorMatch': self.error_match,
            'taxonomy': self.taxonomy,
            'severity': self.severity,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'utteranceIndex': self.utterance_index,
            'context': {
                'humanTranscript': self.human_transcript,
                'asrTranscript': self.asr_transcript,
                'asrReconstructed': self.asr_reconstructed
            }
        }


class AnnotationProgress(db.Model):
    """Track annotation progress for each annotator per model."""
    __tablename__ = 'annotation_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    annotator_id = db.Column(db.String(50), db.ForeignKey('annotators.annotator_id'), 
                            nullable=False, index=True)
    model_name = db.Column(db.String(50), nullable=False, index=True)  # whisper, phi4, etc.
    current_utterance_index = db.Column(db.Integer, default=0)
    completed_utterances = db.Column(JSON, default=list)  # List of utterance_ids
    last_accessed = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Composite unique constraint: one progress record per annotator per model
    __table_args__ = (
        db.UniqueConstraint('annotator_id', 'model_name', name='uix_annotator_model_progress'),
    )
    
    def to_dict(self):
        return {
            'annotatorId': self.annotator_id,
            'modelName': self.model_name,
            'currentUtteranceIndex': self.current_utterance_index,
            'completedUtterances': self.completed_utterances or [],
            'lastAccessed': self.last_accessed.isoformat() if self.last_accessed else None
        }
