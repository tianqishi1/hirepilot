# 一键开发环境：Mock站 + standalone Worker 两轮演示
$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
chcp 65001 | Out-Null
$env:PYTHONIOENCODING = "utf-8"
$site = Start-Process python -ArgumentList "$root\mock-site\app.py" -WindowStyle Hidden -PassThru
Start-Sleep -Seconds 3
try {
    python "$root\worker\main.py" --job 1 --auto-approve --standalone --fresh
    python "$root\worker\main.py" --job 1 --auto-approve --standalone
} finally {
    Stop-Process -Id $site.Id -ErrorAction SilentlyContinue
}
