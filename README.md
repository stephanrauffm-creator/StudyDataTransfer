# Study Data Transfer

Internal Django web application for pseudonymized study data entry, protected document access, and Excel export to a network folder.

## Features

- Authenticated access for all study pages.
- Study entry model with audit metadata (`created_by`, `updated_by`, timestamps).
- Searchable list and edit restrictions (staff or original creator).
- Protected PDF instruction repository with staff-only uploads.
- Export endpoint generating XLSX from database truth.
- Atomic write and advisory lock for network-folder export files.
- Audit trail persisted in `AuditEvent` table and `LOG_DIR/audit.log`.

## Local setup (Linux/macOS)

1. Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Prepare instance config:

```bash
mkdir -p instance
cp instance/config.template.json instance/config.json
```

4. Adjust `instance/config.json` for your local paths.

5. Run migrations and create admin user:

```bash
python manage.py migrate
python manage.py createsuperuser
```

6. Start local server:

```bash
python manage.py runserver
```

Open: `http://127.0.0.1:8000/login`

## Windows test guide (Python 3.12)

Use these commands in **PowerShell** from the repository root.

1. Confirm Python 3.12 is available:

```powershell
py -3.12 --version
```

2. Create and activate a virtual environment:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. Install dependencies and verify Python version inside the venv:

```powershell
python --version
python -m pip install --upgrade pip
pip install -r requirements.txt
```

4. Create local config from template:

```powershell
Copy-Item .\instance\config.template.json .\instance\config.json
```

5. Edit `instance\config.json` for Windows paths (example):

```json
{
  "SECRET_KEY": "replace-with-long-random-secret",
  "DEBUG": true,
  "ALLOWED_HOSTS": ["127.0.0.1", "localhost"],
  "DATA_XLSX_PATH": "C:/StudyDataTransfer/instance/study_export.xlsx",
  "MEDIA_ROOT": "C:/StudyDataTransfer/media",
  "LOG_DIR": "C:/StudyDataTransfer/logs",
  "DATABASE_URL": ""
}
```

6. Run database setup and tests:

```powershell
python manage.py migrate
python manage.py createsuperuser
python manage.py test
python -m compileall .
```

7. Start the app:

```powershell
python manage.py runserver
```

Open: `http://127.0.0.1:8000/login`

### Common Windows terminal notes

- If PowerShell blocks activation scripts, run once as current user:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

- If `py` is not found, install Python 3.12 from python.org and enable "Add python.exe to PATH".
- Use forward slashes (`C:/path/to/file`) in JSON config to avoid escaping issues.

## Configuration (`instance/config.json`)

The app loads config in this order:
1. `instance/config.json`
2. environment variables (and optional `instance/.env`)
3. safe local defaults

Supported keys:

- `SECRET_KEY`
- `DEBUG`
- `ALLOWED_HOSTS`
- `DATA_XLSX_PATH`
- `MEDIA_ROOT`
- `LOG_DIR`
- `DATABASE_URL` (optional PostgreSQL URL)

Example:

```json
{
  "SECRET_KEY": "replace-with-long-random-secret",
  "DEBUG": false,
  "ALLOWED_HOSTS": ["study.internal.example"],
  "DATA_XLSX_PATH": "/nfs/norasys/notebooks/raust/xxxx/study_export.xlsx",
  "MEDIA_ROOT": "/nfs/norasys/notebooks/raust/xxxx/media",
  "LOG_DIR": "/nfs/norasys/notebooks/raust/xxxx/logs",
  "DATABASE_URL": ""
}
```

## Server run example (gunicorn)

```bash
gunicorn studydata.wsgi:application --bind 0.0.0.0:8000 --workers 3
```

### Example systemd unit

Save as `studydata.service` (paths must match your deployment):

```ini
[Unit]
Description=Study Data Transfer Django app
After=network.target

[Service]
Type=simple
WorkingDirectory=/nfs/norasys/notebooks/raust/xxxx
ExecStart=/nfs/norasys/notebooks/raust/xxxx/.venv/bin/gunicorn studydata.wsgi:application --bind 0.0.0.0:8000 --workers 3
Restart=on-failure
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

## Network share and locking notes

- `DATA_XLSX_PATH` should point to the final network file location.
- Export writes to a temp file in the same directory, then atomically renames.
- Advisory file lock (`.lock`) blocks concurrent exports.
- If lock acquisition fails, users get a friendly error and no file corruption occurs.

## Backup and retention recommendations

- Back up SQLite/PostgreSQL database regularly.
- Back up `MEDIA_ROOT/instructions` and `LOG_DIR`.
- Keep periodic snapshots of exported XLSX if required by policy.
- Align retention with institutional and study governance requirements.

## Deployment updater keep-files

Ensure the updater preserves these files/directories:

- `instance/config.json`
- `instance/.env` (optional)
- `db.sqlite3` (if using SQLite in production)
- `media/`
- `logs/`

## Privacy

Only pseudonymized patient identifiers (PIZ) are stored. Do not enter direct identifiers.
