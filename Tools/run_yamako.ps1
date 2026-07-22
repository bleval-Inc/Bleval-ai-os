param(
    [string]$Task = "You are Yamako, the personal chief of staff AI for the founder. Read and follow the persona from executives/Yamako/identity.md, instructions.md, memory.md, and soul.md. Operate as the founder's executive support agent."
)

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

Write-Host "Launching Yamako as executive coordinator..."
Write-Host "Task: $Task"

ruflo agent spawn -t coordinator --name yamako --task $Task