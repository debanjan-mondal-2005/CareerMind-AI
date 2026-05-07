# CareerMind AI - Parallel Runner (PowerShell)
# Starts both backend and frontend services in parallel

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "🎯 CareerMind AI - Parallel Runner" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 Services to start:" -ForegroundColor Yellow
Write-Host "   • Backend (FastAPI): http://localhost:8000" -ForegroundColor White
Write-Host "   • Frontend (Static): http://localhost:3000" -ForegroundColor White
Write-Host ""
Write-Host "💡 Access the application at: http://localhost:3000" -ForegroundColor Green
Write-Host ""
Write-Host "⚠️  Press Ctrl+C to stop all services" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Activate virtual environment
& .\venv\Scripts\Activate.ps1

$projectRoot = Get-Location

# Function to start backend
$backendJob = Start-Job -ScriptBlock {
    Set-Location "$using:projectRoot\backend"
    Write-Host "🚀 Starting Backend on http://localhost:8000" -ForegroundColor Green
    & python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
}

# Wait a moment for backend to start
Start-Sleep -Seconds 2

# Function to start frontend
$frontendJob = Start-Job -ScriptBlock {
    Set-Location "$using:projectRoot\frontend"
    Write-Host "🌐 Starting Frontend on http://localhost:3000" -ForegroundColor Green
    & python -m http.server 3000
}

Write-Host ""
Write-Host "✅ Both services are running!" -ForegroundColor Green
Write-Host "   Backend:  http://localhost:8000" -ForegroundColor Cyan
Write-Host "   Frontend: http://localhost:3000" -ForegroundColor Cyan
Write-Host ""

# Keep both jobs running
try {
    Receive-Job -Job @($backendJob, $frontendJob) -Wait -AutoRemoveJob
}
catch {
    Write-Host "Error occurred" -ForegroundColor Red
}
finally {
    Write-Host ""
    Write-Host "🛑 Shutting down services..." -ForegroundColor Yellow
    Stop-Job -Job @($backendJob, $frontendJob)
    Remove-Job -Job @($backendJob, $frontendJob)
    Write-Host "✅ All services stopped" -ForegroundColor Green
}
