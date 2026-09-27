$root = "C:\Users\Usuario\Proyects\jarvis"

$backend = Join-Path $root "personal-ai"
$frontend = Join-Path $root "frontend"

# --------------------------------------------------
# MODO DEBUG
# --------------------------------------------------
#
# $true  = mostrar terminales
# $false = ejecutar todo oculto
#
$debug = $false


Write-Host "Iniciando Jarvis..." -ForegroundColor Cyan


# --------------------------------------------------
# VERIFICAR RUTAS
# --------------------------------------------------

if (!(Test-Path $backend)) {
    Write-Host "No existe el backend: $backend" -ForegroundColor Red
    exit 1
}

if (!(Test-Path $frontend)) {
    Write-Host "No existe el frontend: $frontend" -ForegroundColor Red
    exit 1
}

if (!(Test-Path (Join-Path $frontend "package.json"))) {
    Write-Host "No encontre package.json en: $frontend" -ForegroundColor Red
    exit 1
}


# --------------------------------------------------
# BACKEND
# --------------------------------------------------

Write-Host "Iniciando backend..." -ForegroundColor Yellow

if ($debug) {

    Start-Process powershell `
        -WorkingDirectory $backend `
        -ArgumentList @(
            "-NoExit",
            "-Command",
            "python -m uvicorn backend.main:app --reload --port 8000"
        )

}
else {

    Start-Process powershell `
        -WindowStyle Hidden `
        -WorkingDirectory $backend `
        -ArgumentList @(
            "-NoProfile",
            "-Command",
            "python -m uvicorn backend.main:app --reload --port 8000"
        )
}


# --------------------------------------------------
# ESPERAR BACKEND
# --------------------------------------------------

Write-Host "Esperando backend..." -ForegroundColor Yellow

$backendReady = $false
$maxAttempts = 60

for ($i = 1; $i -le $maxAttempts; $i++) {

    try {

        $response = Invoke-WebRequest `
            -Uri "http://127.0.0.1:8000/health" `
            -UseBasicParsing `
            -TimeoutSec 1 `
            -ErrorAction Stop

        if ($response.StatusCode -eq 200) {
            $backendReady = $true
            break
        }

    }
    catch {

        Write-Host "Backend cargando... ($i/$maxAttempts)"

        Start-Sleep -Seconds 1
    }
}


if (!$backendReady) {

    Write-Host "El backend no pudo iniciar." -ForegroundColor Red

    exit 1
}


Write-Host "Backend listo." -ForegroundColor Green


# --------------------------------------------------
# FRONTEND
# --------------------------------------------------

Write-Host "Iniciando frontend..." -ForegroundColor Yellow

if ($debug) {

    Start-Process powershell `
        -WorkingDirectory $frontend `
        -ArgumentList @(
            "-NoExit",
            "-Command",
            "npm run dev"
        )

}
else {

    Start-Process powershell `
        -WindowStyle Hidden `
        -WorkingDirectory $frontend `
        -ArgumentList @(
            "-NoProfile",
            "-Command",
            "npm run dev"
        )
}


# --------------------------------------------------
# ESPERAR FRONTEND
# --------------------------------------------------

Write-Host "Esperando frontend..." -ForegroundColor Yellow

$frontendReady = $false
$maxAttempts = 30

for ($i = 1; $i -le $maxAttempts; $i++) {

    try {

        $response = Invoke-WebRequest `
            -Uri "http://localhost:3000" `
            -UseBasicParsing `
            -TimeoutSec 1 `
            -ErrorAction Stop

        if ($response.StatusCode -eq 200) {
            $frontendReady = $true
            break
        }

    }
    catch {

        Write-Host "Frontend cargando... ($i/$maxAttempts)"

        Start-Sleep -Seconds 1
    }
}


# --------------------------------------------------
# ABRIR JARVIS
# --------------------------------------------------

if ($frontendReady) {

    Write-Host "Frontend listo." -ForegroundColor Green

    Start-Process "http://localhost:3000"

}
else {

    Write-Host "El frontend tardo demasiado en iniciar." -ForegroundColor Red
}


Write-Host ""
Write-Host "Jarvis iniciado." -ForegroundColor Green