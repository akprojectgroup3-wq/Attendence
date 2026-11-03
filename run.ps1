# AI & IoT Smart Classroom Attendance System - PowerShell Launcher
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  AI & IoT SMART CLASSROOM ATTENDANCE SYSTEM" -ForegroundColor Yellow
Write-Host "  Face Recognition (OpenCV LBPH) & IoT Architecture" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

Set-Location -Path $PSScriptRoot

if (Test-Path ".\venv\Scripts\python.exe") {
    Write-Host "[*] Activating virtual environment..." -ForegroundColor Green
    $pythonCmd = ".\venv\Scripts\python.exe"
} else {
    Write-Host "[!] Virtual environment not found. Using system Python..." -ForegroundColor Yellow
    $pythonCmd = "python"
}

Write-Host "[*] Launching Flask server on http://127.0.0.1:5000 ..." -ForegroundColor Cyan
Write-Host "[*] Default Admin Credentials: admin / admin123" -ForegroundColor Green

# Launch browser after 2 seconds
Start-Job -ScriptBlock {
    Start-Sleep -Seconds 2
    Start-Process "http://127.0.0.1:5000"
} | Out-Null

& $pythonCmd app.py
