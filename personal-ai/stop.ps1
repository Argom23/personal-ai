Write-Host "Apagando Jarvis..." -ForegroundColor Yellow

# Mata procesos que estén usando los puertos
$ports = @(8000, 3000)

foreach ($port in $ports) {
    $connections = Get-NetTCPConnection `
        -LocalPort $port `
        -ErrorAction SilentlyContinue

    foreach ($connection in $connections) {
        $processId = $connection.OwningProcess

        if ($processId) {
            Stop-Process `
                -Id $processId `
                -Force `
                -ErrorAction SilentlyContinue
        }
    }
}

Write-Host "Jarvis apagado." -ForegroundColor Green