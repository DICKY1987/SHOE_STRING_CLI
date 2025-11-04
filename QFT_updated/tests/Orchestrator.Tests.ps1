Import-Module "$PSScriptRoot/../src/Domain/PlanValidator.ps1" -Force
Import-Module "$PSScriptRoot/../src/Domain/DependencyManager.ps1" -Force
Import-Module "$PSScriptRoot/../src/Adapters/GitAdapter.ps1" -Force
Import-Module "$PSScriptRoot/../src/Adapters/AiderAdapter.ps1" -Force
Import-Module "$PSScriptRoot/../src/Adapters/Tui.ps1" -Force
Import-Module "$PSScriptRoot/../src/Application/Orchestrator.ps1" -Force

Describe "Plan Validator" {
    It "Validates a correct plan file" {
        $planPath = Join-Path $PSScriptRoot "..\PlanFile.example.json"
        $schemaPath = Join-Path $PSScriptRoot "..\schemas\PlanFile.schema.json"
        $result = Test-PlanFile -Path $planPath -SchemaPath $schemaPath
        $result | Should -BeTrue
    }

    It "Detects duplicate IDs and fails integrity" {
        $tmp = Join-Path $PSScriptRoot "duplicate-plan.json"
        # create a temporary plan string with duplicate IDs
        $plan = '{"repoPath": "/tmp", "workstreams": [ {"id": "ws-1", "worktree": "a", "promptFile": "pf.md"}, {"id": "ws-1", "worktree": "b", "promptFile": "pf.md"} ] }'
        $plan | Set-Content -Path $tmp
        $schemaPath = Join-Path $PSScriptRoot "..\schemas\PlanFile.schema.json"
        (Test-PlanFile -Path $tmp -SchemaPath $schemaPath) | Should -BeFalse
        Remove-Item $tmp -ErrorAction SilentlyContinue
    }
}

Describe "Orchestrator execution" {
    It "Processes workstreams respecting dependencies and concurrency" {
        $planPath = Join-Path $PSScriptRoot "..\PlanFile.example.json"
        $depsPath = Join-Path $PSScriptRoot "..\DependencyFile.example.yaml"
        # Track the order of starts
        $startOrder = [System.Collections.ArrayList]::new()
        # Mock GitAdapter.New-Worktree
        Mock -ModuleName GitAdapter -CommandName New-Worktree {
            param($RepoPath,$BranchName,$WorktreePath)
            # record start order
            [void]$startOrder.Add($BranchName)
        }
        # Mock GitAdapter.Remove-Worktree
        Mock -ModuleName GitAdapter -CommandName Remove-Worktree {
            param($RepoPath,$WorktreePath,[switch]$Force) | Out-Null
        }
        # Mock AiderAdapter.Invoke-Aider to simulate some work
        Mock -ModuleName AiderAdapter -CommandName Invoke-Aider {
            param($RepoPath,$WorktreePath,$PromptFile,$Name)
            Start-Sleep -Milliseconds 100
        }
        # Mock Tui.Show-Status to avoid console output
        Mock -ModuleName Tui -CommandName Show-Status {
            param($StatusMap) | Out-Null
        }
        # Execute orchestrator with concurrency 1 to force sequential execution
        Start-Orchestration -PlanPath $planPath -DependenciesPath $depsPath -Concurrency 1
        # Assert that ws-001 started before ws-002
        $startOrder[0] | Should -Be "qft-ws-a"
        $startOrder[1] | Should -Be "qft-ws-b"
    }
}
