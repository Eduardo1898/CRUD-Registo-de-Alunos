[CmdletBinding()]
param(
    [string]$Python
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
    throw 'Execute este script no Windows. O PyInstaller usa o sistema operacional local.'
}

function Invoke-Native {
    param([string]$Executable, [string[]]$Arguments)
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Executable falhou com código $LASTEXITCODE."
    }
}

$root = Split-Path -Parent $PSScriptRoot
Push-Location $root
try {
    $venv = Join-Path $root '.venv-build'
    if ($Python) {
        Invoke-Native $Python @('-m', 'venv', $venv)
    } else {
        Invoke-Native 'py' @('-3.12', '-m', 'venv', $venv)
    }
    $buildPython = Join-Path $venv 'Scripts\python.exe'
    Invoke-Native $buildPython @('-c', "import sys, sysconfig; sys.exit(0 if sys.version_info[:2] == (3, 12) and sysconfig.get_platform() == 'win-amd64' else 'Use Python 3.12 x64 para Windows.')")
    Invoke-Native $buildPython @('-m', 'pip', 'install', '-r', 'requirements-build.txt')
    Invoke-Native $buildPython @(
        '-m', 'PyInstaller', '--clean', '--noconfirm',
        '--workpath', 'build/windows', '--distpath', 'dist/windows', 'StudentHub.spec'
    )

    $bundle = Join-Path $root 'dist\windows\StudentHub'
    $exe = Join-Path $bundle 'StudentHub.exe'
    if (-not (Test-Path -LiteralPath $exe -PathType Leaf)) {
        throw 'StudentHub.exe não foi produzido.'
    }
    $localFiles = Get-ChildItem -LiteralPath $bundle -File -Recurse -Force |
        Where-Object { $_.Name -match '\.(db|sqlite|sqlite3)(-.*)?$|\.(csv|xlsx)$' }
    if ($localFiles) {
        throw 'O pacote inclui bancos ou relatórios. O ZIP não foi criado.'
    }

    $zip = Join-Path $root 'dist\windows\StudentHub-v1.0.0-windows-x64.zip'
    if (Test-Path -LiteralPath $zip) {
        Remove-Item -LiteralPath $zip
    }
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [IO.Compression.ZipFile]::CreateFromDirectory(
        $bundle, $zip, [IO.Compression.CompressionLevel]::Optimal, $true
    )
    Write-Host "Pacote gerado em $zip"
} finally {
    Pop-Location
}
