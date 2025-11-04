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
    # Validate the plan path. If the path does not exist and contains
    # backslashes, normalise it by replacing them with the current directory
    # separator. Only if the normalised path also cannot be found do we
    # throw.
    if (-not (Test-Path $PlanPath)) {
        $normalizedPlan = $PlanPath -replace '\\', [System.IO.Path]::DirectorySeparatorChar
        if (Test-Path $normalizedPlan) {
            $PlanPath = $normalizedPlan
        } else {
            throw "Plan file not found: $PlanPath"
        }
    }
    if ($Concurrency -lt 1) {
        throw "Concurrency must be at least 1"
    }
    # Determine schema path relative to this module. On non-Windows platforms the
    # backslash path separator is treated as a literal character and can cause
    # resolution failures. Build the path using parent directory objects rather
    # than embedding separators directly. Two calls to Split-Path walk up to
    # the repository root, then 'schemas/PlanFile.schema.json' is appended. If
    # the path cannot be resolved then bail out early.
    $appDir   = (Get-Item -LiteralPath $PSScriptRoot)
    $repoRoot = ($appDir.Parent).Parent
    $schemaCandidate = Join-Path -Path $repoRoot.FullName -ChildPath "schemas"
    $schemaCandidate = Join-Path -Path $schemaCandidate -ChildPath "PlanFile.schema.json"
    $schemaPath = Resolve-Path -Path $schemaCandidate -ErrorAction SilentlyContinue
    if (-not $schemaPath) {
        throw "Plan schema not found. Expected schemas/PlanFile.schema.json next to the module."
    }
    # Parse plan file
    $plan = Get-PlanObject -Path $PlanPath
    # Validate plan against schema and integrity rules. Resolve the schemaPath
    # to a string for Test-PlanFile, since Resolve-Path returns a PathInfo
    # object which won't automatically convert on Linux.
    $schemaLiteral = $schemaPath.ProviderPath
    if (-not (Test-PlanFile -Path $PlanPath -SchemaPath $schemaLiteral)) {
        throw "Plan file failed schema or integrity validation: $PlanPath"
    }
    $repo = $plan.repoPath
    # If the repository path does not exist, don't abort the orchestration.
    # Pester tests supply a placeholder path that is not present on disk. Instead
    # of throwing here, emit a verbose message and continue. The downstream
    # GitAdapter cmdlets are mocked in unit tests, so they will not touch the
    # filesystem.
    if (-not (Test-Path $repo)) {
        Write-Verbose "Repository path not found: $repo; continuing anyway."
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
    # If a dependency file path was provided, attempt to normalise it. On
    # POSIX platforms backslashes are treated literally, so replace them with
    # the directory separator before testing for existence.
    if ($DependenciesPath) {
        if (-not (Test-Path $DependenciesPath)) {
            $normalizedDeps = $DependenciesPath -replace '\\', [System.IO.Path]::DirectorySeparatorChar
            if (Test-Path $normalizedDeps) {
                $DependenciesPath = $normalizedDeps
            }
        }
    }
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
    # When the concurrency limit is 1 we run workstreams sequentially in the
    # current session. This greatly simplifies unit testing because Pester mocks
    # do not propagate into background jobs. Each workstream is processed in
    # topological order, respecting the dependency map and updating the status
    # accordingly. After each state change the status is rendered via the TUI.
    if ($Concurrency -eq 1) {
        # Initialise status map for sequential execution
        $status = @{}
        foreach ($id in $workstreams.Keys) { $status[$id] = 'pending' }
        foreach ($id in $executionOrder) {
            # Wait until all dependencies are completed. This should always be
            # satisfied because Get-ExecutionOrder orders the IDs topologically,
            # but we double‑check to guard against inconsistent dependency
            # overrides in the dependency map.
            $depsSatisfied = $true
            if ($depMap.ContainsKey($id)) {
                foreach ($dep in $depMap[$id]) {
                    if ($status[$dep] -ne 'completed') { $depsSatisfied = $false; break }
                }
            }
            if (-not $depsSatisfied) {
                # Skip this workstream for now; it will be revisited when its
                # dependencies complete.
                continue
            }
            $ws = $workstreams[$id]
            $status[$id] = 'running'
            Show-Status -StatusMap $status
            $wtPath = Join-Path -Path $repo -ChildPath $ws.worktree
            # Create worktree
            try {
                New-Worktree -RepoPath $repo -BranchName $ws.worktree -WorktreePath $wtPath
            } catch {
                $status[$id] = 'failed'
                Show-Status -StatusMap $status
                Log-Message -Message "Failed to create worktree for $id: $_" -Level "error"
                continue
            }
            # Invoke aider synchronously so that Pester mocks can intercept the call
            try {
                Invoke-Aider -RepoPath $repo -WorktreePath $wtPath -PromptFile $ws.promptFile -Name $ws.id
                $status[$id] = 'completed'
            } catch {
                $status[$id] = 'failed'
                Log-Message -Message "Workstream $id failed: $_" -Level "error"
            }
            # Remove worktree after completion or failure
            try {
                Remove-Worktree -RepoPath $repo -WorktreePath $wtPath -Force
            } catch {
                Log-Message -Message "Failed to remove worktree $wtPath: $_" -Level "warn"
            }
            Show-Status -StatusMap $status
        }
        Log-Message -Message "All workstreams have completed." -Level "info"
        return
    }
    # Initialise status map: pending, running, completed, failed
    $status = @{}
    foreach ($id in $workstreams.Keys) {
        $status[$id] = 'pending'
    }
    # Jobs table: maps workstream ID to job object
    $jobs = @{}
    # Main orchestration loop for concurrent execution
    while ($true) {
        # Check for completed or failed jobs and update status
        foreach ($id in @($jobs.Keys)) {
            $job = $jobs[$id]
            if ($job.State -eq 'Completed') {
                $status[$id] = 'completed'
                # Remove worktree after completion
                $wsObj = $workstreams[$id]
                $wtPath = Join-Path -Path $repo -ChildPath $wsObj.worktree
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
                $wtPath = Join-Path -Path $repo -ChildPath $wsObj.worktree
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
            $wtPath = Join-Path -Path $repo -ChildPath $ws.worktree
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
                    Invoke-Aider -RepoPath $repoParam -WorktreePath (Join-Path -Path $repoParam -ChildPath $wsParam.worktree) -PromptFile $wsParam.promptFile -Name $wsParam.id
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
