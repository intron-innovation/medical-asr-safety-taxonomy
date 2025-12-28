#!/usr/bin/env python3
"""
Initialize or reset the database with the new multi-model schema.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app import app, db
from models import Annotator, AnnotationData, Annotation, AnnotationProgress
import json

def init_database(reset=False):
    """Initialize the database."""
    with app.app_context():
        if reset:
            print("⚠️  Dropping all tables...")
            db.drop_all()
            print("✓ Tables dropped")
        
        print("Creating tables...")
        db.create_all()
        print("✓ Tables created")
        
        # Load annotators
        annotators_file = Path(__file__).parent / 'data' / 'annotators.json'
        if annotators_file.exists():
            with open(annotators_file) as f:
                annotators_data = json.load(f)
            
            for ann_data in annotators_data:
                existing = Annotator.query.filter_by(email=ann_data['email']).first()
                if not existing:
                    annotator = Annotator(
                        name=ann_data['name'],
                        email=ann_data['email'],
                        annotator_id=ann_data['annotator_id']
                    )
                    db.session.add(annotator)
            
            db.session.commit()
            print(f"✓ Loaded {len(annotators_data)} annotators")
        else:
            print("⚠️  No annotators.json file found")
        
        print("\n✓ Database initialization complete!")
        print(f"  Database location: {app.config['SQLALCHEMY_DATABASE_URI']}")

def show_stats():
    """Show database statistics."""
    with app.app_context():
        annotators = Annotator.query.count()
        utterances = AnnotationData.query.count()
        annotations = Annotation.query.count()
        progress = AnnotationProgress.query.count()
        
        print("\nDatabase Statistics:")
        print("=" * 40)
        print(f"Annotators:       {annotators}")
        print(f"Utterances:       {utterances}")
        print(f"Annotations:      {annotations}")
        print(f"Progress records: {progress}")
        
        if utterances > 0:
            print("\nUtterances by model:")
            from sqlalchemy import func
            models = db.session.query(
                AnnotationData.model_name,
                func.count(AnnotationData.id)
            ).group_by(AnnotationData.model_name).all()
            
            for model, count in models:
                print(f"  • {model}: {count}")
        
        if annotations > 0:
            print("\nAnnotations by model:")
            models = db.session.query(
                Annotation.model_name,
                func.count(Annotation.id)
            ).group_by(Annotation.model_name).all()
            
            for model, count in models:
                print(f"  • {model}: {count}")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Initialize annotation database')
    parser.add_argument('--reset', action='store_true', 
                       help='Reset database (WARNING: deletes all data)')
    parser.add_argument('--stats', action='store_true',
                       help='Show database statistics')
    
    args = parser.parse_args()
    
    if args.stats:
        show_stats()
    else:
        if args.reset:
            response = input("⚠️  This will DELETE ALL DATA. Continue? (yes/no): ")
            if response.lower() != 'yes':
                print("Cancelled.")
                sys.exit(0)
        
        init_database(reset=args.reset)
        
        if not args.reset:
            show_stats()
