@echo off
rem Entfernt den Biblix-Spielstarter wieder (Aufgabe loeschen).
powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process powershell -Verb RunAs -ArgumentList '-NoProfile -Command Unregister-ScheduledTask -TaskName ''Biblix Spielstarter'' -Confirm:$false'"
