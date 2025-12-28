#!/usr/bin/env python3
"""Quick verification script for the annotation webapp."""

import sys
from pathlib import Path

print("🔍 Verifying ASR Annotation Web Application Setup...\n")

# Check required files
required_files = [
    'app.py',
    'models.py',
    'config.py',
    'requirements.txt',
    'templates/base.html',
    'templates/index.html',
    'templates/login.html',
    'templates/instructions.html',
    'templates/annotate.html',
    'static/css/style.css',
    'static/js/annotate.js',
    'data/annotators.json'
]

missing_files = []
for file_path in required_files:
    if not Path(file_path).exists():
        missing_files.append(file_path)
        print(f"❌ Missing: {file_path}")
    else:
        print(f"✅ Found: {file_path}")

if missing_files:
    print(f"\n❌ {len(missing_files)} files are missing!")
    sys.exit(1)

print(f"\n✅ All {len(required_files)} required files are present!")

# Check if we can import the app
try:
    from app import app, db
    print("✅ Flask app imports successfully")
except Exception as e:
    print(f"❌ Error importing app: {e}")
    sys.exit(1)

# Check database
with app.app_context():
    from models import Annotator
    annotators = Annotator.query.all()
    print(f"✅ Database connected: {len(annotators)} annotators loaded")

# Print annotators
if annotators:
    print("\n👥 Pre-registered Annotators:")
    for ann in annotators:
        print(f"   • {ann.name} ({ann.email}) - ID: {ann.annotator_id}")

print("\n" + "="*60)
print("🎉 Setup verification complete!")
print("="*60)
print("\nTo start the server:")
print("  ./start.sh")
print("\nOr:")
print("  python app.py")
print("\nThen open: http://localhost:5000")
print("\n")
