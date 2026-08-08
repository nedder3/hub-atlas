# hub_watcher.ps1 - Watcher para Sur (Windows) via Task Scheduler.
# Se ejecuta cada 30s y dispara hub_dispatch.py --agent sur (local, sin SSH).
# RUTA REAL del hub (no la vieja Atlas\HUB, que ya no existe).
$ErrorActionPreference = "SilentlyContinue"
$hubPath = "C:\Users\arijd\Documents\Atlas\10-Projects\hub-atlas"
$log = Join-Path $hubPath ".dispatch_sur.log"
python "$hubPath\hub_dispatch.py" --agent sur --hub-path "$hubPath" *>> $log
