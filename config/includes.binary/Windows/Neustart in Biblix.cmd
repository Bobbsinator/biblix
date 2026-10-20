@echo off
rem Doppelklick: startet den PC einmal direkt in Biblix.
rem Tipp: Rechtsklick > Senden an > Desktop (Verknuepfung erstellen).
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Neustart-in-Biblix.ps1"
