Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Creates a local venv and installs dependencies for stage-1 latent space pipeline.
# Usage (PowerShell):
#   cd response_latent_space
#   .\setup_env.ps1

$venvDir = Join-Path $PSScriptRoot ".venv"

if (-not (Test-Path $venvDir)) {
  python -m venv $venvDir
}

$pythonExe = Join-Path $venvDir "Scripts\python.exe"
$pipExe = Join-Path $venvDir "Scripts\pip.exe"

& $pythonExe -m pip install --upgrade pip wheel setuptools
& $pipExe install -r (Join-Path $PSScriptRoot "requirements.txt")

Write-Host "Done."
Write-Host ("Activate with: " + (Join-Path $venvDir "Scripts\Activate.ps1"))
Write-Host ""
Write-Host "Note: Parquet IO is optional. If you need it, install 'pyarrow' (or 'fastparquet') inside the venv."
