# ASR Annotation Web Application

A Flask-based web application for annotating ASR (Automatic Speech Recognition) errors in medical conversations with server-side storage and multi-user support.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd annotation_webapp
pip install -r requirements.txt
```

### 2. Initialize Database

```bash
python app.py
# Or use Flask CLI:
flask init-db
```

The database will be created automatically at `annotation_tool.db` (SQLite) and pre-registered annotators will be loaded from `data/annotators.json`.

### 3. Run the Server

```bash
# Development mode
python app.py

# Production mode (with Gunicorn)
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

The application will be available at `http://localhost:5000`

## 📂 Project Structure

```
annotation_webapp/
├── app.py                      # Main Flask application
├── models.py                   # Database models (SQLAlchemy)
├── config.py                   # Configuration
├── requirements.txt            # Python dependencies
├── templates/                  # Jinja2 templates
│   ├── base.html              # Base template with navbar
│   ├── index.html             # Landing page
│   ├── login.html             # Login page
│   ├── instructions.html      # Annotation instructions
│   └── annotate.html          # Main annotation interface
├── static/                     # Static assets
│   ├── css/
│   │   └── style.css          # Main stylesheet
│   └── js/
│       └── annotate.js        # Annotation interface logic
├── data/                       # Data directory
│   ├── annotators.json        # Pre-registered users
│   └── *.json                 # Uploaded annotation data
└── annotation_tool.db         # SQLite database (created automatically)
```

## 🔐 Authentication

The system uses pre-registered annotators stored in `data/annotators.json`:

```json
{
  "annotators": [
    {
      "annotatorId": "ANN001",
      "name": "Dr. Sarah Johnson",
      "email": "sarah.johnson@example.com",
      "affiliation": "Stanford Medical Center"
    }
  ]
}
```

Users login with their **email** and **annotator ID**. Add more users by editing this JSON file and restarting the server.

## 📊 Database Schema

### Annotator
- `id`: Primary key
- `annotator_id`: Unique annotator ID (e.g., ANN001)
- `name`: Full name
- `email`: Email address (unique)
- `affiliation`: Organization/institution

### AnnotationData
- `id`: Primary key
- `utterance_id`: Unique utterance identifier
- `human_transcript`: Reference transcript
- `asr_reconstructed`: ASR output with error tags
- `metadata`: Additional fields (JSON)

### Annotation
- `id`: Primary key
- `annotator_id`: Foreign key to Annotator
- `utterance_id`: Foreign key to AnnotationData
- `error_type`: DEL, SUB, or INS
- `error_match`: The error pattern (e.g., [DEL:word])
- `taxonomy`: List of categories (JSON)
- `severity`: 0-5 severity score
- `timestamp`: Creation/update timestamp

### AnnotationProgress
- `id`: Primary key
- `annotator_id`: Foreign key to Annotator
- `current_utterance_index`: Resume position
- `completed_utterances`: List of completed IDs (JSON)
- `last_accessed`: Last activity timestamp

## 🎯 Workflow

1. **Login**: Users authenticate with email + annotator ID
2. **Upload Data**: Load JSON file with utterances to annotate
3. **Annotate**: Click errors, select taxonomy categories, rate severity
4. **Auto-Save**: Annotations save to database automatically
5. **Export**: Download annotations as JSON for analysis

## 🔄 API Endpoints

### GET /
Landing page

### GET/POST /login
User authentication

### GET /logout
Clear session

### GET /instructions
Annotation guide

### GET /annotate
Main annotation interface

### POST /api/load_data
Upload JSON data file

### GET /api/utterances
Get all utterances

### GET /api/utterance/<index>
Get specific utterance

### GET /api/annotations
Get current user's annotations

### POST /api/annotations
Save annotation (upsert)

### GET/POST /api/progress
Get or update annotation progress

### GET /api/stats
Get annotation statistics

### GET /api/export
Export annotations to JSON

## 🎨 Features

### Multi-User Support
- Each annotator has separate account and progress
- Server-side session management
- Independent annotation storage per user

### Real-Time Auto-Save
- Annotations saved to database immediately
- Progress tracked automatically
- Resume from exact position

### Rich Annotation Interface
- Color-coded error highlighting (DEL/SUB/INS)
- Click-to-annotate workflow
- 11-category taxonomy
- 0-5 severity scoring
- Live statistics

### Data Export
- JSON export for analysis
- Includes all annotation metadata
- Timestamped exports

## 🔧 Configuration

Edit `config.py` to customize:

```python
class Config:
    SECRET_KEY = 'your-secret-key-here'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///annotation_tool.db'
    # For PostgreSQL in production:
    # SQLALCHEMY_DATABASE_URI = 'postgresql://user:pass@host/db'
```

Environment variables:
- `FLASK_ENV`: `development` or `production`
- `SECRET_KEY`: Session encryption key
- `DATABASE_URL`: Database connection string

## 📦 Deployment

### Local Development
```bash
python app.py
```

### Production with Gunicorn
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Docker (Optional)
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

### Cloud Deployment

**Heroku:**
```bash
heroku create your-app-name
heroku addons:create heroku-postgresql:mini
git push heroku main
```

**Railway/Render:**
- Connect GitHub repository
- Set build command: `pip install -r requirements.txt`
- Set start command: `gunicorn app:app`

## 🔍 Data Format

Input JSON format (uploaded via interface):

```json
[
  {
    "utterance_id": "RES0001",
    "human_transcript": "Patient reports chest pain...",
    "asr_reconstructed": "Patient reports [SUB:chest pain->chess pain]..."
  }
]
```

## 🛠️ CLI Commands

```bash
# Initialize database
flask init-db

# Load sample data (first 10 utterances)
flask load-sample-data
```

## 📈 Analytics

Annotations include:
- Error type distribution
- Taxonomy category frequencies
- Severity ratings
- Per-annotator statistics
- Inter-annotator agreement (future feature)

## ⚠️ Important Notes

1. **Database Backups**: Regularly backup `annotation_tool.db`
2. **SECRET_KEY**: Change in production for security
3. **PostgreSQL**: Recommended for production (set DATABASE_URL)
4. **HTTPS**: Use reverse proxy (Nginx) with SSL in production
5. **Annotators**: Manage via `data/annotators.json`

## 🐛 Troubleshooting

**Database errors:**
```bash
# Reset database
rm annotation_tool.db
flask init-db
```

**Port already in use:**
```bash
# Change port
python app.py  # Edit app.run(port=5001)
```

**Annotators not loading:**
- Check `data/annotators.json` exists
- Verify JSON format is valid
- Restart server after changes

## 📝 License

Research use only. Medical speech recognition quality assessment.

## 👥 Contact

For access, contact your research administrator.
