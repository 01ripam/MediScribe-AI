# Free Online Setup (Doctor Website + Patient App)

This guide uses free tools only:
- Render (free web service) for backend API
- Supabase (free PostgreSQL) for database
- Firebase Hosting or Netlify free tier for doctor website

## Step 1: Create Free Supabase Postgres

1. Create a new project in Supabase.
2. Open Project Settings -> Database.
3. Copy the connection string.
4. Convert to SQLAlchemy format if needed:
   - `postgresql://...` -> `postgresql+psycopg://...`

## Step 2: Deploy Backend Free on Render

1. Push this repo to GitHub.
2. In Render, create a new Blueprint or Web Service from repo.
3. Render will detect [render.yaml](render.yaml).
4. Set environment values:
   - `DATABASE_URL` = your Supabase URL
   - `SECRET_PEPPER` = strong random string
   - `ALLOWED_ORIGINS` = doctor and patient app origins
   - `DEV_MASTER_OTP` = empty for production
5. Deploy and copy URL, e.g. `https://patient-api.onrender.com`.

## Step 3: Connect Doctor Website

Point doctor website API base URL to Render URL.
All doctor actions and patient app actions share one database.

## Step 4: Build Patient App for Internet Use

From [patient-platform/frontend](patient-platform/frontend):

```powershell
flutter build apk --release --dart-define=API_BASE_URL=https://patient-api.onrender.com
```

Install that APK on phone. It will work from anywhere with internet.

## Step 5: Verify Data Is Persisted

1. Login as patient and complete KYC.
2. In Supabase SQL editor run:

```sql
select id, phone, kyc_verified, govt_id_hash from patients order by id desc;
```

You should see saved patient records.

## Notes

- Free tiers may sleep when idle.
- First request after sleep can be slow.
- For production SLA, move to paid plan later.
