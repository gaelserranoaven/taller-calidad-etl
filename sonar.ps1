# sonar.ps1 - Atajos de PowerShell para el taller (requiere Docker Desktop abierto).
#
#   .\sonar.ps1 levantar   -> arranca SonarQube y espera a que esté listo (http://localhost:9000)
#   .\sonar.ps1 pruebas    -> corre pytest + cobertura dentro de Docker (genera coverage.xml)
#   .\sonar.ps1 analizar   -> pruebas + envío del análisis a SonarQube (necesita $env:SONAR_TOKEN)
#   .\sonar.ps1 bajar      -> detiene SonarQube (conserva los datos)
#   .\sonar.ps1 limpiar    -> detiene SonarQube y BORRA sus datos (empezar de cero)
param(
    [Parameter(Position = 0)]
    [ValidateSet("levantar", "pruebas", "analizar", "bajar", "limpiar")]
    [string]$Accion = "analizar"
)

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

function Invoke-Docker {
    param([string[]]$Argumentos)
    & docker @Argumentos
    if ($LASTEXITCODE -ne 0) {
        throw "Fallo: docker $($Argumentos -join ' ') (código $LASTEXITCODE)"
    }
}

function Wait-SonarQube {
    Write-Host "Esperando a SonarQube (la primera vez tarda 1-3 minutos)..."
    $limite = (Get-Date).AddMinutes(6)
    while ((Get-Date) -lt $limite) {
        try {
            $estado = Invoke-RestMethod -Uri "http://localhost:9000/api/system/status" -TimeoutSec 5
            if ($estado.status -eq "UP") {
                Write-Host "SonarQube listo: http://localhost:9000" -ForegroundColor Green
                return
            }
        } catch { }
        Start-Sleep -Seconds 5
    }
    throw "SonarQube no quedó listo en 6 minutos. Revisa: docker compose logs sonarqube"
}

function Invoke-Pruebas {
    Invoke-Docker @("compose", "run", "--rm", "tests")
}

switch ($Accion) {
    "levantar" {
        Invoke-Docker @("compose", "up", "-d", "sonarqube")
        Wait-SonarQube
        Write-Host "Primer ingreso: admin / admin (te pedirá cambiar la clave)."
    }
    "pruebas" {
        Invoke-Pruebas
    }
    "analizar" {
        if (-not $env:SONAR_TOKEN) {
            throw 'Falta el token. En SonarQube: My Account > Security > Generate Token y luego: $env:SONAR_TOKEN = "squ_xxx"'
        }
        Invoke-Pruebas
        Invoke-Docker @("compose", "run", "--rm", "scanner")
        Write-Host "Análisis enviado: http://localhost:9000/dashboard?id=taller-calidad" -ForegroundColor Green
    }
    "bajar" {
        Invoke-Docker @("compose", "stop", "sonarqube")
    }
    "limpiar" {
        Invoke-Docker @("compose", "down", "-v")
    }
}
