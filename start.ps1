$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (-not (Test-Path '.venv\Scripts\python.exe')) {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Cannot create Python environment.' }
}
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
& .\.venv\Scripts\python.exe manage.py migrate
if ($LASTEXITCODE -ne 0) { throw 'Migration failed.' }
& .\.venv\Scripts\python.exe manage.py seed_demo
if ($LASTEXITCODE -ne 0) { throw 'Demo data creation failed.' }
& .\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
