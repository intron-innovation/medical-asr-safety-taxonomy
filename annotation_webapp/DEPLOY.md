# Deploying the annotation webapp to PythonAnywhere

The live site runs on the PythonAnywhere `kelehenry` account. Deploy is a
`git pull` on the server plus a couple of one-time config steps. Audio is served
from a private Google Cloud Storage bucket via short-lived signed URLs, so the
2.7 GB of `.wav` files never need to live on PA's disk.

Repo root on PA: `/home/kelehenry/webapp_v5` (this app is the
`annotation_webapp/` subdirectory).

---

## 1. Pull the latest code

The tracked SQLite DB (`annotation_tool.db`) holds real annotator data and must
be preserved across pulls. Because the DB and (sometimes) `app.py` are tracked
and get modified on the server, a plain `git pull` will abort. Use this sequence:

```bash
cd ~/webapp_v5

# Back up the live DB (real annotator data)
cp annotation_webapp/annotation_tool.db annotation_webapp/annotation_tool.db.live_backup

# Discard ALL local tracked edits (staged + unstaged) so the pull can fast-forward.
# Untracked files (backups, the SA key, etc.) are NOT touched by this.
git reset --hard HEAD

git pull --ff-only origin main

# Restore the live DB over the repo's committed copy
cp annotation_webapp/annotation_tool.db.live_backup annotation_webapp/annotation_tool.db
```

Then reload the app (Web tab -> Reload).

Notes:
- `git checkout -- .` is NOT enough if there are *staged* local changes on the
  server; `git reset --hard` clears both staged and unstaged.
- New model data files (`data/annotation_data/*_annotation_data.json`) are loaded
  into the DB automatically on the first visit to `/select_model` — no manual
  import step.

---

## 2. Virtualenv and Python version MUST match (the #1 gotcha)

PythonAnywhere **silently ignores the virtualenv** if the web app's configured
Python version does not exactly match the virtualenv's Python version. When that
happens the app runs on system Python and any venv-only packages (like
`google-cloud-storage`) fail with `ModuleNotFoundError: No module named 'google'`.

- Web tab -> **Python version** must equal the virtualenv's `python --version`.
  Current setup: **3.13**, venv at `/home/kelehenry/.virtualenvs/webapp_v5-env`.
- To install/verify packages in the *exact* env the site runs, use the Web tab's
  **"Start a console in this virtualenv"** link (do not rely on `workon`, which can
  activate a same-named env elsewhere).

Install/refresh dependencies in that console:

```bash
python --version   # must match the Web tab Python version
pip install -r ~/webapp_v5/annotation_webapp/requirements.txt
python -c "import flask, flask_sqlalchemy; from google.cloud import storage; print('deps OK')"
```

If the Web tab shows a pink "virtualenv seems to have the wrong Python version"
warning, fix the version mismatch before doing anything else.

---

## 3. GCS audio configuration

Audio is served by `/api/audio` which, in GCS mode, redirects to a v4 signed URL.

**Environment variables** — set at the TOP of the WSGI file
(`/var/www/kelehenry_pythonanywhere_com_wsgi.py`), BEFORE the app/`config` import,
because `config.py` reads them at import time:

```python
import sys, os

os.environ["AUDIO_STORAGE"] = "gcs"
os.environ["GCS_BUCKET"] = "bio-ramp-ner-asr-audio-563398935287"
os.environ["GCS_PREFIX"] = "final_audio"
os.environ["GCS_SIGNED_URL_TTL"] = "900"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/home/kelehenry/.config/gcloud/bioramp-storage.json"
```

**Service-account key** — v4 signing from PA (which is not on GCP) requires a
service-account JSON key with **Storage Object Viewer** on the bucket:

- Create the key in GCP Console (IAM & Admin -> Service Accounts -> Keys ->
  Add key -> Create new key -> JSON).
- Upload it to PA via the **Files tab "Upload a file"** — do NOT paste the JSON
  into the editor. Pasting mangles the `private_key` and causes
  `invalid_grant: Invalid JWT Signature` (the key parses fine but won't sign).
- Never commit the key; it is gitignored / lives only on the PA disk.

`google-cloud-storage` is in `requirements.txt`; make sure it is installed in the
matching venv (step 2).

---

## 4. Verify

Run this in the web app's virtualenv console to test the whole audio chain:

```bash
python - <<'PY'
import os
from datetime import timedelta
import urllib.request
os.environ.setdefault("GOOGLE_APPLICATION_CREDENTIALS",
    "/home/kelehenry/.config/gcloud/bioramp-storage.json")
from google.cloud import storage
BUCKET = "bio-ramp-ner-asr-audio-563398935287"
OBJ = "final_audio/day5_consultation02_stereo.wav"
c = storage.Client()
print("Auth OK. project =", c.project)
b = c.bucket(BUCKET).blob(OBJ)
print("exists =", b.exists())
url = b.generate_signed_url(version="v4", expiration=timedelta(seconds=300), method="GET")
r = urllib.request.urlopen(urllib.request.Request(url, method="HEAD"))
print("GCS HEAD:", r.status, r.headers.get("Content-Type"), r.headers.get("Content-Length"))
PY
```

Expected: `Auth OK` -> `exists = True` -> `GCS HEAD: 200`.

In the browser (logged in), the endpoint should 302-redirect to
`storage.googleapis.com` and play:

```
https://kelehenry.pythonanywhere.com/api/audio?path=data/final_audio/day5_consultation02_stereo.wav
```

The Web tab **error log** is the first place to look if audio fails
(`app.logger.exception` records the traceback there).

### Failure quick-reference

| Symptom | Cause | Fix |
| --- | --- | --- |
| `No module named 'google'` | venv/Python version mismatch, or package not in the web app's venv | Match Web tab Python to the venv; `pip install` via "Start a console in this virtualenv" |
| `invalid_grant: Invalid JWT Signature` | SA key corrupted (pasted) or revoked | Regenerate key, upload as a file (not paste) |
| `blob.exists() = False` | object not at `final_audio/<name>` in the bucket | Upload the file / fix the path |
| `GCS HEAD: 403` | SA lacks bucket read | Grant **Storage Object Viewer** on the bucket |
| `git pull` aborts | staged/unstaged local edits on server | `git reset --hard HEAD` (after backing up the DB) |

---

## Notes

- `data/final_audio/*.wav` is gitignored on purpose (purged from history). Audio
  lives in GCS, never in the repo.
- Only sessions whose audio resolves are shown to annotators. In GCS mode every
  session is treated as available (`_has_audio_file` returns True when a bucket is
  configured).
- phi4/whisper reference a few older-named audio files; confirm those specific
  objects exist in the bucket or their audio will 404 while the newer models work.
