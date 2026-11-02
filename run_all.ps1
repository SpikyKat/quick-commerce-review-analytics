$py = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$env:PYTHONIOENCODING = "utf-8"
& $py -m pytest -q
Push-Location scripts
foreach ($s in "01_audit.py", "02_review_themes.py", "03_text_model.py", "04_orders_audit.py", "05_powerbi_export.py") {
    Write-Host "== $s"
    & $py $s | Out-Null
}
Pop-Location

