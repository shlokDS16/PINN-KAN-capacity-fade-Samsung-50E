# Restart loop for tools/resumable_download.py: runs it again (it resumes from the bytes on disk)
# until it writes data/logs/downloader.DONE or someone creates data/STOP_DOWNLOADS.
$root = Split-Path -Parent $PSScriptRoot
$done = Join-Path $root "data\logs\downloader.DONE"
$stop = Join-Path $root "data\STOP_DOWNLOADS"
$log = Join-Path $root "data\logs\downloader.log"
while (-not (Test-Path $done) -and -not (Test-Path $stop)) {
    & python -I (Join-Path $root "tools\resumable_download.py")
    Add-Content -Path $log -Value ("{0} restart loop: downloader exited, restarting in 60 s" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"))
    Start-Sleep -Seconds 60
}
