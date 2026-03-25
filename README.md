# Patient Platform (Production-Oriented Scaffold)

This workspace contains:
- Flutter patient mobile app with Riverpod state management
- FastAPI backend with secure KYC hash enforcement and appointment state machine

## Monorepo Structure

- `backend/`: FastAPI APIs and SQLite persistence
- `frontend/`: Flutter mobile client

## Quick Start

### 1) Backend

```powershell
cd d:\mayday\patient-platform\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend URL: `http://127.0.0.1:8000`

### 2) Frontend

```powershell
cd d:\mayday\patient-platform\frontend
flutter pub get
flutter run
```

## Security Notes

- Government IDs are never stored raw.
- `govt_id_hash` is generated using SHA-256 + pepper in `backend/app/security.py`.
- Duplicate accounts are blocked by unique hash in `/auth/kyc`.

## Required Endpoint Coverage

Implemented:
- `POST /auth/login`
- `POST /auth/verify-otp`
- `POST /auth/kyc`
- `GET /doctors`
- `GET /doctors/{id}`
- `POST /appointments`
- `GET /appointments`
- `PATCH /appointments/{id}`
- `GET /records`
- `POST /records`

Extra:
- `POST /ai/symptom-suggestion`
