Write-Host "Apagando Jarvis..." -ForegroundColor Yellow

$ports = @(8000, 3000)

$processIds = @()

foreach ($port in $ports) {

    $connections = Get-NetTCPConnection `
        -LocalPort $port `
        -ErrorAction SilentlyContinue

    foreach ($connection in $connections) {

        if ($connection.OwningProcess) {
            $processIds += $connection.OwningProcess
        }
    }
}

$processIds = $processIds | Sort-Object -Unique

foreach ($processId in $processIds) {

    try {

        $process = Get-Process `
            -Id $processId `
            -ErrorAction Stop

        Write-Host (
            "Cerrando proceso: " +
            $process.ProcessName +
            " (PID " +
            $processId +
            ")"
        ) -ForegroundColor DarkGray

        Stop-Process `
            -Id $processId `
            -Force `
            -ErrorAction SilentlyContinue
    }
    catch {
        # El proceso pudo cerrarse antes.
    }
}

Write-Host "Jarvis apagado." -ForegroundColor Green