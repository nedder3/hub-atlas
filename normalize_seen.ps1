$seenDir = Join-Path $PSScriptRoot ".seen"
$briefsDir = Join-Path $PSScriptRoot "briefs"

if (-not (Test-Path $seenDir)) { New-Item -ItemType Directory -Path $seenDir | Out-Null }
if (-not (Test-Path $briefsDir)) { New-Item -ItemType Directory -Path $briefsDir | Out-Null }

$cleanedCount = 0
$createdCount = 0

# Clean up old format markers
$seenFiles = Get-ChildItem -Path $seenDir -File
foreach ($file in $seenFiles) {
    # Match any marker that doesn't have .md before the double underscore
    if ($file.Name -match "__" -and $file.Name -notmatch "\.md__") {
        Remove-Item $file.FullName -Force
        $cleanedCount++
        Write-Host "Removed old format marker: $($file.Name)"
    }
}

# Ensure every existing brief has a marker for both norte and sur
$briefFiles = Get-ChildItem -Path $briefsDir -Filter "*.md" -File
foreach ($brief in $briefFiles) {
    $briefName = $brief.Name
    foreach ($agent in @("norte", "sur")) {
        $markerName = "${briefName}__${agent}"
        $markerPath = Join-Path $seenDir $markerName
        
        if (-not (Test-Path $markerPath)) {
            New-Item -ItemType File -Path $markerPath | Out-Null
            $createdCount++
            Write-Host "Created missing marker: $markerName"
        }
    }
}

Write-Host "----------------------------------------"
Write-Host "Summary:"
Write-Host "Removed old format markers: $cleanedCount"
Write-Host "Created missing markers: $createdCount"
Write-Host "Done."
