function Get-PlanObject {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$Path
    )
    if (-not (Test-Path $Path)) {
        throw "Plan file not found: $Path"
    }
    $text = Get-Content -Path $Path -Raw
    # Try JSON first
    try {
        return $text | ConvertFrom-Json -ErrorAction Stop
    } catch {
        # Fallback to YAML if module available
        if (Get-Command ConvertFrom-Yaml -ErrorAction SilentlyContinue) {
            try {
                return $text | ConvertFrom-Yaml -ErrorAction Stop
            } catch {
                throw "Unable to parse plan file as YAML: $_"
            }
        } else {
            throw "Plan file is not valid JSON and ConvertFrom-Yaml is not available. Please install PowerShell-Yaml or provide JSON."
        }
    }
}

function Test-PlanFile {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$SchemaPath
    )
    if (-not (Test-Path $SchemaPath)) {
        throw "Schema file not found: $SchemaPath"
    }
    # Parse plan into object
    $planObj = Get-PlanObject -Path $Path
    # Serialize to JSON for schema validation
    $planJson = $planObj | ConvertTo-Json -Depth 10
    # Validate against provided schema if Test-Json is available
    $schemaContent = Get-Content -Path $SchemaPath -Raw
    if (Get-Command Test-Json -ErrorAction SilentlyContinue) {
        try {
            $valid = Test-Json -Json $planJson -Schema $schemaContent -ErrorAction Stop
            if (-not $valid) { return $false }
        } catch {
            Write-Verbose "Schema validation failed: $_"
            return $false
        }
    } else {
        # Minimal check: ensure required properties exist
        if (-not ($planObj.PSObject.Properties.Name -contains 'repoPath') -or -not ($planObj.workstreams)) {
            return $false
        }
    }
    # Additional integrity checks
    return (Check-PlanIntegrity -Plan $planObj)
}

function Check-PlanIntegrity {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]$Plan
    )
    # Ensure workstreams array exists
    if (-not $Plan.workstreams) { return $false }
    # Check for duplicate IDs and build lookup
    $ids = @{}
    foreach ($ws in $Plan.workstreams) {
        if (-not $ws.id) { return $false }
        if ($ids.ContainsKey($ws.id)) {
            Write-Verbose "Duplicate workstream ID detected: $($ws.id)"
            return $false
        }
        $ids[$ws.id] = $true
    }
    # Check dependencies refer to existing workstreams
    foreach ($ws in $Plan.workstreams) {
        if ($ws.dependsOn) {
            foreach ($dep in $ws.dependsOn) {
                if (-not $ids.ContainsKey($dep)) {
                    Write-Verbose "Workstream '$($ws.id)' depends on unknown ID '$dep'"
                    return $false
                }
            }
        }
    }
    # Detect cycles using depth-first search
    $visited = @{}
    $stack = @{}
    function HasCycle {
        param($id)
        if ($stack[$id]) { return $true }
        if ($visited[$id]) { return $false }
        $visited[$id] = $true
        $stack[$id] = $true
        $ws = $Plan.workstreams | Where-Object { $_.id -eq $id }
        if ($ws -and $ws.dependsOn) {
            foreach ($d in $ws.dependsOn) {
                if (HasCycle $d) { return $true }
            }
        }
        $stack.Remove($id)
        return $false
    }
    foreach ($ws in $Plan.workstreams) {
        if (HasCycle $ws.id) {
            Write-Verbose "Cycle detected in dependency graph at '$($ws.id)'"
            return $false
        }
    }
    return $true
}

Export-ModuleMember -Function Get-PlanObject, Test-PlanFile, Check-PlanIntegrity
