# --- CONFIG ---
$PY_VERSION = "3.13"
$VENV_NAME = "venv"
$REQ_FILE = "requirements.txt"

Write-Host "Checking for Python $PY_VERSION..."

# Check installed versions using the py launcher
$installed = py --list | Select-String $PY_VERSION

if (-not $installed) {
    Write-Host "Python $PY_VERSION is NOT installed." -ForegroundColor Red
    Write-Host "Download it here: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

Write-Host "Creating virtual environment..."

py -$PY_VERSION -m venv $VENV_NAME

Write-Host "Activating virtual environment..."
& "$VENV_NAME\Scripts\Activate.ps1"

Write-Host "Installing requirements..."
pip install --upgrade pip
pip install -r $REQ_FILE

Write-Host "Setup complete!" -ForegroundColor Green
