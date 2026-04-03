#Requires AutoHotkey v2.0
#SingleInstance Force
Persistent

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
TraySetIcon("shell32.dll", 71)  ; Clipboard icon from shell32
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
    ; Check if clipboard has image data by running TCP core
    path := GetImagePath()
    if path != "" {
        ; Type the path instead of pasting
        prevDelay := A_KeyDelay
        SetKeyDelay 0
        SendInput path
        SetKeyDelay prevDelay
    } else {
        ; No image — pass through normal Ctrl+V
        SendInput "^v"
    }
}
#HotIf

; --- Alt+V: Universal force paste ---
!v:: {
    path := GetImagePath()
    if path != "" {
        prevDelay := A_KeyDelay
        SetKeyDelay 0
        SendInput path
        SetKeyDelay prevDelay
    }
    ; If no image, Alt+V just does nothing
}
