$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot
$pythonExecutable = (Get-Command python -ErrorAction Stop).Source
& $pythonExecutable app.py
