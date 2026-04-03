; TCP - Terminal Copy Paste
; Inno Setup Script
; Requires Inno Setup 6+

#define MyAppName "Terminal Copy Paste"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Crossroads Technologies, LLC"
#define MyAppURL "https://github.com/CodeWarrior4Life/TerminalCopyPaste"
#define MyAppExeName "tcp.ahk"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
DefaultDirName={localappdata}\tcp
DefaultGroupName={#MyAppName}
LicenseFile=..\LICENSE
OutputDir=..\dist
OutputBaseFilename=TCPSetup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
SetupIconFile=compiler:SetupClassicIcon.ico
UninstallDisplayIcon={app}\src\platforms\windows\tcp.ahk

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "startup"; Description: "Start TCP on login"; Flags: unchecked

[Files]
; Copy entire project
Source: "..\src\*"; DestDir: "{app}\src"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\config\*"; DestDir: "{app}\config"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\requirements.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\src\platforms\windows\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{userstartup}\TCP"; Filename: "{app}\src\platforms\windows\{#MyAppExeName}"; Tasks: startup

[Run]
; Install Python if needed (check done in Code section)
Filename: "{tmp}\python-installer.exe"; Parameters: "/quiet InstallAllUsers=0 PrependPath=1 Include_launcher=1"; StatusMsg: "Installing Python..."; Flags: waituntilterminated; Check: NeedsPython
; Install AHK if needed
Filename: "{tmp}\ahk-installer.exe"; Parameters: "/silent"; StatusMsg: "Installing AutoHotkey v2..."; Flags: waituntilterminated; Check: NeedsAHK
; Install pip dependencies
Filename: "python"; Parameters: "-m pip install --quiet -r ""{app}\requirements.txt"""; StatusMsg: "Installing Python dependencies..."; Flags: runhidden waituntilterminated
; Copy default config if not present
Filename: "{cmd}"; Parameters: "/c if not exist ""{userappdata}\tcp\config.toml"" ( mkdir ""{userappdata}\tcp"" 2>nul & copy ""{app}\config\config.example.toml"" ""{userappdata}\tcp\config.toml"" )"; Flags: runhidden waituntilterminated
; Launch TCP
Filename: "{app}\src\platforms\windows\{#MyAppExeName}"; Description: "Launch TCP now"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[Code]
var
  PythonNeeded: Boolean;
  AHKNeeded: Boolean;

function NeedsPython: Boolean;
begin
  Result := PythonNeeded;
end;

function NeedsAHK: Boolean;
begin
  Result := AHKNeeded;
end;

function IsPythonInstalled: Boolean;
var
  ResultCode: Integer;
begin
  Result := Exec('python', '--version', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) and (ResultCode = 0);
end;

function IsAHKInstalled: Boolean;
begin
  Result := RegKeyExists(HKLM, 'SOFTWARE\AutoHotkey') or
            RegKeyExists(HKCU, 'SOFTWARE\AutoHotkey');
end;

procedure InitializeWizard;
begin
  PythonNeeded := not IsPythonInstalled;
  AHKNeeded := not IsAHKInstalled;
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  DownloadPage: TDownloadWizardPage;
begin
  Result := '';

  if PythonNeeded or AHKNeeded then
  begin
    DownloadPage := CreateDownloadPage(SetupMessage(msgWizardPreparing), SetupMessage(msgPreparingDesc), nil);
    DownloadPage.Clear;

    if PythonNeeded then
      DownloadPage.Add('https://www.python.org/ftp/python/3.13.1/python-3.13.1-amd64.exe', 'python-installer.exe', '');

    if AHKNeeded then
      DownloadPage.Add('https://www.autohotkey.com/download/ahk-v2.exe', 'ahk-installer.exe', '');

    DownloadPage.Show;
    try
      try
        DownloadPage.Download;
      except
        Result := GetExceptionMessage;
      end;
    finally
      DownloadPage.Hide;
    end;
  end;
end;
