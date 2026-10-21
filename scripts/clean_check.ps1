# Clean-machine check for Windows (PowerShell). Run from the repo root:
#   powershell -ExecutionPolicy Bypass -File scripts\clean_check.ps1
# Needs your API key in .env (or set in this shell) before it is run.

$ErrorActionPreference = "Stop"
$venv = Join-Path $env:TEMP "shelfhelp-clean"
if (Test-Path $venv) { Remove-Item -Recurse -Force $venv }

py -3 -m venv $venv
& "$venv\Scripts\python.exe" -m pip install -q -r requirements.txt
& "$venv\Scripts\python.exe" -m pytest -q
& "$venv\Scripts\python.exe" run.py evals\sample_requests.json 2>$null | Out-File -Encoding utf8 "$env:TEMP\shelfhelp-out.json"
& "$venv\Scripts\python.exe" -m json.tool "$env:TEMP\shelfhelp-out.json"
Write-Host "OK: clean install works and stdout is valid JSON"
