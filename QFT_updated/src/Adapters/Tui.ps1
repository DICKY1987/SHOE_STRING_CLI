function Show-Status {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][hashtable]$StatusMap
    )
    Clear-Host
    Write-Host "=== Workstream Status ===" -ForegroundColor Yellow
    foreach ($key in $StatusMap.Keys) {
        $state = $StatusMap[$key]
        $color = switch ($state) {
            "running" { "Cyan" }
            "completed" { "Green" }
            "failed" { "Red" }
            default { "White" }
        }
        Write-Host ("{0,-12}: {1}" -f $key, $state) -ForegroundColor $color
    }
}

function Log-Message {
    param(
        [string]$Message,
        [string]$Level = "Info"
    )
    $color = switch ($Level.ToLower()) {
        "error" { "Red" }
        "warn" { "Yellow" }
        "debug" { "DarkGray" }
        default { "Gray" }
    }
    Write-Host ("[{0}] {1}" -f $Level.ToUpper(), $Message) -ForegroundColor $color
}

Export-ModuleMember -Function Show-Status,Log-Message
