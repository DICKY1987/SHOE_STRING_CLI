function New-Worktree {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$RepoPath,
        [Parameter(Mandatory)][string]$BranchName,
        [Parameter(Mandatory)][string]$WorktreePath
    )
    Push-Location $RepoPath
    try {
        # Ensure remote is fetched
        git fetch origin | Out-Null
        # Ensure branch exists; create from origin/main if missing
        if (-not (git rev-parse --verify $BranchName 2>$null)) {
            git checkout -B $BranchName origin/main | Out-Null
        }
        # Create worktree if path does not exist
        if (-not (Test-Path $WorktreePath)) {
            git worktree add $WorktreePath $BranchName | Out-Null
        }
    } catch {
        Write-Warning "Failed to create worktree $WorktreePath: $_"
    } finally {
        Pop-Location
    }
}

function Ensure-Branch {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$RepoPath,
        [Parameter(Mandatory)][string]$BranchName,
        [string]$BaseBranch = "origin/main"
    )
    Push-Location $RepoPath
    try {
        git fetch origin | Out-Null
        $exists = git rev-parse --verify $BranchName 2>$null
        if (-not $?) {
            git checkout -B $BranchName $BaseBranch | Out-Null
        }
    } finally {
        Pop-Location
    }
}

function Checkout-Branch {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$RepoPath,
        [Parameter(Mandatory)][string]$BranchName
    )
    Push-Location $RepoPath
    try {
        git checkout $BranchName | Out-Null
    } finally {
        Pop-Location
    }
}

function Push-Branch {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$RepoPath,
        [Parameter(Mandatory)][string]$BranchName
    )
    Push-Location $RepoPath
    try {
        git push -u origin $BranchName | Out-Null
    } finally {
        Pop-Location
    }
}

function Prune-Worktrees {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$RepoPath
    )
    Push-Location $RepoPath
    try {
        git worktree prune | Out-Null
    } finally {
        Pop-Location
    }
}

function Remove-Worktree {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$RepoPath,
        [Parameter(Mandatory)][string]$WorktreePath,
        [switch]$Force
    )
    Push-Location $RepoPath
    try {
        $args = @('worktree','remove')
        if ($Force) { $args += '--force' }
        $args += $WorktreePath
        git @args | Out-Null
    } catch {
        Write-Warning "Failed to remove worktree $WorktreePath: $_"
    } finally {
        Pop-Location
    }
}

function Get-WorktreeStatus {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$RepoPath
    )
    Push-Location $RepoPath
    try {
        $output = git worktree list --porcelain
        # Parse output into objects
        $list = @()
        $current = @{}
        foreach ($line in $output) {
            if ($line -match '^worktree ') {
                if ($current.Count -gt 0) { $list += [pscustomobject]$current; $current = @{} }
                $current.Path = $line.Substring(9).Trim()
            } elseif ($line -match '^HEAD ') {
                $current.Head = $line.Substring(5).Trim()
            } elseif ($line -match '^branch ') {
                $current.Branch = $line.Substring(7).Trim()
            }
        }
        if ($current.Count -gt 0) { $list += [pscustomobject]$current }
        return $list
    } finally {
        Pop-Location
    }
}

Export-ModuleMember -Function New-Worktree,Remove-Worktree,Get-WorktreeStatus
Export-ModuleMember -Function Ensure-Branch,Checkout-Branch,Push-Branch,Prune-Worktrees
