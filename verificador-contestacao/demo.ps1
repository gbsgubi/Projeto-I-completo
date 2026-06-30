# demo.ps1 - Demonstracao "de um clique" do verificador de contestacao.
#
# O que faz:
#   1. Cria o ambiente virtual (.venv) se ainda nao existir.
#   2. Instala as dependencias de requirements.txt.
#   3. Roda o verificador sobre a minuta de teste (PDF e HTML).
#
# Como rodar (na pasta do projeto):
#   powershell -ExecutionPolicy Bypass -File .\demo.ps1
# ou, dentro do Claude Code / terminal:
#   .\demo.ps1

$ErrorActionPreference = "Stop"
$raiz = $PSScriptRoot
$python = Join-Path $raiz ".venv\Scripts\python.exe"

# garante que o pacote 'src' seja encontrado (python -m roda a partir da raiz)
Set-Location $raiz

# saida em UTF-8 para acentos aparecerem corretamente
$env:PYTHONIOENCODING = "utf-8"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "=== Verificador de Contestacao - DEMO ===" -ForegroundColor Cyan

# 1. ambiente virtual
if (-not (Test-Path $python)) {
    Write-Host "`n[1/3] Criando ambiente virtual (.venv)..." -ForegroundColor Yellow
    python -m venv (Join-Path $raiz ".venv")
} else {
    Write-Host "`n[1/3] Ambiente virtual ja existe." -ForegroundColor Green
}

# 2. dependencias
Write-Host "`n[2/3] Instalando dependencias..." -ForegroundColor Yellow
& $python -m pip install --quiet --upgrade pip
& $python -m pip install --quiet -r (Join-Path $raiz "requirements.txt")

# 3. execucao sobre a minuta de teste
$pdf  = Join-Path $raiz "tests\fixtures\minuta_teste.pdf"
$html = Join-Path $raiz "tests\fixtures\minuta_teste.html"

Write-Host "`n[3/3] Rodando o verificador..." -ForegroundColor Yellow

Write-Host "`n------------------------------------------------------------" -ForegroundColor DarkGray
Write-Host " ENTRADA: minuta_teste.pdf  (formato principal)" -ForegroundColor Cyan
Write-Host "------------------------------------------------------------" -ForegroundColor DarkGray
& $python -m src.verificador $pdf

Write-Host "`n------------------------------------------------------------" -ForegroundColor DarkGray
Write-Host " ENTRADA: minuta_teste.html (formato nativo do SAPIENS)" -ForegroundColor Cyan
Write-Host "------------------------------------------------------------" -ForegroundColor DarkGray
& $python -m src.verificador $html

Write-Host "`n=== Fim da demo ===" -ForegroundColor Cyan
Write-Host "Dica: para verificar uma minuta sua, rode:" -ForegroundColor DarkGray
Write-Host "  .\.venv\Scripts\python.exe -m src.verificador CAMINHO\DA\MINUTA.pdf" -ForegroundColor DarkGray

# o verificador retorna 1 quando o veredito e REPROVADO; aqui a demo
# rodou com sucesso, entao saimos com 0 para nao parecer falha.
exit 0
