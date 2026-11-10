@echo off
setlocal
cd /d "%~dp0"
title Set up Hernandez Invoice

echo Setting up the Hernandez Invoice desktop icon...
set "HI_PYTHONW="
rem Find the installed Python interpreter, then use its windowless version.
for /f "delims=" %%I in ('py -3 -c "import sys; print(sys.executable)" 2^>nul') do if not defined HI_PYTHONW set "HI_PYTHONW=%%~dpIpythonw.exe"
if not exist "%HI_PYTHONW%" set "HI_PYTHONW="
if not defined HI_PYTHONW for /f "delims=" %%I in ('python -c "import sys; print(sys.executable)" 2^>nul') do if not defined HI_PYTHONW set "HI_PYTHONW=%%~dpIpythonw.exe"
if not exist "%HI_PYTHONW%" (
  echo Python was not found. Install Python 3.9 or newer and run this setup again.
  pause
  exit /b 1
)
set "HI_PROJECT=%~dp0"
set "HI_LAUNCHER=%~dp0open_hernandez_invoice.pyw"
set "HI_ICON=%~dp0assets\hernandez_invoice.ico"
rem PowerShell creates a standard Windows shortcut. Arguments are passed through
rem environment variables so spaces and apostrophes in folder names are safe.
powershell.exe -NoProfile -NonInteractive -Command "$ErrorActionPreference='Stop'; $shell=New-Object -ComObject WScript.Shell; 
$desktop=[Environment]::GetFolderPath('Desktop'); if (-not $desktop) { throw 'Desktop folder not found' };
 $shortcut=$shell.CreateShortcut([IO.Path]::Combine($desktop,'Hernandez Invoice.lnk')); 
 $shortcut.TargetPath=$env:HI_PYTHONW; $shortcut.Arguments=[char]34 + $env:HI_LAUNCHER + 
 [char]34; $shortcut.WorkingDirectory=$env:HI_PROJECT; $shortcut.IconLocation=$env:HI_ICON + 
 ',0'; $shortcut.Description='Open Hernandez Invoice'; $shortcut.Save()"
if errorlevel 1 (
  echo The shortcut could not be created. Check that you can write to your Desktop.
  pause
  exit /b 1
)
echo.
echo Done! Open Hernandez Invoice from the new desktop icon.
echo Keep this folder on the computer or USB drive in its current location.
pause
