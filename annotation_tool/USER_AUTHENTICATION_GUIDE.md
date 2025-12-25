# User Authentication & Session Management Guide

## Overview

Your annotation tool now features a complete authentication system with per-user session management. This guide explains how to use the system from login to annotation.

---

## System Architecture

### Pages Flow

```
index.html (Landing)
    ↓
login.html (Authentication)
    ↓
instructions.html (Guidelines)
    ↓
annotation_interface.html (Main Tool)
    ↓
logout → back to index.html
```

### Session Storage

The system uses browser storage APIs for session management:

- **sessionStorage**: Stores current logged-in user during browser session
  - Key: `currentUser`
  - Cleared when browser closes
  - Contains: `annotatorId`, `annotatorName`, `annotatorEmail`, `institution`

- **localStorage**: Stores persistent user data and annotations
  - Key: `session_{annotatorId}` (user profile)
  - Key: `annotations_{annotatorId}` (user's annotations)
  - Persists across browser sessions until manually cleared

---

## User Workflow

### 1. Landing Page (index.html)

- **Purpose**: Welcome screen introducing the annotation system
- **Features**:
  - System overview with key features highlighted
  - Quick statistics (11 categories, severity scale, etc.)
  - Navigation buttons: "Login & Begin", "View Instructions"

**Action**: Click "Login & Begin" to proceed to authentication

---

### 2. Login Page (login.html)

- **Purpose**: User authentication and session creation
- **Form Fields**:
  - Full Name (required)
  - Email (required, validated format)
  - Annotator ID (required, alphanumeric only)
  - Institution (optional)

- **Features**:
  - **New Session**: Fill form to create new annotator profile
  - **Resume Session**: Enter Annotator ID to load previous session
  - Form validation with error messages
  - Auto-dismissing success/error notifications

**Validation Rules**:
- Email: Must be valid format (contains @ and .)
- Annotator ID: Only alphanumeric characters (A-Z, 0-9, no spaces/symbols)
- At least one annotation must be entered

**Storage**:
- sessionStorage.currentUser: Set on successful login
- localStorage.session_{annotatorId}: Stores user profile permanently

**Action**: After successful login, you'll be redirected to instructions.html

---

### 3. Instructions Page (instructions.html)

- **Purpose**: Comprehensive guide to annotation process
- **Contents**:
  - Your logged-in annotator info (displayed at top)
  - Annotation workflow (9-step process)
  - Error types (DEL, SUB, INS) explained
  - Complete 11-category taxonomy with examples
  - Severity scoring guide (0-5 scale)
  - Interface guide and keyboard shortcuts
  - Best practices and tips
  - Frequently asked questions (FAQ)

- **Features**:
  - Table of contents with section links
  - Color-coded error types and severity levels
  - Multi-label taxonomy examples
  - Keyboard shortcuts reference

**Action**: Click "Start Annotating" button to open annotation interface

---

### 4. Annotation Interface (annotation_interface.html)

#### Authentication Check
- Automatically checks if user is logged in
- Redirects to login if no session found
- Displays logged-in user info in header

#### User Information Display
- Shows: Annotator Name | Email | Annotator ID
- Located in header section below title
- Accessible throughout annotation session

#### Loading Data
1. Click "Load JSON File" button
2. Select your JSON file with ASR errors
3. System loads utterances and displays statistics

#### Annotation Process
1. **Select Conversation**: Use dropdown to choose utterance
2. **Review Transcripts**: Compare human vs ASR output
3. **Identify Errors**: Color-coded in ASR text:
   - 🔴 Red = Deletion (DEL)
   - 🟡 Yellow = Substitution (SUB)
   - 🔵 Blue = Insertion (INS)
4. **Click Error**: Opens annotation modal
5. **Assign Categories**: Select all applicable taxonomy (can be multiple)
6. **Rate Severity**: Use slider (0-5 scale)
7. **Save Annotation**: Click "Save Annotation" button

#### Auto-Save Feature
- **Automatic**: Each annotation is automatically saved to localStorage
- **Per-User**: Stored under `annotations_{annotatorId}`
- **Persistent**: Survives browser restart if using same Annotator ID
- **Visual Feedback**: Status message shows "Annotation saved"

#### Viewing Progress
- **Statistics Cards**: Show total conversations, errors, annotated count, progress %
- **Error List**: Shows all errors with annotation status
  - 🟢 Green dot = Annotated
  - 🟠 Orange dot = Needs annotation
- **Summary Tab**: Charts showing annotation patterns
  - Error type distribution
  - Taxonomy usage
  - Severity distribution

#### Exporting Results
1. Click "💾 Export Annotations" button
2. JSON file downloads with:
   - Annotator info
   - All annotations with timestamps
   - Filename: `asr_annotations_{annotatorId}_{timestamp}.json`
3. File contains: error types, categories, severity scores

#### Logout
- Click "🚪 Logout" button (top right)
- Confirms before logging out
- Saves all annotations before clearing session
- Returns to index.html

---

## Data Format

### User Session Object (sessionStorage.currentUser)

```json
{
  "annotatorId": "ANN001",
  "annotatorName": "John Smith",
  "annotatorEmail": "john@example.com",
  "institution": "Medical Center",
  "createdAt": "2025-12-24T10:30:00Z",
  "updatedAt": "2025-12-24T10:35:00Z"
}
```

### Annotations Storage (localStorage.annotations_{annotatorId})

```json
{
  "0_DEL_[DEL:medication]": {
    "taxonomy": ["Medication", "Numerics"],
    "severity": 4,
    "timestamp": "2025-12-24T10:35:00Z",
    "annotatorId": "ANN001"
  },
  "0_SUB_[SUB:diabetic~diabetic]": {
    "taxonomy": ["Clinical Concepts"],
    "severity": 2,
    "timestamp": "2025-12-24T10:36:00Z",
    "annotatorId": "ANN001"
  }
}
```

### Exported File Format

```json
{
  "exported_at": "2025-12-24T10:40:00Z",
  "annotator_id": "ANN001",
  "annotator_name": "John Smith",
  "annotator_email": "john@example.com",
  "total_annotations": 145,
  "annotations": {
    "0": [
      {
        "utterance_id": "CONV_001_UTT_001",
        "error_type": "DEL",
        "error_match": "[DEL:medication]",
        "taxonomy": ["Medication", "Numerics"],
        "severity": 4,
        "timestamp": "2025-12-24T10:35:00Z",
        "annotatorId": "ANN001"
      }
    ]
  }
}
```

---

## Resuming Previous Work

### Method 1: Same Browser Session
- If browser is still open from previous session
- Session data persists in sessionStorage
- Click "Start Annotating" on instructions page
- Your previous annotations automatically load

### Method 2: New Browser Session
1. Open index.html (or login.html)
2. On login page, enter your **Annotator ID**
3. Click "Load Previous Session" option
4. System loads your profile and all previous annotations
5. Continue annotating where you left off

### Method 3: Between Different Browsers/Devices
- Export your annotations (JSON file)
- Load the JSON file on new browser/device
- Your annotations are available for export on new machine
- Note: Session storage won't transfer (need to login again)

---

## Session Storage FAQ

### Q: Will my annotations be saved if I close the browser?
**A**: Yes! Annotations are saved in localStorage, which persists even after closing the browser.

### Q: What happens if I clear browser data?
**A**: localStorage will be cleared, so previous annotations will be lost. **Export your annotations regularly** to backup!

### Q: Can I use different annotators on same computer?
**A**: Yes! Each annotator has a unique ID. Login with different IDs to keep separate annotation sets.

### Q: What if I forget my Annotator ID?
**A**: You'll need to create a new session with a new ID. Your old annotations won't be accessible unless you saved/exported them.

### Q: Can I edit an annotation after saving?
**A**: Yes! Click the error again in the annotation interface to modify the annotation. Changes are auto-saved.

### Q: How do I backup my work?
**A**: Click "💾 Export Annotations" regularly to download a JSON file. Keep these files as backup.

---

## Tips & Best Practices

1. **Save Frequently**: Export your annotations every 30-50 errors to ensure backup
2. **Use Consistent IDs**: Use the same Annotator ID when resuming work
3. **Check Progress**: Monitor the progress % and error count in statistics
4. **Review Summary**: Use Summary tab periodically to check annotation patterns
5. **Read Instructions**: Refer back to instructions.html if unsure about categories
6. **Take Breaks**: Annotate for ~1 hour, then break to avoid fatigue
7. **Stay Consistent**: Be consistent in severity scoring across annotations
8. **Use Multiple Categories**: Don't limit errors to single category—select all that apply

---

## Troubleshooting

### Page redirects to login automatically
- **Cause**: No active session (browser was closed)
- **Solution**: Login again with your Annotator ID

### Can't find previous annotations
- **Cause**: Logged in with different Annotator ID
- **Solution**: Login with correct Annotator ID to resume

### Export file contains old annotations
- **Cause**: System exports all stored annotations
- **Solution**: This is correct—exported file should contain all your work

### Form validation error on login
- **Cause**: Email format invalid or Annotator ID contains special characters
- **Solution**: Use valid email (with @) and alphanumeric ID only (A-Z, 0-9)

### Annotations not saving
- **Cause**: Browser storage may be full or disabled
- **Solution**: Clear some localStorage or enable private storage

---

## Security Note

This is a **client-side only** system:
- No data is sent to any server
- All data stored locally in browser
- Annotator credentials not transmitted
- Export JSON files for backup/sharing

For sensitive data, ensure:
- Computer is secure and password-protected
- Don't share exported JSON files on unsecured networks
- Use unique, memorable Annotator IDs
- Export files regularly for backup

---

## Next Steps

1. ✅ Understand the authentication flow (this guide)
2. ✅ Open index.html to start
3. ✅ Create new account or resume with existing ID
4. ✅ Read instructions.html thoroughly
5. ✅ Start annotating on annotation_interface.html
6. ✅ Export annotations regularly for backup
7. ✅ Use process_annotations.py to analyze results (optional)

---

## Quick Reference

| Page | Purpose | Actions |
|------|---------|---------|
| index.html | Landing | Login, View Instructions |
| login.html | Authentication | Create/Resume Session |
| instructions.html | Guidelines | Read Guide, Start Annotating |
| annotation_interface.html | Annotation | Load Data, Annotate, Export |

---

**Version**: 2.0  
**Last Updated**: December 2024  
**Author**: ASR Annotation System
