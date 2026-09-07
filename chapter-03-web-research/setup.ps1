$ErrorActionPreference = "Stop"

Write-Host "Creating virtual environment..."
python -m venv .venv

Write-Host "Activating virtual environment..."
.\.venv\Scripts\Activate.ps1

Write-Host "Upgrading pip..."
python -m pip install --upgrade pip

Write-Host "Installing Chapter 3 dependencies..."
pip install -r requirements.txt

Write-Host "Installing Chromium for optional Playwright live-page rendering..."
python -m playwright install chromium

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env from .env.example"
}

Write-Host ""
Write-Host "Setup complete. Edit .env and set OPENAI_API_KEY and OPENAI_MODEL."
Write-Host "Then test the plumbing with:"
Write-Host "python experiments/full_experiment.py --provider mock --config config/experiment.demo.yaml --reset"
