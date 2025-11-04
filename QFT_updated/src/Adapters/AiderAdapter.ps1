function Invoke-Aider {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$RepoPath,
        [Parameter(Mandatory)][string]$WorktreePath,
        [Parameter(Mandatory)][string]$PromptFile,
        [Parameter(Mandatory)][string]$Name,
        [string]$ToolPath = "aider",
        [string[]]$ExtraArgs = @()
    )
    # Invoke the Aider CLI in headless mode. Captures output and logs to file.
    # In production, ensure $ToolPath points to the aider executable and that
    # the prompt file exists. Additional arguments may be provided via $ExtraArgs.
    if (-not (Test-Path $PromptFile)) {
        Write-Warning "Prompt file not found: $PromptFile"
    }
    $logDir = Join-Path $RepoPath "logs"
    if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir | Out-Null }
    $logFile = Join-Path $logDir ("{0}.log" -f $Name)
    Push-Location $WorktreePath
    try {
        Write-Host ("[AIDER] Starting job {0} with prompt {1}" -f $Name, $PromptFile) -ForegroundColor Cyan
        $arguments = @('--yes', '--message', "Job:$Name", '--prompt-file', $PromptFile) + $ExtraArgs
        $process = Start-Process -FilePath $ToolPath -ArgumentList $arguments -RedirectStandardOutput $logFile -RedirectStandardError $logFile -NoNewWindow -Wait -PassThru -ErrorAction Stop
        if ($process.ExitCode -ne 0) {
            Write-Warning ("[AIDER] Job {0} exited with code {1}" -f $Name, $process.ExitCode)
            throw "Aider process failed with exit code $($process.ExitCode)"
        } else {
            Write-Host ("[AIDER] Completed job {0}" -f $Name) -ForegroundColor Green
        }
    } catch {
        Write-Warning ("[AIDER] Job {0} failed: {1}" -f $Name, $_)
        throw
    } finally {
        Pop-Location
    }
}

Export-ModuleMember -Function Invoke-Aider
