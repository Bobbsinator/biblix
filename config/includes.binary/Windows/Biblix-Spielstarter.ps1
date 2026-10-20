# Biblix-Spielstarter: laeuft bei jeder Windows-Anmeldung einmal (Aufgabenplanung).
# Liegt im UEFI-Speicher ein Auftrag aus Biblix ("Call of Duty (Windows)"-Knopf),
# wird er geloescht und das passende Spiel aus spiele.ini gestartet.
#   -TestKennung cod -Trocken   nur anzeigen, was gestartet wuerde (ohne UEFI, ohne Start)
param([string]$TestKennung, [switch]$Trocken)

$GUID = "{111c1337-65dd-47c2-9e92-7c71c8e26c13}"
$NAME = "BiblixSpiel"
$ini = Join-Path $PSScriptRoot "spiele.ini"
$log = Join-Path $PSScriptRoot "spielstarter.log"
function Log($m) { "$(Get-Date -Format s)  $m" | Add-Content -Path $log -Encoding UTF8 }

if (-not ("BiblixFw" -as [type])) {
Add-Type @"
using System;
using System.Runtime.InteropServices;
public static class BiblixFw {
    [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
    public static extern uint GetFirmwareEnvironmentVariableW(string name, string guid, byte[] buffer, uint size);
    [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
    public static extern bool SetFirmwareEnvironmentVariableW(string name, string guid, IntPtr value, uint size);
    [DllImport("advapi32.dll", SetLastError = true)]
    static extern bool OpenProcessToken(IntPtr process, uint access, out IntPtr token);
    [DllImport("advapi32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
    static extern bool LookupPrivilegeValueW(string system, string name, out long luid);
    [StructLayout(LayoutKind.Sequential, Pack = 1)]
    struct TokenPrivileges { public int Count; public long Luid; public int Attributes; }
    [DllImport("advapi32.dll", SetLastError = true)]
    static extern bool AdjustTokenPrivileges(IntPtr token, bool disableAll, ref TokenPrivileges state, int len, IntPtr prev, IntPtr retLen);
    [DllImport("kernel32.dll")]
    static extern IntPtr GetCurrentProcess();
    // UEFI-Variablen lesen/loeschen braucht dieses Recht (nur mit Admin-Rechten verfuegbar)
    public static bool EnablePrivilege() {
        IntPtr token;
        if (!OpenProcessToken(GetCurrentProcess(), 0x28, out token)) return false;
        TokenPrivileges tp = new TokenPrivileges();
        tp.Count = 1; tp.Attributes = 2;
        if (!LookupPrivilegeValueW(null, "SeSystemEnvironmentPrivilege", out tp.Luid)) return false;
        if (!AdjustTokenPrivileges(token, false, ref tp, 0, IntPtr.Zero, IntPtr.Zero)) return false;
        return Marshal.GetLastWin32Error() == 0;  // 1300 = Recht fehlt trotz "Erfolg"
    }
}
"@
}

if ($TestKennung) {
    $id = $TestKennung
} else {
    if (-not [BiblixFw]::EnablePrivilege()) { Log "Kein Recht fuer UEFI-Variablen (laeuft der Starter mit hoechsten Rechten?)"; exit 1 }
    $buf = New-Object byte[] 64
    $n = [BiblixFw]::GetFirmwareEnvironmentVariableW($NAME, $GUID, $buf, 64)
    if ($n -eq 0) {
        $err = [Runtime.InteropServices.Marshal]::GetLastWin32Error()
        if ($err -ne 203) { Log "UEFI-Speicher nicht lesbar (Fehler $err)" }
        exit 0   # 203 = kein Auftrag: normaler Windows-Start
    }
    $id = [Text.Encoding]::ASCII.GetString($buf, 0, $n)
    # Auftrag sofort loeschen, damit er nur einmal greift
    [BiblixFw]::SetFirmwareEnvironmentVariableW($NAME, $GUID, [IntPtr]::Zero, 0) | Out-Null
}

if ($id -notmatch '^[a-z0-9-]{1,32}$') { Log "Ungueltige Kennung: $id"; exit 1 }
$zeile = Get-Content $ini -ErrorAction SilentlyContinue | Where-Object { $_ -match "^\s*$([regex]::Escape($id))\s*=" } | Select-Object -First 1
if (-not $zeile) { Log "Kennung '$id' steht nicht in spiele.ini"; exit 1 }
$ziel = ($zeile -replace '^\s*[^=]+=\s*', '').Trim()
# Nur Launcher-Links, keine beliebigen Programme
if ($ziel -notmatch '^(steam|battlenet|com\.epicgames\.launcher|riotclient|eaapp|uplay|goggalaxy)://') {
    Log "Ziel nicht erlaubt: $ziel"; exit 1
}
if ($Trocken) { "Wuerde starten: $id -> $ziel"; exit 0 }

Log "Starte $id -> $ziel"
# Kurz warten, bis Desktop und Steam bereit sind
Start-Sleep -Seconds 8
# Ueber den Explorer starten: das Spiel laeuft dann mit normalen Rechten, nicht als Admin
Start-Process explorer.exe -ArgumentList $ziel
