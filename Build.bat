@echo off
python -m PyInstaller ^
  --onefile ^
  --noconsole ^
  --name "FL Studio Plugin Organizer" ^
  FLPLUGIN-ARRENGER.pyw
pause