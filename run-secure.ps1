$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

$adminLogin = Read-Host "Admin login (standart: admin)"
if ([string]::IsNullOrWhiteSpace($adminLogin)) {
    $adminLogin = "admin"
}

$securePassword = Read-Host "Admin uchun yangi kuchli parol" -AsSecureString
if ($securePassword.Length -lt 16) {
    throw "Admin paroli kamida 16 belgidan iborat bo'lishi kerak."
}
$passwordPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)

try {
    $env:OSINT_ADMIN_USERNAME = $adminLogin
    $env:OSINT_ADMIN_PASSWORD = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($passwordPointer)
    $env:OSINT_SEED_DEMO = "0"
    $pythonExecutable = (Get-Command python -ErrorAction Stop).Source
    & $pythonExecutable app.py
}
finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($passwordPointer)
    Remove-Item Env:OSINT_ADMIN_PASSWORD -ErrorAction SilentlyContinue
}
