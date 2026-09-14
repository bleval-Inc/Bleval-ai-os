param(
    [string]$Task = "You are Jenson, the executive AI for Bleval Inc. Read and follow the persona from executives/Jenson/identity.md, instructions.md, memory.md, and soul.md. Operate as the single executive operator for the project."
)

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

Write-Host "Launching Jenson as executive coordinator..."
Write-Host "Task: $Task"

ruflo agent spawn -t coordinator --name jenson --task $Task
