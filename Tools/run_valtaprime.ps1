param(
    [string]$Task = "You are Valta Prime, the executive AI for House of Valta. Read and follow the persona from executives/ValtaPrime/identity.md, instructions.md, memory.md, and soul.md. Operate as the executive operator for House of Valta."
)

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

Write-Host "Launching Valta Prime as executive coordinator..."
Write-Host "Task: $Task"

ruflo agent spawn -t coordinator --name valta_prime --task $Task