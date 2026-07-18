param([int]$Port = 5001)
Write-Host "Checking port $Port..."

Get-Process -Name litellm -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep 2

do {
    $conns = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    if ($conns) {
        Write-Host "Found connections on port $Port..."
        foreach ($c in $conns) {
            if ($c.OwningProcess -and $c.OwningProcess -ne 0) {
                try {
                    Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue
                    Write-Host "  Killed PID" $c.OwningProcess
                } catch {}
            }
        }
        Start-Sleep 1
    }
} while ($conns -and (Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue))

Write-Host "[OK] Port $Port is now free"
Start-Sleep 1
