$root = Split-Path -Parent $PSScriptRoot
$log = Join-Path $root "data\logs\samsung_cu.log"
while (-not (Test-Path (Join-Path $root "data\STOP_SAMSUNG"))) {
    & (Join-Path $root ".venv\Scripts\python.exe") -P (Join-Path $root "tools\samsung_cu_batch.py")
    if ((Get-Content $log -Tail 1) -match "finished") { break }
    Add-Content -Path $log -Value ("{0} restart loop: restarting in 60 s" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"))
    Start-Sleep -Seconds 60
}
