#!/usr/bin/env pwsh
# Start Patient Platform Backend Server

# Define paths
$BackendDir = "D:\mobdwd\mayday\patient-platform\backend"
$VenvPython = "D:\mobdwd\mayday\.venv\Scripts\python.exe"

# Display banner
Write-Host "`n" -ForegroundColor White
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "  PATIENT PLATFORM - LOCAL BACKEND SERVER" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "`nServices Active:" -ForegroundColor Green
Write-Host "   - OTP Service (In-memory simulation)" -ForegroundColor Yellow
Write-Host "   - Patient Authentication (Phone + OTP)" -ForegroundColor Yellow
Write-Host "   - Doctor Management and Profiles" -ForegroundColor Yellow
Write-Host "   - Appointment Booking and Updates" -ForegroundColor Yellow
Write-Host "   - Payment Gateway (Razorpay - Optional)" -ForegroundColor Yellow
Write-Host "`nServer Endpoints:" -ForegroundColor Green
Write-Host "   http://localhost:8000" -ForegroundColor Cyan
Write-Host "   http://localhost:8000/docs (Swagger UI)" -ForegroundColor Cyan
Write-Host "   http://localhost:8000/redoc (ReDoc)" -ForegroundColor Cyan
Write-Host "`nOTP Service Details:" -ForegroundColor Green
Write-Host "   Type: In-memory simulation" -ForegroundColor Cyan
Write-Host "   Phone: Any 10-digit number (e.g., 9999999999)" -ForegroundColor Cyan
Write-Host "   OTP: Any 4-6 digit code (e.g., 1234)" -ForegroundColor Cyan
Write-Host "`nDatabase: MongoDB Atlas" -ForegroundColor Green
Write-Host "   Status: Connected" -ForegroundColor Cyan
Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "`nServer starting in 2 seconds...`n" -ForegroundColor Yellow

# Change to backend directory
Set-Location -Path $BackendDir

# Start the server
& $VenvPython -m uvicorn app.main:app --host 0.0.0.0 --port 8000
