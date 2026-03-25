# Deployment Guide (Patient + Doctor Shared Backend)

This setup gives you one shared production backend/database used by:
- Patient mobile app
- Doctor web app

## 1) Run Production Stack with Docker

From repository root:

```powershell
docker compose -f docker-compose.prod.yml up -d --build
```

API health check:

```powershell
python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/').read().decode())"
```

## 2) Use PostgreSQL in Production

`DATABASE_URL` is already set in [backend/.env.production.example](backend/.env.production.example).

For free cloud setup, use Render + Supabase and set:

- `DATABASE_URL=postgresql+psycopg://<user>:<pass>@<host>:5432/<db>`
- `SECRET_PEPPER=<strong-random-string>`
- `ALLOWED_ORIGINS=https://doctor.your-domain.com,https://patient.your-domain.com`

## 3) Connect Doctor Website

Doctor website should call this same backend base URL.

Core doctor-side calls:
- `GET /doctors`
- `GET /appointments?patient_id=...`
- `PATCH /appointments/{id}` with `{ "action": "approve" }`

This keeps doctor and patient data in one database.

## 4) Deploy Backend Publicly

Deploy using [render.yaml](render.yaml) as a free Render web service.
Expose HTTPS endpoint, for example:
- `https://patient-api.onrender.com`

## 5) Deploy Patient App for Wireless Anywhere Access

Build Flutter app with public API URL:

```powershell
flutter build apk --release --dart-define=API_BASE_URL=https://patient-api.onrender.com
```

For debug run:

```powershell
flutter run --dart-define=API_BASE_URL=https://patient-api.onrender.com
```

## 6) Important Production Notes

- Keep `DEV_MASTER_OTP` disabled or changed in production.
- Store secrets in cloud secret manager, not git.
- Use HTTPS only.
- Set strict `ALLOWED_ORIGINS`.
- Add proper auth (JWT/roles) before go-live.

See full free setup checklist in [FREE_ONLINE_SETUP.md](FREE_ONLINE_SETUP.md).
