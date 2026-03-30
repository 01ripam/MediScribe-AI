$BackendDir = "D:\mobdwd\mayday\patient-platform\backend"
$VenvPython = "D:\mobdwd\mayday\.venv\Scripts\python.exe"

Write-Host ""
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "  PATIENT PLATFORM - LOCAL BACKEND SERVER" -ForegroundColor Green
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "Services Active:" -ForegroundColor Green
Write-Host "   - OTP Service (In-memory simulation)" -ForegroundColor Yellow
Write-Host "   - Patient Authentication (Phone + OTP)" -ForegroundColor Yellow
Write-Host "   - Doctor Management"
Write-Host "   - Appointment Booking"
Write-Host ""
Write-Host "Server Endpoints:" -ForegroundColor Green
Write-Host "   http://localhost:8000" -ForegroundColor Cyan
Write-Host "   http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "OTP Testing:" -ForegroundColor Yellow
Write-Host "   Phone: Any 10-digit (9999999999)" -ForegroundColor Cyan
Write-Host "   OTP: Any 4-6 digits (1234)" -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host ""

Set-Location -Path $BackendDir
& $VenvPython -m uvicorn app.main:app --host 0.0.0.0 --port 8000
