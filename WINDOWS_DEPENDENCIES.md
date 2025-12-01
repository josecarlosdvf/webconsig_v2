# Windows System Dependencies

Installed via winget/Scoop on 2025-12-01 07:27

## Poppler (pdftoppm)
- Installed via: winget
- Path: C:\Users\Develop\AppData\Local\Microsoft\WinGet\Packages\oschwartz10612.Poppler_Microsoft.Winget.Source_8wekyb3d8bbwe\poppler-25.07.0\Library\bin
- Verify: pdftoppm -v
- Version: 25.07.0

## ImageMagick
- Installed via: winget
- Path: C:\Program Files\ImageMagick-7.1.2-Q16-HDRI
- Verify: magick -version
- Version: 7.1.2-9 Q16-HDRI x64

## Ghostscript
- Installed via: Scoop
- Path: C:\Users\Develop\scoop\shims\gswin64c.exe
- Verify: gswin64c --version
- Version: 10.06.0

## Add to PATH (current session only)
`powershell
$env:Path += ';C:\Users\Develop\AppData\Local\Microsoft\WinGet\Packages\oschwartz10612.Poppler_Microsoft.Winget.Source_8wekyb3d8bbwe\poppler-25.07.0\Library\bin'
$env:Path += ';C:\Program Files\ImageMagick-7.1.2-Q16-HDRI'
# Scoop automatically adds its shims to PATH
`

## Permanent PATH (user-level)
Use PowerShell:
`powershell
[Environment]::SetEnvironmentVariable('Path', $env:Path, 'User')
`
Or manually add in System Properties > Environment Variables.
