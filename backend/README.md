# Backend (FastAPI)

## Stack
- FastAPI + SQLAlchemy + SQLite
- OTP simulation in-memory
- KYC uniqueness via `govt_id_hash`

## Architecture

- `app/models.py`: SQLAlchemy entities
- `app/schemas.py`: API contracts
- `app/routers/`: Endpoint modules
- `app/services/`: OTP, payments, symptom suggestion
- `app/seed.py`: Sample doctors and demo patient records

## Appointment State Machine

Allowed transitions:
- `REQUESTED -> APPROVED`
- `APPROVED -> CONFIRMED` (only via payment)
- `REQUESTED/APPROVED -> CANCELLED`

## Auth/KYC Flow

1. `POST /auth/login` with phone
2. `POST /auth/verify-otp` to create/fetch patient
3. `POST /auth/kyc` to verify identity

If another account already has same ID hash, KYC fails with `409`.

## Sample Curl

```bash
curl -X POST http://127.0.0.1:8000/auth/login -H "Content-Type: application/json" -d '{"phone":"9876543210"}'
```

```bash
curl -X POST http://127.0.0.1:8000/auth/verify-otp -H "Content-Type: application/json" -d '{"phone":"9876543210","otp":"123456"}'
```

```bash
curl -X POST http://127.0.0.1:8000/auth/kyc -H "Content-Type: application/json" -d '{"patient_id":2,"name":"Rahul","age":29,"gender":"Male","govt_id":"ABCDE1234F","govt_id_type":"PAN"}'
```
