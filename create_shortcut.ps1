param(
    [string]$exePath = "$PSScriptRoot\dist\DocumentManagerApp.exe",
    [string]$shortcutName = "DocumentManagerApp",
    [string]$iconSource = ""
)

$exeFullPath = Resolve-Path -Path $exePath -ErrorAction Stop
$desktop = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktop "$shortcutName.lnk"
$iconLocation = "$exeFullPath,0"

if ($iconSource -ne "") {
    $iconSourcePath = Resolve-Path -Path $iconSource -ErrorAction Stop
    $iconExt = [System.IO.Path]::GetExtension($iconSourcePath).ToLowerInvariant()
    if ($iconExt -eq ".ico") {
        $iconLocation = "$iconSourcePath,0"
    } else {
        Add-Type -AssemblyName System.Drawing
        $bitmap = [System.Drawing.Bitmap]::FromFile($iconSourcePath)
        $iconFile = Join-Path (Split-Path $exeFullPath) "$shortcutName.ico"
        $hIcon = $bitmap.GetHicon()
        $icon = [System.Drawing.Icon]::FromHandle($hIcon)
        $fs = New-Object System.IO.FileStream($iconFile, [System.IO.FileMode]::Create)
        $icon.Save($fs)
        $fs.Close()
        $iconLocation = "$iconFile,0"
    }
}

$wshShell = New-Object -ComObject WScript.Shell
$shortcut = $wshShell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $exeFullPath
$shortcut.WorkingDirectory = Split-Path $exeFullPath
$shortcut.IconLocation = $iconLocation
$shortcut.Save()

Write-Host "Shortcut created:" $shortcutPath
if ($iconSource -ne "" -and $iconExt -ne ".ico") {
    Write-Host "Generated icon file:" $iconFile
}
