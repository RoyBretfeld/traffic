@echo off
echo Stoppe alle Python-Prozesse...
taskkill /F /IM python.exe 2>nul
timeout /t 2 /nobreak >nul

echo Starte CSV Bulk Processor Test...
python test_standalone.py

echo.
echo Test abgeschlossen. Druecken Sie eine beliebige Taste...
pause >nul
