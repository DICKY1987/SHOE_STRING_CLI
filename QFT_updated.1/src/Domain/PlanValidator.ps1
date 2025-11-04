function Get-PlanObject {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$Path
    )
    # Accept both forward and backward slashes in paths. On POSIX systems a
    # backslash is treated as a literal character, so a relative path like
    # "..\file.json" may not be found. If the provided path does not exist
    # attempt to normalise it by replacing backslashes with the current
    # platform's directory separator. Only if the normalised path also does not
    # exist do we raise an error.
    if (-not (Test-Path $Path)) {
        $normalised = $Path -replace '\\', [System.IO.Path]::DirectorySeparatorChar
        if (Test-Path $normalised) {
            $Path = $normalised
        } else {
            throw "Plan file not found: $Path"
        }
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
    # Normalise the schema path so that backslashes are treated as directory
    # separators on non-Windows platforms. If the provided schema path does
    # not exist try replacing backslashes, then perform the test again.
    if (-not (Test-Path $SchemaPath)) {
        $normalizedSchema = $SchemaPath -replace '\\', [System.IO.Path]::DirectorySeparatorChar
        if (Test-Path $normalizedSchema) {
            $SchemaPath = $normalizedSchema
        } else {
            throw "Schema file not found: $SchemaPath"
        }
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
