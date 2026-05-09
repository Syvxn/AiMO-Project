#Requires -Version 5.1
param()

$ErrorActionPreference = "Stop"
$ScriptDir = $PSScriptRoot
$VenvDir = Join-Path $ScriptDir ".venv"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
$TargetMajorMinor = "3.11"

function Write-Step([string]$msg) {
    Write-Host ""
    Write-Host "==> $msg" -ForegroundColor Cyan
}
function Write-Ok([string]$msg) { Write-Host "    OK: $msg" -ForegroundColor Green }
function Write-Err([string]$msg) { Write-Host "    ERROR: $msg" -ForegroundColor Red }

# 1. Find Python 3.11
Write-Step "Finding Python $TargetMajorMinor ..."
$pythonExe = $null
$candidate = & py "-$TargetMajorMinor" -c "import sys; print(sys.executable)" 2>$null
if ($LASTEXITCODE -eq 0 -and $candidate) { $pythonExe = $candidate.Trim() }
if (-not $pythonExe) {
    Write-Err "Python $TargetMajorMinor not found. Install it from python.org."
    exit 1
}
Write-Ok "$( & $pythonExe --version 2>&1 ) ($pythonExe)"

# 2. Create / validate venv
$needCreate = $false
if (Test-Path $VenvDir) {
    if (Test-Path $VenvPython) {
        $venvVer = & $VenvPython -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>&1
        if ($venvVer.Trim() -ne $TargetMajorMinor) {
            Write-Step "Venv is Python $venvVer - recreating with Python $TargetMajorMinor ..."
            Remove-Item -Recurse -Force $VenvDir
            $needCreate = $true
        } else {
            Write-Ok "Venv already exists with Python $venvVer."
        }
    } else {
        Write-Step "Venv exists but python.exe missing - recreating ..."
        Remove-Item -Recurse -Force $VenvDir
        $needCreate = $true
    }
} else {
    $needCreate = $true
}

if ($needCreate) {
    Write-Step "Creating virtual environment at .venv ..."
    & $pythonExe -m venv $VenvDir
    Write-Ok "Virtual environment created."
}

# 3. Bootstrap pip if missing
$pipOk = & $VenvPython -c "import pip" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Step "Bootstrapping pip ..."
    & $VenvPython -m ensurepip --upgrade
}

# 4. Install dependencies
Write-Step "Installing / upgrading dependencies (may take a while on first run)..."
& $VenvPython -m pip install --quiet --upgrade pip
& $VenvPython -m pip install --quiet -e "$ScriptDir/.[dev]"
& $VenvPython -m pip install --quiet fastapi "uvicorn[standard]" httpx
Write-Ok "Dependencies installed."

# 5. Ensure .env exists
$envFile    = Join-Path $ScriptDir ".env"
$envExample = Join-Path $ScriptDir ".env.example"
if (-not (Test-Path $envFile)) {
    Write-Step "No .env found - copying .env.example to .env ..."
    Copy-Item $envExample $envFile
    Write-Host "    Edit $envFile to customise model IDs if needed." -ForegroundColor Yellow
} else {
    Write-Ok ".env already exists."
}

# 6. Start the server
Write-Step "Starting agents server on http://0.0.0.0:8001 ..."
Write-Host "    Press Ctrl+C to stop." -ForegroundColor Yellow
Write-Host ""

& $VenvPython -m uvicorn aimo_agents.server:app --host 0.0.0.0 --port 8001 --app-dir "$ScriptDir/src"
