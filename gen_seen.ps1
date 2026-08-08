$b = Get-ChildItem C:\Users\arijd\Documents\Atlas\HUB\briefs\*.md | Where-Object { $_.BaseName -ne 'brief_20260808_060500' } | ForEach-Object { $_.BaseName }
$lines = @()
foreach ($n in $b) { $lines += "$n|norte"; $lines += "$n|sur" }
Set-Content -Path C:\Users\arijd\Documents\Atlas\HUB\.seen.log -Value $lines
Write-Host "lineas: $($lines.Count)"
