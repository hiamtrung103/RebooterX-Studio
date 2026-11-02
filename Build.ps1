$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$buildPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $buildPython)) {
    py -3 -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Could not create build environment.' }
}
& $buildPython -m pip install -r requirements-build.txt
if ($LASTEXITCODE -ne 0) { throw 'Build dependencies failed.' }
& $buildPython -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw 'Tests failed.' }
& $buildPython -m PyInstaller --noconfirm RebooterX-Studio.spec
if ($LASTEXITCODE -ne 0) { throw 'Executable build failed.' }
Get-FileHash -LiteralPath 'dist\RebooterX-Studio.exe' -Algorithm SHA256
