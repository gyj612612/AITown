param(
    [string]$Version = "1.0.0",
    [string]$SteamAppId = "480",
    [switch]$UseIsolatedVenv = $true,
    [switch]$UsePythonLauncher = $true
)

$ErrorActionPreference = "Stop"

function Invoke-Checked {
    param(
        [string]$CommandName,
        [string[]]$Arguments
    )
    & $CommandName @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed: $CommandName $($Arguments -join ' ')"
    }
}

function Invoke-BasePython {
    param(
        [string[]]$Arguments
    )
    if ($UsePythonLauncher) {
        Invoke-Checked -CommandName "py" -Arguments (@("-3.11") + $Arguments)
    }
    else {
        Invoke-Checked -CommandName "python" -Arguments $Arguments
    }
}

$pythonExe = "python"
if ($UseIsolatedVenv) {
    $venvPath = ".venv_build"
    if (!(Test-Path $venvPath)) {
        Write-Host "==> Creating isolated build venv: $venvPath"
        Invoke-BasePython -Arguments @("-m", "venv", $venvPath)
    }
    $pythonExe = Join-Path $venvPath "Scripts/python.exe"
}
elseif ($UsePythonLauncher) {
    $pythonExe = "py"
}

Write-Host "==> Installing dependencies"
if ($pythonExe -eq "py") {
    Invoke-Checked -CommandName $pythonExe -Arguments @("-3.11", "-m", "pip", "install", "--upgrade", "pip")
    Invoke-Checked -CommandName $pythonExe -Arguments @("-3.11", "-m", "pip", "install", "-r", "requirements-dev.txt")
}
else {
    Invoke-Checked -CommandName $pythonExe -Arguments @("-m", "pip", "install", "--upgrade", "pip")
    Invoke-Checked -CommandName $pythonExe -Arguments @("-m", "pip", "install", "-r", "requirements-dev.txt")
}

Write-Host "==> Running tests"
if ($pythonExe -eq "py") {
    Invoke-Checked -CommandName $pythonExe -Arguments @("-3.11", "-m", "pytest")
    Invoke-Checked -CommandName $pythonExe -Arguments @("-3.11", "scripts/smoke_test.py")
}
else {
    Invoke-Checked -CommandName $pythonExe -Arguments @("-m", "pytest")
    Invoke-Checked -CommandName $pythonExe -Arguments @("scripts/smoke_test.py")
}

Write-Host "==> Running lint"
if ($pythonExe -eq "py") {
    Invoke-Checked -CommandName $pythonExe -Arguments @("-3.11", "-m", "ruff", "check", ".")
    Invoke-Checked -CommandName $pythonExe -Arguments @("-3.11", "scripts/license_guard.py")
}
else {
    Invoke-Checked -CommandName $pythonExe -Arguments @("-m", "ruff", "check", ".")
    Invoke-Checked -CommandName $pythonExe -Arguments @("scripts/license_guard.py")
}

Write-Host "==> Building executable with PyInstaller"
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }

$assetsArg = "--add-data=assets;assets"
$docsArg = "--add-data=docs;docs"
$licensesArg = "--add-data=THIRD_PARTY_LICENSES.md;."

$excludeModules = @(
    "--exclude-module", "numpy",
    "--exclude-module", "scipy",
    "--exclude-module", "pandas",
    "--exclude-module", "matplotlib",
    "--exclude-module", "setuptools",
    "--exclude-module", "wheel",
    "--exclude-module", "yaml"
)

$iconPath = "assets/sprites/app.ico"
$pyiArgs = @(
    "-m", "PyInstaller",
    "--noconfirm",
    "--clean",
    "--windowed",
    "--name", "AITown",
    $assetsArg,
    $docsArg,
    $licensesArg
) + $excludeModules + @("main.py")

if (Test-Path $iconPath) {
    $pyiArgs += @("--icon", $iconPath)
}

if ($pythonExe -eq "py") {
    Invoke-Checked -CommandName $pythonExe -Arguments (@("-3.11") + $pyiArgs)
}
else {
    Invoke-Checked -CommandName $pythonExe -Arguments $pyiArgs
}

if (Test-Path "release/windows") {
    cmd /c rmdir /s /q release\windows
}
New-Item -ItemType Directory -Force -Path "release/windows" | Out-Null
Copy-Item -Recurse -Force "dist/AITown/*" "release/windows/"
Set-Content -Path "release/windows/version.txt" -Value $Version -Encoding UTF8
Set-Content -Path "release/windows/steam_appid.txt" -Value $SteamAppId -Encoding ASCII
Copy-Item -Force "RELEASE_NOTES.md" "release/windows/RELEASE_NOTES.md"
Copy-Item -Force "THIRD_PARTY_LICENSES.md" "release/windows/THIRD_PARTY_LICENSES.md"

Write-Host "==> Build complete: release/windows"
