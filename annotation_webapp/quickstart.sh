#!/bin/bash
# Quick Start Script for ASR Annotation Webapp

set -e  # Exit on error

echo "============================================================"
echo "ASR Annotation Webapp - Quick Start"
echo "============================================================"
echo ""

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "Error: Please run this script from the annotation_webapp directory"
    exit 1
fi

# Step 1: Check Python
echo "[1/6] Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 not found"
    exit 1
fi
PYTHON_VERSION=$(python3 --version)
echo "✓ Found: $PYTHON_VERSION"
echo ""

# Step 2: Check/Install dependencies
echo "[2/6] Checking Flask installation..."
if python3 -c "import flask" 2>/dev/null; then
    echo "✓ Flask is installed"
else
    echo "⚠️  Flask not installed"
    echo "Installing Flask and dependencies..."
    
    # Try different methods
    if command -v pip3 &> /dev/null; then
        pip3 install Flask Flask-SQLAlchemy flask-cors Werkzeug
    elif command -v conda &> /dev/null; then
        conda install -y flask flask-sqlalchemy
        pip install flask-cors
    else
        echo "Error: Neither pip3 nor conda found. Please install Flask manually."
        exit 1
    fi
fi
echo ""

# Step 3: Setup data directory
echo "[3/6] Setting up data directory..."
mkdir -p data/annotation_data
echo "✓ Created data/annotation_data/"

# Check for existing annotation files
echo "Checking for annotation data files..."
FILE_COUNT=$(find data/annotation_data/ -name "*.json" 2>/dev/null | wc -l)
if [ "$FILE_COUNT" -eq 0 ]; then
    echo "⚠️  No annotation data files found in data/annotation_data/"
    echo ""
    echo "Please add your model JSON files to data/annotation_data/"
    echo "Format: {model_name}_annotation_data.json"
    echo ""
    echo "You can run: python3 setup_data.py"
    echo "Or manually copy files to: data/annotation_data/"
else
    echo "✓ Found $FILE_COUNT annotation data file(s)"
fi
echo ""

# Step 4: Check annotators file
echo "[4/6] Checking annotators configuration..."
if [ ! -f "data/annotators.json" ]; then
    echo "Creating sample annotators.json..."
    cat > data/annotators.json <<'EOF'
[
  {
    "name": "Test Annotator",
    "email": "test@example.com",
    "annotator_id": "TEST001"
  }
]
EOF
    echo "✓ Created data/annotators.json (please update with real annotators)"
else
    echo "✓ Found data/annotators.json"
fi
echo ""

# Step 5: Initialize database
echo "[5/6] Initializing database..."
if [ -f "data/annotation_tool.db" ]; then
    read -p "Database exists. Reset it? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        python3 init_db.py --reset
    else
        echo "Skipping database initialization"
    fi
else
    python3 init_db.py
fi
echo ""

# Step 6: Summary
echo "[6/6] Setup complete!"
echo "============================================================"
echo ""
echo "📁 Directory structure:"
echo "  ✓ data/annotation_data/     - Model JSON files"
echo "  ✓ data/annotators.json      - Annotator credentials"
echo "  ✓ data/annotation_tool.db   - SQLite database"
echo ""
echo "🚀 To start the application:"
echo "  python3 app.py"
echo ""
echo "🌐 Then visit:"
echo "  http://localhost:5000"
echo ""
echo "📋 Useful commands:"
echo "  python3 setup_data.py          - Interactive data setup"
echo "  python3 setup_data.py list     - List current data files"
echo "  python3 init_db.py --stats     - Show database statistics"
echo "  python3 init_db.py --reset     - Reset database (caution!)"
echo ""
echo "📖 Documentation:"
echo "  README_MULTI_MODEL.md          - Full documentation"
echo "  IMPLEMENTATION_SUMMARY.md      - Technical summary"
echo ""
echo "============================================================"
