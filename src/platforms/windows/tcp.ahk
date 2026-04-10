#Requires AutoHotkey v2.0
#SingleInstance Force
Persistent

; --- Global mutex: prevent multiple TCP instances across different script paths ---
DllCall("CreateMutex", "Ptr", 0, "Int", 0, "Str", "TCPClipboardPaster")
if A_LastError = 183  ; ERROR_ALREADY_EXISTS
    ExitApp

; --- Configuration ---
TCP_PYTHON := "python"
TCP_SCRIPT := A_ScriptDir "\..\..\..\tcp_core.py"

; Built-in terminal executables
TERMINALS := Map(
    "WindowsTerminal.exe", true,
    "powershell.exe", true,
    "pwsh.exe", true,
    "cmd.exe", true,
    "warp.exe", true,
    "Code.exe", true,
    "alacritty.exe", true,
    "mintty.exe", true
)

; Load extra terminals from config (if tcp_core.py --terminals is implemented)
; For now, built-in list only. Config integration in future version.

; --- System Tray ---
TraySetIcon(A_ScriptDir "\..\..\..\assets\tcp-tray-icon.ico")
A_IconTip := "TCP active — Ctrl+V smart paste, Alt+V force paste"

tray := A_TrayMenu
tray.Delete()  ; Clear default menu
tray.Add("TCP - Terminal Copy Paste", (*) => "")
tray.Disable("TCP - Terminal Copy Paste")
tray.Add()  ; Separator
tray.Add("Pause", MenuPause)
tray.Add("Exit", MenuExit)

MenuPause(name, pos, menu) {
    Suspend
    if A_IsSuspended {
        menu.Rename(name, "Resume")
        A_IconTip := "TCP paused"
    } else {
        menu.Rename("Resume", "Pause")
        A_IconTip := "TCP active — Ctrl+V smart paste, Alt+V force paste"
    }
}

MenuExit(*) {
    ExitApp
}

; --- Helper: Check if active window is a terminal ---
IsTerminal() {
    try {
        exe := WinGetProcessName("A")
        return TERMINALS.Has(exe)
    }
    return false
}

; --- Helper: Paste path via clipboard (bracketed paste in terminals) ---
PastePath(path) {
    saved := ClipboardAll()
    A_Clipboard := path
    SendInput "^v"
    ; Restore clipboard after terminal has time to read it
    SetTimer(() => (A_Clipboard := saved), -150)
}

; --- Helper: Run TCP core and get path ---
GetImagePath() {
    try {
        tempFile := A_Temp "\tcp_output_" A_TickCount ".txt"
        exitCode := RunWait(A_ComSpec ' /c ' TCP_PYTHON ' -m src.tcp_core > "' tempFile '"', A_ScriptDir "\..\..\..","Hide")
        if exitCode = 0 && FileExist(tempFile) {
            path := FileRead(tempFile)
            FileDelete(tempFile)
            path := Trim(path, "`r`n `t")
            if path != ""
                return path
        }
        ; Clean up temp file on non-zero exit
        if FileExist(tempFile)
            FileDelete(tempFile)
    }
    return ""
}

; --- Ctrl+V: Smart paste in terminals ---
#HotIf IsTerminal()
$^v:: {
    path := GetImagePath()
    if path != "" {
        PastePath(path)
    } else {
        Send "^v"
    }
}
#HotIf

; --- Alt+V: Universal force paste ---
!v:: {
    path := GetImagePath()
    if path != "" {
        PastePath(path)
    }
}
