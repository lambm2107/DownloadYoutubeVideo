# VidGrab — Build Windows Desktop App
# Chạy: .\build-desktop.ps1
# Output: dist-electron\VidGrab Setup*.exe

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ROOT = $PSScriptRoot
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  VidGrab Desktop Build" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# ── Bước 1: Build React SPA cho desktop ───────────────────────────────────────
Write-Host "`n[1/4] Build giao dien React (SPA mode)..." -ForegroundColor Yellow
Set-Location $ROOT
npx vite build --config vite.desktop.config.ts
if ($LASTEXITCODE -ne 0) { Write-Error "Vite build that bai!"; exit 1 }
Write-Host "    OK: dist-desktop/" -ForegroundColor Green

# ── Bước 2: Đóng gói Python backend thành .exe ────────────────────────────────
Write-Host "`n[2/4] Dong goi Python backend (PyInstaller)..." -ForegroundColor Yellow
$venvPy = Join-Path $ROOT "python-core\.venv\Scripts\python.exe"
if (-not (Test-Path $venvPy)) {
    Write-Error "Khong tim thay venv Python. Chay: python -m venv python-core\.venv & python-core\.venv\Scripts\pip install -r python-core\requirements.txt"
    exit 1
}

$specFile = Join-Path $ROOT "python-core\vidgrab.spec"

& $venvPy -m PyInstaller $specFile `
    --noconfirm --clean `
    --distpath (Join-Path $ROOT "dist") `
    --workpath (Join-Path $ROOT "build\pyinstaller")

if ($LASTEXITCODE -ne 0) { Write-Error "PyInstaller that bai!"; exit 1 }
Write-Host "    OK: dist\VidGrab.exe" -ForegroundColor Green

# ── Bước 3: Cài Electron dependencies ─────────────────────────────────────────
Write-Host "`n[3/4] Cai dat Electron dependencies..." -ForegroundColor Yellow
Set-Location (Join-Path $ROOT "electron")
npm install --prefer-offline 2>&1 | Select-String -NotMatch "npm warn"
if ($LASTEXITCODE -ne 0) { Write-Error "npm install that bai!"; exit 1 }
Write-Host "    OK" -ForegroundColor Green

# ── Bước 4: Build Electron installer ──────────────────────────────────────────
Write-Host "`n[4/4] Build Electron installer (.exe)..." -ForegroundColor Yellow
npm run build
if ($LASTEXITCODE -ne 0) { Write-Error "electron-builder that bai!"; exit 1 }

Set-Location $ROOT

# ── Kết quả ──────────────────────────────────────────────────────────────────
Write-Host "`n==================================================" -ForegroundColor Green
Write-Host "  Build hoan thanh!" -ForegroundColor Green
$installer = Get-ChildItem (Join-Path $ROOT "dist-electron") -Filter "*.exe" | Select-Object -First 1
if ($installer) {
    $sizeMB = [math]::Round($installer.Length / 1MB, 1)
    Write-Host "  Installer : $($installer.FullName)" -ForegroundColor White
    Write-Host "  Kich thuoc: $sizeMB MB" -ForegroundColor White
}
Write-Host "==================================================" -ForegroundColor Green
