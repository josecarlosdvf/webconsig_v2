param(
    [string]$EnvFile = ".env.docker.local",
    [string[]]$Services = @("api", "web", "gateway"),
    [switch]$OnlyRestart,
    [switch]$SkipMigrations,
    [switch]$NoCache,
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Invoke-Step {
    param(
        [string]$Description,
        [string]$Command
    )

    Write-Host "`n==> $Description" -ForegroundColor Cyan
    Write-Host "    $Command" -ForegroundColor DarkGray

    if ($DryRun) {
        return
    }

    Invoke-Expression $Command
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$envPath = Join-Path $repoRoot $EnvFile

if (-not (Test-Path $envPath)) {
    throw "Arquivo de ambiente não encontrado: $envPath"
}

$normalizedServices = @()
foreach ($item in $Services) {
    if (-not $item) {
        continue
    }
    $parts = $item -split ","
    foreach ($part in $parts) {
        $service = $part.Trim()
        if ($service.Length -gt 0) {
            $normalizedServices += $service
        }
    }
}

$serviceList = ($normalizedServices | Select-Object -Unique) -join " "
if (-not $serviceList) {
    throw "Informe ao menos um serviço em -Services"
}

$buildFlags = ""
if ($NoCache) {
    $buildFlags = " --no-cache"
}

Push-Location $repoRoot
try {
    Write-Host "Aplicação incremental de mudanças em: $repoRoot" -ForegroundColor Green
    Write-Host "Env file: $envPath" -ForegroundColor Green
    Write-Host "Serviços alvo: $serviceList" -ForegroundColor Green

    if ($OnlyRestart) {
        Invoke-Step -Description "Reiniciar apenas serviços alvo" -Command "docker compose --env-file `"$envPath`" restart $serviceList"
    }
    else {
        Invoke-Step -Description "Build apenas dos serviços alvo" -Command "docker compose --env-file `"$envPath`" build$buildFlags $serviceList"
        Invoke-Step -Description "Subir/recriar apenas serviços alvo" -Command "docker compose --env-file `"$envPath`" up -d $serviceList"
    }

    if ((-not $SkipMigrations) -and ($normalizedServices -contains "api" -or $serviceList -match "\bapi\b")) {
        Invoke-Step -Description "Aplicar migrações Alembic (api)" -Command "docker compose --env-file `"$envPath`" exec api alembic upgrade head"
    }

    Invoke-Step -Description "Status dos serviços" -Command "docker compose --env-file `"$envPath`" ps"

    Write-Host "`nAplicação incremental concluída." -ForegroundColor Green
}
finally {
    Pop-Location
}
