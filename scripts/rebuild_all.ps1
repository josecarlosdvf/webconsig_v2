param(
    [string]$EnvFile = ".env.docker.local",
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

$composeBuildFlags = ""
if ($NoCache) {
    $composeBuildFlags = " --no-cache"
}

Push-Location $repoRoot
try {
    Write-Host "Rebuild completo do stack em: $repoRoot" -ForegroundColor Green
    Write-Host "Env file: $envPath" -ForegroundColor Green

    Invoke-Step -Description "Build das imagens" -Command "docker compose --env-file `"$envPath`" build$composeBuildFlags"
    Invoke-Step -Description "Subida com recriação forçada" -Command "docker compose --env-file `"$envPath`" up -d --force-recreate --remove-orphans"

    if (-not $SkipMigrations) {
        Invoke-Step -Description "Aplicar migrações Alembic no container API" -Command "docker compose --env-file `"$envPath`" exec api alembic upgrade head"
    }

    Invoke-Step -Description "Status dos serviços" -Command "docker compose --env-file `"$envPath`" ps"

    Write-Host "`nStack rebuild concluído com sucesso." -ForegroundColor Green
    Write-Host "URL segura padrão: https://localhost:15443" -ForegroundColor Yellow
}
finally {
    Pop-Location
}
