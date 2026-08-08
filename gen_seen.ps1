# gen_seen.ps1 - Marca todos los briefs existentes como ya vistos por ambos
# agentes, para no reprocesar historia al arrancar el watcher.
# RUTA REAL del hub (no la vieja Atlas\HUB).
$hubPath = "C:\Users\arijd\Documents\Atlas\10-Projects\hub-atlas"
$briefsDir = Join-Path $hubPath "briefs"
$seenLog = Join-Path $hubPath ".seen.log"
$b = Get-ChildItem $briefsDir\*.md | ForEach-Object { $_.BaseName }
$lines = @()
foreach ($n in $b) { $lines += "$n|norte"; $lines += "$n|sur" }
Set-Content -Path $seenLog -Value $lines
Write-Host "lineas: $($lines.Count)"
