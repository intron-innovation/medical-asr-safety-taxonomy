# 🎉 ASR Annotation Web Application - Setup Complete!

Your annotation tool has been successfully converted to a full Flask web application!

## 📂 Location
```
/home/kelechi/bio_ramp_asr/annotation_webapp/
```

## 🚀 Quick Start

### Option 1: Using the startup script
```bash
cd /home/kelechi/bio_ramp_asr/annotation_webapp
./start.sh
```

### Option 2: Manual start
```bash
cd /home/kelechi/bio_ramp_asr/annotation_webapp
python app.py
```

Then open your browser to: **http://localhost:5000**

## 🔐 Login Credentials

Use any of these pre-registered annotators:

| Email | Annotator ID | Name |
|-------|--------------|------|
| sarah.johnson@example.com | ANN001 | Dr. Sarah Johnson |
| michael.chen@example.com | ANN002 | Dr. Michael Chen |
| emily.rodriguez@example.com | ANN003 | Emily Rodriguez |
| james.williams@example.com | ANN004 | Dr. James Williams |
| lisa.anderson@example.com | ANN005 | Lisa Anderson |

**To add more annotators:** Edit `data/annotators.json` and restart the server.

## 📊 What's New

### ✅ Server-Side Features
- **Database Storage**: SQLite database (`annotation_tool.db`) stores all data
- **Multi-User Support**: Each annotator has separate account and progress
- **Session Management**: Server-side authentication with Flask sessions
- **Auto-Save**: Annotations persist immediately to database
- **Progress Tracking**: Resume from exact position across sessions
- **RESTful API**: Clean API endpoints for all operations

### ✅ Enhanced UI
- **Modern Design**: Professional responsive interface
- **Navigation Bar**: Consistent navbar across all pages
- **Flash Messages**: Real-time feedback for user actions
- **Statistics Dashboard**: Live annotation progress tracking
- **Error Highlighting**: Color-coded DEL/SUB/INS errors

### ✅ Data Management
- **Upload JSON**: Load annotation data via web interface
- **Export Annotations**: Download your work as JSON
- **Database Backup**: Single file backup (`annotation_tool.db`)

## 📁 Project Structure

```
annotation_webapp/
├── app.py                      # Main Flask application
├── models.py                   # Database models
├── config.py                   # Configuration
├── requirements.txt            # Python dependencies
├── README.md                   # Full documentation
├── start.sh                    # Startup script
├── annotation_tool.db          # SQLite database (auto-created)
├── templates/
│   ├── base.html              # Base template with navbar
│   ├── index.html             # Landing page
│   ├── login.html             # Login page
│   ├── instructions.html      # Annotation guide
│   └── annotate.html          # Main annotation interface
├── static/
│   ├── css/
│   │   └── style.css          # Main stylesheet (650+ lines)
│   └── js/
│       └── annotate.js        # Annotation logic (350+ lines)
└── data/
    └── annotators.json        # Pre-registered users
```

## 🎯 Workflow

1. **Start Server**: Run `./start.sh` or `python app.py`
2. **Open Browser**: Navigate to http://localhost:5000
3. **Login**: Use email + annotator ID from table above
4. **Upload Data**: Load your JSON file with utterances
5. **Annotate**: Click errors, select categories, rate severity
6. **Auto-Save**: Work is saved to database automatically
7. **Export**: Download annotations when ready

## 🔄 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Landing page |
| `/login` | GET, POST | Authentication |
| `/logout` | GET | Clear session |
| `/instructions` | GET | Annotation guide |
| `/annotate` | GET | Main interface |
| `/api/load_data` | POST | Upload JSON file |
| `/api/utterances` | GET | Get all utterances |
| `/api/annotations` | GET, POST | Get/save annotations |
| `/api/progress` | GET, POST | Get/update progress |
| `/api/stats` | GET | Annotation statistics |
| `/api/export` | GET | Export to JSON |

## 📦 Database Schema

### Tables Created:
1. **annotators** - Pre-registered users
2. **annotation_data** - Utterances to annotate
3. **annotations** - Error annotations (with taxonomy & severity)
4. **annotation_progress** - Per-user progress tracking

## 🎨 Features Highlight

### Authentication
- Pre-registered annotator system
- Server-side session management
- Secure login with email + ID validation
- Session persistence (24 hours)

### Annotation Interface
- Click-to-annotate workflow
- 11-category taxonomy (Medical, Medication, Numerics, etc.)
- 0-5 severity scoring with visual slider
- Color-coded error types (DEL/SUB/INS)
- Status indicators (annotated vs. unannotated)

### Progress Tracking
- Current utterance index saved
- Completed utterances list
- Resume from exact position
- Last accessed timestamp

### Data Export
- JSON format export
- Includes all metadata
- Timestamped exports
- Per-annotator isolation

## 🔧 Configuration

### Development Mode (Current)
- Debug mode enabled
- SQLite database
- Auto-reload on code changes

### Production Deployment
Edit `config.py` to use PostgreSQL:
```python
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
SECRET_KEY = 'your-secure-secret-key'
DEBUG = False
```

### Cloud Deployment Options
- **Heroku**: `heroku create && git push heroku main`
- **Railway**: Connect GitHub repo
- **Render**: Deploy from GitHub
- **University Server**: Use Gunicorn + Nginx

## 📈 Next Steps

### Immediate:
1. Start the server with `./start.sh`
2. Test login with sample credentials
3. Upload your annotation JSON file
4. Begin annotating errors

### Optional Enhancements:
- Add admin dashboard for monitoring all annotators
- Implement inter-annotator agreement calculations
- Add quality control features (flag difficult cases)
- Export to Excel format
- Add annotation comments field
- Implement real-time collaboration

## 🐛 Troubleshooting

### Server won't start:
```bash
# Check if port 5000 is in use
lsof -i :5000

# Try different port
# Edit app.py: app.run(port=5001)
```

### Database errors:
```bash
# Reset database
rm annotation_tool.db
python app.py  # Will recreate automatically
```

### Can't login:
- Verify `data/annotators.json` exists
- Check email is lowercase in JSON
- Annotator ID is case-insensitive (ANN001 = ann001)

### Upload not working:
- Check file is valid JSON
- Ensure JSON has `utterance_id`, `human_transcript`, `asr_reconstructed`
- File size limit is 50MB

## 📝 Key Files Summary

| File | Lines | Purpose |
|------|-------|---------|
| app.py | 350+ | Main application, routes, API |
| models.py | 120+ | Database models |
| style.css | 650+ | Complete styling |
| annotate.js | 350+ | Annotation interface logic |
| README.md | 400+ | Full documentation |

## 🎉 Success!

Your annotation tool is now a production-ready web application with:
- ✅ Database persistence
- ✅ Multi-user support
- ✅ Professional UI
- ✅ RESTful API
- ✅ Session management
- ✅ Progress tracking
- ✅ Auto-save functionality

**Ready to deploy to production or use locally!**

## 📞 Support

For issues or questions:
1. Check README.md for detailed documentation
2. Review API endpoints in app.py
3. Inspect browser console for JavaScript errors
4. Check Flask logs in terminal

---
**Created**: December 26, 2025
**Version**: 1.0.0
**Framework**: Flask 3.0 + SQLAlchemy
