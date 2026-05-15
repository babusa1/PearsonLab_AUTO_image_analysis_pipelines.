# =============================================================================
# Pearson Lab — Conda environment setup (Windows PowerShell)
# =============================================================================
# Author:        Shreeya Malvi
# Email:          shreeya.malvi@colorado.edu
# Date Created:   2025-05-01
# Date Modified:  2026-05-16
# Version:        1.2.0
#
# Purpose: One-time install of the pearsonlab conda environment and package.
# Usage:   .\scripts\setup_conda.ps1
# =============================================================================

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

Write-Host "Creating conda environment 'pearsonlab'..."
conda env create -f environment.yml --force

Write-Host "Activating and installing package in editable mode..."
conda activate pearsonlab
pip install -e .

Write-Host ""
Write-Host "Done. Next steps:"
Write-Host "  conda activate pearsonlab"
Write-Host '  python run_cbf.py --input "YOUR_VIDEO_FOLDER" --fps 150 --pixel-um 0.162 --no-prompt'
