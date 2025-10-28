# Installing Git for Windows

## Option 1: Download and Install Git (Recommended)
1. Go to: https://git-scm.com/download/win
2. Download the latest version (64-bit)
3. Run the installer with default settings
4. Restart PowerShell/terminal after installation

## Option 2: Use winget (if available)
Open PowerShell as Administrator and run:
```powershell
winget install --id Git.Git -e --source winget
```

## Option 3: Use Chocolatey (if installed)
```powershell
choco install git
```

After installation, close and reopen your terminal/PowerShell, then we'll continue with setting up the GitHub repository.

