$project = "C:\Users\Usuario\Proyects\personal-ai"

Write-Host "Iniciando Jarvis..." -ForegroundColor Cyan

# Backend
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd `"$project`"; python -m uvicorn backend.main:app --reload --port 8000"
)

Start-Sleep -Seconds 2

# Frontend
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd `"$project\frontend`"; npm run dev"
)

Start-Sleep -Seconds 3

# Abrir navegador
Start-Process "http://localhost:3000"

Write-Host "Jarvis iniciado." -ForegroundColor Green