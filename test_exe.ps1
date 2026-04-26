# Test - start and wait 7 seconds
$start = Get-Date
$proc = Start-Process -FilePath 'C:\Users\RSman\Desktop\backup script\SystemMonitor\dist\SystemMonitor.exe' -PassThru
Write-Host "Started process ID: $($proc.Id)"

Start-Sleep -Seconds 7

if ($proc.HasExited) {
    $code = $proc.ExitCode
    $elapsed = (Get-Date) - $start
    Write-Host "EXIT after 7 seconds with code: $code (elapsed: $($elapsed.TotalSeconds)s)"
} else {
    $elapsed = (Get-Date) - $start
    Write-Host "Still running at 7 seconds (elapsed: $($elapsed.TotalSeconds)s) - SUCCESS"
}