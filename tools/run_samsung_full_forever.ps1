$root = Split-Path -Parent $PSScriptRoot
$done = Join-Path $root "data\logs\samsung_full.DONE"
$log = Join-Path $root "data\logs\samsung_full.log"
while (-not (Test-Path (Join-Path $root "data\STOP_SAMSUNG_FULL")) -and -not (Test-Path $done)) {
    & (Join-Path $root ".venv\Scripts\python.exe") -P (Join-Path $root "tools\samsung_full_download.py")
    if (Test-Path $done) { break }
    Add-Content -Path $log -Value ("{0} restart loop: restarting in 60 s" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"))
    Start-Sleep -Seconds 60
}
