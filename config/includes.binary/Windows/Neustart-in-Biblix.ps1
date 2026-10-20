# Neustart in Biblix: startet den PC einmal direkt in Biblix (UEFI BootNext).
# Danach startet der PC wieder wie gewohnt. Braucht Admin-Rechte (fragt automatisch).
#   -Pruefen   zeigt nur an, ob Biblix gefunden wird, aendert nichts
param([switch]$Pruefen)

$principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    $arg = "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`""
    if ($Pruefen) { $arg += " -Pruefen" }
    Start-Process powershell -Verb RunAs -ArgumentList $arg
    exit
}

Add-Type -AssemblyName PresentationFramework

# bcdedit-Ausgabe ist je nach Windows-Sprache anders beschriftet: deshalb nur nach
# dem Eintrag suchen, in dem "Biblix" vorkommt, und dessen {GUID} nehmen.
$text = (bcdedit /enum firmware) -join "`n"
$block = ($text -split "`n\s*`n") | Where-Object { $_ -match 'Biblix|debian' } | Select-Object -First 1
$guid = if ($block) { [regex]::Match($block, '\{[0-9a-fA-F\-]{36}\}').Value } else { "" }

if (-not $guid) {
    [System.Windows.MessageBox]::Show("Biblix wurde im UEFI nicht gefunden.`n`nIst Biblix schon installiert? Sonst ueber das Bootmenue des PCs (F8/F11/F12) starten.", "Neustart in Biblix", "OK", "Error") | Out-Null
    exit 1
}
if ($Pruefen) {
    [System.Windows.MessageBox]::Show("Biblix gefunden: $guid", "Neustart in Biblix") | Out-Null
    exit 0
}

$antwort = [System.Windows.MessageBox]::Show("Jetzt in Biblix neu starten?`n`nNicht gespeicherte Arbeit geht verloren.", "Neustart in Biblix", "YesNo", "Question")
if ($antwort -ne "Yes") { exit 0 }

bcdedit /set "{fwbootmgr}" bootsequence $guid | Out-Null
shutdown /r /t 0
