function Resolve-DependencyMap {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [array]$Dependencies
    )
    # Build a hash table mapping target workstream IDs to dependency arrays
    $map = @{}
    foreach ($dep in $Dependencies) {
        $target = $dep.target
        $depends = $dep.dependsOn
        if ($target -and $depends) {
            $map[$target] = $depends
        }
    }
    return $map
}

function Get-ExecutionOrder {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]$Plan
    )
    # Produce a topologically sorted list of workstream IDs. Throws if a cycle exists.
    $ids = @()
    $adj = @{}
    $indegree = @{}
    foreach ($ws in $Plan.workstreams) {
        $ids += $ws.id
        $adj[$ws.id] = @()
        $indegree[$ws.id] = 0
    }
    foreach ($ws in $Plan.workstreams) {
        $deps = @()
        if ($ws.dependsOn) { $deps = $ws.dependsOn }
        foreach ($d in $deps) {
            $adj[$d] += $ws.id
            $indegree[$ws.id]++
        }
    }
    # queue of nodes with zero in-degree
    $queue = [System.Collections.Generic.Queue[string]]::new()
    foreach ($id in $ids) {
        if ($indegree[$id] -eq 0) { $queue.Enqueue($id) }
    }
    $order = @()
    while ($queue.Count -gt 0) {
        $n = $queue.Dequeue()
        $order += $n
        foreach ($m in $adj[$n]) {
            $indegree[$m]--
            if ($indegree[$m] -eq 0) { $queue.Enqueue($m) }
        }
    }
    if ($order.Count -ne $ids.Count) {
        throw "Cycle detected in dependency graph; cannot determine execution order."
    }
    return $order
}

Export-ModuleMember -Function Resolve-DependencyMap, Get-ExecutionOrder
