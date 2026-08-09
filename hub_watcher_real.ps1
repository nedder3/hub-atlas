<#
.SYNOPSIS
    Watches the 'briefs' directory for new markdown files and triggers the hub dispatcher.

.DESCRIPTION
    This script uses System.IO.FileSystemWatcher to monitor the specified directory for new .md files.
    When a new file is detected, it waits 2 seconds (debounce) to ensure the file write is complete,
    then runs the python dispatcher script. Events and errors are logged.
#>

$WatcherDir = "C:\Users\arijd\Documents\Atlas\10-Projects\hub-atlas\briefs\"
$LogFile = "C:\Users\arijd\Documents\Atlas\10-Projects\hub-atlas\.dispatch_sur.log"
$PythonScript = "C:\Users\arijd\Documents\Atlas\10-Projects\hub-atlas\hub_dispatch.py"
$HubPath = "C:\Users\arijd\Documents\Atlas\10-Projects\hub-atlas"

function Write-Log {
    param (
        [string]$Message,
        [string]$Level = "INFO"
    )
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogMessage = "[$Timestamp] [$Level] $Message"
    Write-Host $LogMessage
    $LogMessage | Out-File -FilePath $LogFile -Append -Encoding UTF8
}

Write-Log "Starting Atlas HUB Watcher..."
Write-Log "Watching directory: $WatcherDir"
Write-Log "Logging to: $LogFile"

if (-not (Test-Path $WatcherDir)) {
    Write-Log "Directory $WatcherDir does not exist. Creating it." "WARN"
    New-Item -ItemType Directory -Force -Path $WatcherDir | Out-Null
}

$Watcher = New-Object System.IO.FileSystemWatcher
$Watcher.Path = $WatcherDir
$Watcher.Filter = "*.md"
$Watcher.IncludeSubdirectories = $false
$Watcher.EnableRaisingEvents = $true

$Action = {
    $path = $Event.SourceEventArgs.FullPath
    $changeType = $Event.SourceEventArgs.ChangeType
    Write-Log "Detected $changeType on file: $path"
    
    # Debounce: Wait 2 seconds to avoid partial writes
    Start-Sleep -Seconds 2
    
    try {
        Write-Log "Dispatching python script for newly detected file."
        $Command = "python"
        $Args = @("$PythonScript", "--agent", "sur", "--hub-path", "$HubPath", "--once")
        
        $Process = Start-Process -FilePath $Command -ArgumentList $Args -NoNewWindow -PassThru -Wait
        
        if ($Process.ExitCode -eq 0) {
            Write-Log "Dispatch successful."
        } else {
            Write-Log "Dispatch failed with exit code $($Process.ExitCode)." "ERROR"
        }
    } catch {
        Write-Log "Error running dispatcher: $_" "ERROR"
    }
}

$EventSubscriber = Register-ObjectEvent -InputObject $Watcher -EventName "Created" -Action $Action

Write-Log "Watcher started. Press Ctrl+C to stop."

try {
    while ($true) {
        Start-Sleep -Seconds 1
    }
}
finally {
    Write-Log "Stopping Atlas HUB Watcher..."
    Unregister-Event -SourceIdentifier $EventSubscriber.Name
    $Watcher.EnableRaisingEvents = $false
    $Watcher.Dispose()
    Write-Log "Watcher stopped."
}
