; TCP - Terminal Copy Paste
; Inno Setup Script
; Requires Inno Setup 6+

#define MyAppName "Terminal Copy Paste"
#define MyAppVersion "1.1.0"
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
Name: "startup"; Description: "Start TCP on login"

[Files]
; Copy entire project
Source: "..\src\*"; DestDir: "{app}\src"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\config\*"; DestDir: "{app}\config"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\requirements.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{code:GetAHKExePath}"; Parameters: """{app}\src\platforms\windows\{#MyAppExeName}"""; IconFilename: "{app}\assets\tcp-tray-icon.ico"; Check: IsAHKInstalled
Name: "{group}\{#MyAppName}"; Filename: "{app}\src\platforms\windows\{#MyAppExeName}"; IconFilename: "{app}\assets\tcp-tray-icon.ico"; Check: not IsAHKInstalled
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{userstartup}\TCP"; Filename: "{code:GetAHKExePath}"; Parameters: """{app}\src\platforms\windows\{#MyAppExeName}"""; IconFilename: "{app}\assets\tcp-tray-icon.ico"; Tasks: startup; Check: IsAHKInstalled
Name: "{userstartup}\TCP"; Filename: "{app}\src\platforms\windows\{#MyAppExeName}"; IconFilename: "{app}\assets\tcp-tray-icon.ico"; Tasks: startup; Check: not IsAHKInstalled

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
var
  Ver: String;
begin
  // Check HKLM (standard install)
  if RegKeyExists(HKLM, 'SOFTWARE\AutoHotkey\v2') then begin Result := True; exit; end;
  if RegQueryStringValue(HKLM, 'SOFTWARE\AutoHotkey', 'Version', Ver) then
    if (Length(Ver) > 0) and (Ver[1] = '2') then begin Result := True; exit; end;
  // Check HKCU (Scoop / per-user install)
  if RegKeyExists(HKCU, 'SOFTWARE\AutoHotkey\v2') then begin Result := True; exit; end;
  if RegQueryStringValue(HKCU, 'SOFTWARE\AutoHotkey', 'Version', Ver) then
    if (Length(Ver) > 0) and (Ver[1] = '2') then begin Result := True; exit; end;
  Result := False;
end;

function GetAHKExePath: String;
var
  InstallDir: String;
begin
  // Check HKLM first (standard install)
  if RegQueryStringValue(HKLM, 'SOFTWARE\AutoHotkey', 'InstallDir', InstallDir) then begin
    if FileExists(InstallDir + '\v2\AutoHotkey64.exe') then begin
      Result := InstallDir + '\v2\AutoHotkey64.exe';
      exit;
    end;
    if FileExists(InstallDir + '\v2\AutoHotkey32.exe') then begin
      Result := InstallDir + '\v2\AutoHotkey32.exe';
      exit;
    end;
  end;
  // Check HKCU (Scoop / per-user install)
  if RegQueryStringValue(HKCU, 'SOFTWARE\AutoHotkey', 'InstallDir', InstallDir) then begin
    if FileExists(InstallDir + '\v2\AutoHotkey64.exe') then begin
      Result := InstallDir + '\v2\AutoHotkey64.exe';
      exit;
    end;
    if FileExists(InstallDir + '\v2\AutoHotkey32.exe') then begin
      Result := InstallDir + '\v2\AutoHotkey32.exe';
      exit;
    end;
  end;
  // Fallback: rely on file association
  Result := '';
end;

procedure KillExistingTCP;
var
  ResultCode: Integer;
begin
  // Kill any running AutoHotkey instances running tcp.ahk
  Exec('cmd.exe', '/c taskkill /F /FI "IMAGENAME eq AutoHotkey64.exe" /FI "WINDOWTITLE eq tcp*" 2>nul', '',
       SW_HIDE, ewWaitUntilTerminated, ResultCode);
  Exec('cmd.exe', '/c taskkill /F /FI "IMAGENAME eq AutoHotkey.exe" /FI "WINDOWTITLE eq tcp*" 2>nul', '',
       SW_HIDE, ewWaitUntilTerminated, ResultCode);
  // Also try WMIC for command-line match (catches background instances)
  Exec('cmd.exe', '/c wmic process where "name like ''AutoHotkey%'' and commandline like ''%tcp.ahk%''" call terminate 2>nul', '',
       SW_HIDE, ewWaitUntilTerminated, ResultCode);
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

  // Kill any running TCP sessions before installing
  KillExistingTCP;

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
