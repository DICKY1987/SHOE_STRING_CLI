Import-Module "$PSScriptRoot/../Domain/PlanValidator.ps1" -Force
Import-Module "$PSScriptRoot/../Domain/DependencyManager.ps1" -Force
Import-Module "$PSScriptRoot/../Adapters/GitAdapter.ps1" -Force
Import-Module "$PSScriptRoot/../Adapters/AiderAdapter.ps1" -Force
Import-Module "$PSScriptRoot/../Adapters/Tui.ps1" -Force

function Start-Orchestration {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$PlanPath,
        [string]$DependenciesPath,
        [int]$Concurrency = 5,
        [switch]$Verbose
    )
    <#
    .SYNOPSIS
        Main entry point for the Aider orchestrator. Validates the plan file,
        resolves dependencies and manages concurrent execution of workstreams
        via git worktrees and headless Aider processes.

    .DESCRIPTION
        This function reads a plan file (JSON or YAML), validates it against
        the plan schema and integrity rules, optionally loads additional
        dependencies from a separate file, then executes the defined
        workstreams in parallel while respecting a dependency graph. It
        creates git worktrees for each workstream, launches Aider as a
        background job, updates a status map and displays progress via
        the TUI.

    .PARAMETER PlanPath
        Path to the plan file (JSON or YAML). Must conform to PlanFile.schema.json
        and pass integrity checks.
    .PARAMETER DependenciesPath
        Optional path to a separate dependency file (JSON or YAML) listing
        additional dependency edges. Entries in this file override any
        dependsOn properties in the plan for the corresponding targets.
    .PARAMETER Concurrency
        Maximum number of workstreams to run concurrently. Defaults to 5.
    .PARAMETER Verbose
        Switch to enable verbose logging via the TUI.
    #>
    # Validate parameters
    if (-not (Test-Path $PlanPath)) {
        throw "Plan file not found: $PlanPath"
    }
    if ($Concurrency -lt 1) {
        throw "Concurrency must be at least 1"
    }
    # Determine schema path relative to this module
    $schemaPath = Join-Path $PSScriptRoot "..\..\schemas\PlanFile.schema.json" | Resolve-Path -ErrorAction SilentlyContinue
    if (-not $schemaPath) {
        throw "Plan schema not found. Expected schemas/PlanFile.schema.json next to the module."
    }
    # Parse plan file
    $plan = Get-PlanObject -Path $PlanPath
    # Validate plan against schema and integrity rules
    if (-not (Test-PlanFile -Path $PlanPath -SchemaPath $schemaPath)) {
        throw "Plan file failed schema or integrity validation: $PlanPath"
    }
    $repo = $plan.repoPath
    if (-not (Test-Path $repo)) {
        throw "Repository path not found: $repo"
    }
    # Build workstream map (ID -> workstream object)
    $workstreams = @{}
    foreach ($ws in $plan.workstreams) {
        $workstreams[$ws.id] = $ws
    }
    # Resolve dependencies: start with dependsOn defined in plan
    $depMap = @{}
    foreach ($ws in $plan.workstreams) {
        if ($ws.dependsOn) {
            $depMap[$ws.id] = @($ws.dependsOn)
        }
    }
    # Merge in dependency file if provided. Entries override plan dependsOn
    if ($DependenciesPath -and (Test-Path $DependenciesPath)) {
        try {
            $depObj = Get-PlanObject -Path $DependenciesPath
            if ($depObj.dependencies) {
                foreach ($d in $depObj.dependencies) {
                    $depMap[$d.target] = @($d.dependsOn)
                }
            }
        } catch {
            Write-Warning "Dependency file could not be parsed: $DependenciesPath. Ignoring file."
        }
    }
    # Determine execution order using topological sort for deterministic scheduling
    $executionOrder = Get-ExecutionOrder -Plan $plan
    # Initialise status map: pending, running, completed, failed
    $status = @{}
    foreach ($id in $workstreams.Keys) {
        $status[$id] = 'pending'
    }
    # Jobs table: maps workstream ID to job object
    $jobs = @{}
    # Main orchestration loop
    while ($true) {
        # Check for completed or failed jobs and update status
        foreach ($id in @($jobs.Keys)) {
            $job = $jobs[$id]
            if ($job.State -eq 'Completed') {
                $status[$id] = 'completed'
                # Remove worktree after completion
                $wsObj = $workstreams[$id]
                $wtPath = Join-Path $repo $wsObj.worktree
                Try {
                    Remove-Worktree -RepoPath $repo -WorktreePath $wtPath -Force
                } Catch {
                    # Log and continue
                    Log-Message -Message "Failed to remove worktree $wtPath: $_" -Level "warn"
                }
                Remove-Job -Job $job -Force
                $jobs.Remove($id)
                if ($Verbose) { Log-Message -Message "Completed workstream $id" -Level "info" }
            } elseif ($job.State -eq 'Failed') {
                $status[$id] = 'failed'
                $wsObj = $workstreams[$id]
                $wtPath = Join-Path $repo $wsObj.worktree
                Try {
                    Remove-Worktree -RepoPath $repo -WorktreePath $wtPath -Force
                } Catch {
                    Log-Message -Message "Failed to remove worktree $wtPath: $_" -Level "warn"
                }
                Remove-Job -Job $job -Force
                $jobs.Remove($id)
                if ($Verbose) { Log-Message -Message "Workstream $id failed" -Level "error" }
            }
        }
        # Determine which workstreams are ready to run
        $ready = @()
        foreach ($id in $executionOrder) {
            if ($status[$id] -ne 'pending') { continue }
            # gather dependencies for this workstream
            $deps = @()
            if ($depMap.ContainsKey($id)) {
                $deps = $depMap[$id]
            }
            $depsSatisfied = $true
            foreach ($dep in $deps) {
                if ($status[$dep] -ne 'completed') {
                    $depsSatisfied = $false
                    break
                }
            }
            if ($depsSatisfied) { $ready += $id }
        }
        # Launch ready workstreams while under concurrency limit
        foreach ($id in $ready) {
            if ($jobs.Count -ge $Concurrency) { break }
            $ws = $workstreams[$id]
            $status[$id] = 'running'
            $wtPath = Join-Path $repo $ws.worktree
            # Create worktree (branch named same as worktree)
            try {
                New-Worktree -RepoPath $repo -BranchName $ws.worktree -WorktreePath $wtPath
            } catch {
                $status[$id] = 'failed'
                Log-Message -Message "Failed to create worktree for $id: $_" -Level "error"
                continue
            }
            # Launch aider in background job with runspace isolation
            $jobs[$id] = Start-Job -ScriptBlock {
                param($wsParam, $repoParam)
                Import-Module "$using:PSScriptRoot/../Adapters/AiderAdapter.ps1" -Force
                Import-Module "$using:PSScriptRoot/../Adapters/GitAdapter.ps1" -Force
                Import-Module "$using:PSScriptRoot/../Adapters/Tui.ps1" -Force
                try {
                    Invoke-Aider -RepoPath $repoParam -WorktreePath (Join-Path $repoParam $wsParam.worktree) -PromptFile $wsParam.promptFile -Name $wsParam.id
                } catch {
                    throw $_
                }
            } -ArgumentList $ws, $repo
            if ($Verbose) { Log-Message -Message "Started workstream $id" -Level "info" }
        }
        # Display status via TUI
        Show-Status -StatusMap $status
        # Break when all workstreams have finished (no pending or running states)
        if ($status.Values -notcontains 'pending' -and $status.Values -notcontains 'running') {
            break
        }
        Start-Sleep -Milliseconds 500
    }
    Log-Message -Message "All workstreams have completed." -Level "info"
}

Export-ModuleMember -Function Start-Orchestration
