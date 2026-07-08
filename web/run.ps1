# run.ps1 — sobe o app de demonstracao do Verificador de Contestacao (Fase 2)
# com UM comando:
#
#   powershell -ExecutionPolicy Bypass -File .\run.ps1
#
# O que faz:
#   1. Cria o ambiente virtual (web\.venv) se nao existir e instala as deps.
#   2. Builda o frontend (npm install + npm run build) se ainda nao houver build.
#   3. Sobe o FastAPI em http://localhost:8000 servindo API + frontend.
#
# Parametros:
#   -Porta 8000     porta do servidor (padrao 8000)
#   -Rebuild        forca reinstalar deps e rebuildar o frontend

param(
    [int]$Porta = 8000,
    [switch]$Rebuild
)

$ErrorActionPreference = "Stop"
$raiz = $PSScriptRoot
$python = Join-Path $raiz ".venv\Scripts\python.exe"
$frontend = Join-Path $raiz "frontend"
$dist = Join-Path $frontend "dist"

Write-Host "=== Verificador de Contestacao - demo (Fase 2) ===" -ForegroundColor Cyan

# 1. ambiente virtual + dependencias do backend -----------------------------
if (-not (Test-Path $python)) {
    Write-Host "`n[1/3] Criando ambiente virtual (web\.venv)..." -ForegroundColor Yellow
    python -m venv (Join-Path $raiz ".venv")
    & $python -m pip install --quiet --upgrade pip
    & $python -m pip install --quiet -r (Join-Path $raiz "backend\requirements.txt")
} elseif ($Rebuild) {
    Write-Host "`n[1/3] Reinstalando dependencias do backend..." -ForegroundColor Yellow
    & $python -m pip install --quiet -r (Join-Path $raiz "backend\requirements.txt")
} else {
    Write-Host "`n[1/3] Ambiente virtual ja existe." -ForegroundColor Green
}

# 2. build do frontend -------------------------------------------------------
if (-not (Test-Path $dist) -or $Rebuild) {
    Write-Host "`n[2/3] Buildando o frontend (npm install + build)..." -ForegroundColor Yellow
    Push-Location $frontend
    npm install --no-fund --no-audit
    if ($LASTEXITCODE -ne 0) { Pop-Location; throw "npm install falhou" }
    npm run build
    if ($LASTEXITCODE -ne 0) { Pop-Location; throw "npm run build falhou" }
    Pop-Location
} else {
    Write-Host "`n[2/3] Frontend ja buildado (use -Rebuild para refazer)." -ForegroundColor Green
}

# 3. servidor ----------------------------------------------------------------
Write-Host "`n[3/3] Subindo em http://localhost:$Porta ..." -ForegroundColor Yellow
Write-Host "      (Ctrl+C para encerrar)`n" -ForegroundColor DarkGray
$env:PYTHONIOENCODING = "utf-8"
Start-Process "http://localhost:$Porta"
Set-Location (Join-Path $raiz "backend")
& $python -m uvicorn app:app --port $Porta
