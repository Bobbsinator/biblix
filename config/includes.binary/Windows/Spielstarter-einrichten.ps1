# Richtet den Biblix-Spielstarter ein: kopiert die Biblix-Dateien nach C:\Biblix und legt
# eine Aufgabe an, die bei deiner Anmeldung einmal kurz nach einem Spielauftrag schaut.
$principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Start-Process powershell -Verb RunAs -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`""
    exit
}
Add-Type -AssemblyName PresentationFramework
$ziel = "C:\Biblix"
New-Item -ItemType Directory -Force -Path $ziel | Out-Null
Get-ChildItem -Path $PSScriptRoot -File | Where-Object { $_.Name -ne "spiele.ini" -or -not (Test-Path (Join-Path $ziel "spiele.ini")) } |
    Copy-Item -Destination $ziel -Force

$user = "$env:USERDOMAIN\$env:USERNAME"
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$ziel\Biblix-Spielstarter.ps1`""
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $user
$prin = New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Highest
$set = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Minutes 5)
Register-ScheduledTask -TaskName "Biblix Spielstarter" -Action $action -Trigger $trigger -Principal $prin -Settings $set -Force | Out-Null

[System.Windows.MessageBox]::Show("Biblix-Spielstarter ist eingerichtet (fuer $user).`n`nDateien liegen in $ziel.`nAb jetzt startet der Knopf 'Call of Duty (Windows)' in Biblix das Spiel nach deiner Anmeldung.", "Biblix") | Out-Null
