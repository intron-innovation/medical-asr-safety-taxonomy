#!/bin/bash
# Startup script for ASR Annotation Web Application

cd "$(dirname "$0")"

echo "🚀 Starting ASR Annotation Web Application..."
echo "📍 Location: $(pwd)"
echo ""

# Check if database exists
if [ ! -f "annotation_tool.db" ]; then
    echo "📦 Initializing database..."
    /home/kelechi/miniconda3/bin/conda run -p /home/kelechi/miniconda3 python -c "from app import app, db; app.app_context().push(); db.create_all(); print('✅ Database created')"
fi

echo ""
echo "🌐 Starting Flask server..."
echo "📋 Access the application at: http://localhost:5000"
echo "🔐 Login with credentials from data/annotators.json"
echo ""
echo "Press Ctrl+C to stop the server"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Start the Flask application
/home/kelechi/miniconda3/bin/conda run -p /home/kelechi/miniconda3 python app.py
