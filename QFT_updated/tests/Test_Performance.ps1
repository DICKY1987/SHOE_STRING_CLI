# Performance Tests for PowerShell Optimizations
Import-Module "$PSScriptRoot/../src/Domain/PlanValidator.ps1" -Force
Import-Module "$PSScriptRoot/../src/Domain/DependencyManager.ps1" -Force

Describe "PlanValidator Performance" {
    It "Efficiently validates plans with many workstreams" {
        # Create a plan with 50 workstreams
        $workstreams = @()
        for ($i = 1; $i -le 50; $i++) {
            $ws = [PSCustomObject]@{
                id = "ws-$i"
                worktree = "wt-$i"
                promptFile = "prompt-$i.md"
                dependsOn = @()
            }
            # Add some dependencies
            if ($i -gt 1) {
                $ws.dependsOn += "ws-$($i-1)"
            }
            $workstreams += $ws
        }
        
        $plan = [PSCustomObject]@{
            repoPath = "/tmp/test"
            workstreams = $workstreams
        }
        
        $startTime = Get-Date
        $result = Check-PlanIntegrity -Plan $plan
        $elapsed = (Get-Date) - $startTime
        
        $result | Should -BeTrue
        $elapsed.TotalSeconds | Should -BeLessThan 2.0
        Write-Host "Plan integrity check took $($elapsed.TotalMilliseconds)ms for 50 workstreams"
    }
    
    It "Efficiently detects cycles in dependency graph" {
        # Create workstreams with no cycles
        $workstreams = @()
        for ($i = 1; $i -le 30; $i++) {
            $ws = [PSCustomObject]@{
                id = "ws-$i"
                worktree = "wt-$i"
                promptFile = "prompt-$i.md"
                dependsOn = @()
            }
            # Create a more complex dependency graph
            if ($i -gt 2) {
                $ws.dependsOn += "ws-$($i-1)"
                $ws.dependsOn += "ws-$($i-2)"
            }
            elseif ($i -gt 1) {
                $ws.dependsOn += "ws-$($i-1)"
            }
            $workstreams += $ws
        }
        
        $plan = [PSCustomObject]@{
            repoPath = "/tmp/test"
            workstreams = $workstreams
        }
        
        $startTime = Get-Date
        $result = Check-PlanIntegrity -Plan $plan
        $elapsed = (Get-Date) - $startTime
        
        $result | Should -BeTrue
        $elapsed.TotalSeconds | Should -BeLessThan 1.0
        Write-Host "Cycle detection took $($elapsed.TotalMilliseconds)ms for 30 workstreams"
    }
    
    It "Efficiently computes execution order via topological sort" {
        # Create workstreams with dependencies
        $workstreams = @()
        for ($i = 1; $i -le 40; $i++) {
            $ws = [PSCustomObject]@{
                id = "ws-$i"
                worktree = "wt-$i"
                promptFile = "prompt-$i.md"
                dependsOn = @()
            }
            if ($i -gt 1 -and ($i % 2) -eq 0) {
                $ws.dependsOn += "ws-$($i-1)"
            }
            $workstreams += $ws
        }
        
        $plan = [PSCustomObject]@{
            repoPath = "/tmp/test"
            workstreams = $workstreams
        }
        
        $startTime = Get-Date
        $order = Get-ExecutionOrder -Plan $plan
        $elapsed = (Get-Date) - $startTime
        
        $order.Count | Should -Be 40
        $elapsed.TotalSeconds | Should -BeLessThan 0.5
        Write-Host "Topological sort took $($elapsed.TotalMilliseconds)ms for 40 workstreams"
    }
}

Write-Host "`nRunning Performance Tests..." -ForegroundColor Yellow
Invoke-Pester -Path $PSScriptRoot/Test_Performance.ps1 -Output Detailed
