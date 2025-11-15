# OpenAPI Check
Write-Host "=== OpenAPI Check ===" -ForegroundColor Cyan
try {
    $openapi = Invoke-RestMethod -Uri http://127.0.0.1:8111/openapi.json
    $routePaths = $openapi.paths.PSObject.Properties.Name | Where-Object { $_ -like "*route*" }
    Write-Host "Route-Endpoints gefunden:" -ForegroundColor Green
    $routePaths | ForEach-Object { Write-Host "  $_" }
    
    if ($routePaths -contains "/api/tour/route-details") {
        Write-Host "`n✓ /api/tour/route-details ist registriert!" -ForegroundColor Green
    } else {
        Write-Host "`n✗ /api/tour/route-details NICHT gefunden!" -ForegroundColor Red
    }
} catch {
    Write-Host "Fehler beim OpenAPI-Check: $_" -ForegroundColor Red
}

Write-Host "`n=== Route-Details Test ===" -ForegroundColor Cyan
$payload = @{
    stops = @(
        @{ lat = 51.01127; lon = 13.70161; name = "Depot" },
        @{ lat = 51.013179; lon = 13.804567; name = "36 Nici zu RP" }
    )
    include_depot = $false
} | ConvertTo-Json -Depth 10

try {
    $response = Invoke-RestMethod -Uri http://127.0.0.1:8111/api/tour/route-details -Method Post -ContentType 'application/json' -Body $payload
    Write-Host "✓ Endpoint antwortet (200)" -ForegroundColor Green
    Write-Host "Routes: $($response.routes.Count)" -ForegroundColor Cyan
    
    if ($response.routes.Count -gt 0) {
        $firstRoute = $response.routes[0]
        $hasGeometry = -not [string]::IsNullOrEmpty($firstRoute.geometry)
        Write-Host "Geometrie vorhanden: $(if ($hasGeometry) { '✓ Ja' } else { '✗ Nein' })" -ForegroundColor $(if ($hasGeometry) { 'Green' } else { 'Red' })
        Write-Host "Quelle: $($firstRoute.source)" -ForegroundColor Cyan
        Write-Host "Distanz: $($firstRoute.distance_km) km" -ForegroundColor Cyan
        Write-Host "Dauer: $($firstRoute.duration_minutes) Min" -ForegroundColor Cyan
    }
} catch {
    Write-Host "✗ Fehler: $_" -ForegroundColor Red
    if ($_.Exception.Response.StatusCode -eq 404) {
        Write-Host "  → Endpoint gibt 404 zurück!" -ForegroundColor Yellow
    }
}

