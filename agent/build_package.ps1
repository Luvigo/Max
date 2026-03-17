# =============================================
# Build MAX-IDE Agent distribution package (Windows)
# =============================================

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$OutputDir = Join-Path (Split-Path -Parent $ScriptDir) "editor\static\agent"
$PackageName = "maxide-agent"

Write-Host "Building MAX-IDE Agent package..."
Write-Host ""

# Crear directorio de salida
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

# Crear directorio temporal
$TempDir = Join-Path $env:TEMP "maxide-build-$(Get-Random)"
$PackageDir = Join-Path $TempDir $PackageName
New-Item -ItemType Directory -Force -Path $PackageDir | Out-Null

# Copiar archivos del agent
Copy-Item (Join-Path $ScriptDir "agent.py") $PackageDir
Copy-Item (Join-Path $ScriptDir "boards_registry.json") $PackageDir
Copy-Item (Join-Path $ScriptDir "install.py") $PackageDir
Copy-Item (Join-Path $ScriptDir "requirements.txt") $PackageDir
Copy-Item (Join-Path $ScriptDir "start_agent.bat") $PackageDir
Copy-Item (Join-Path $ScriptDir "install_autostart.bat") $PackageDir
Copy-Item (Join-Path $ScriptDir "LEEME.txt") $PackageDir
if (Test-Path (Join-Path $ScriptDir "libraries")) {
    Copy-Item (Join-Path $ScriptDir "libraries") (Join-Path $PackageDir "libraries") -Recurse -Force
}

# start_agent.sh: normalizar LF (quitar CR)
$shContent = [System.IO.File]::ReadAllText((Join-Path $ScriptDir "start_agent.sh")).Replace("`r`n", "`n").Replace("`r", "`n")
[System.IO.File]::WriteAllText((Join-Path $PackageDir "start_agent.sh"), $shContent)

# Sincronizar boards_registry al static del editor
$StaticJsonDir = Join-Path (Split-Path -Parent $ScriptDir) "editor\static\editor\json"
New-Item -ItemType Directory -Force -Path $StaticJsonDir | Out-Null
Copy-Item (Join-Path $ScriptDir "boards_registry.json") (Join-Path $StaticJsonDir "boards.json")
Write-Host "  + boards_registry.json -> editor/static/editor/json/boards.json"

# Crear ZIP
$ZipPath = Join-Path $OutputDir "$PackageName.zip"
if (Test-Path $ZipPath) { Remove-Item $ZipPath -Force }
Compress-Archive -Path $PackageDir -DestinationPath $ZipPath -Force

# Limpiar
Remove-Item -Recurse -Force $TempDir

Write-Host ""
Write-Host "Package created: $ZipPath"
Write-Host ""
