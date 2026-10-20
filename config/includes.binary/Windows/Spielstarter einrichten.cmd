@echo off
rem Einmal doppelklicken: richtet den Biblix-Spielstarter ein (fragt nach Admin-Rechten).
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Spielstarter-einrichten.ps1"
