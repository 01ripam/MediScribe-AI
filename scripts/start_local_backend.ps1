$ErrorActionPreference = 'Stop'

Set-Location "d:\mayday\patient-platform\backend"

if (Test-Path ".env.local") {
  Copy-Item ".env.local" ".env" -Force
}

$python = "d:\mayday\.venv\Scripts\python.exe"

& $python -m uvicorn app.main:app --app-dir "d:\mayday\patient-platform\backend" --host 0.0.0.0 --port 8000
