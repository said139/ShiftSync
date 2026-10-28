$pw = Read-Host "Enter POSTGRES_PASSWORD (typing hidden)" -AsSecureString
$plain = [Net.NetworkCredential]::new("", $pw).Password
Set-Content -Path "C:\Users\saidm\Desktop\SHIFTSYNC\.env" -Value "POSTGRES_PASSWORD=$plain"
Write-Host "Saved to C:\Users\saidm\Desktop\SHIFTSYNC\.env" -ForegroundColor Green
