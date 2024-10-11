function global:prompt { $prompting = ""; $path = (Get-Location).Path.Replace($env:USERPROFILE, '~'); return "$prompting$path> "; } 
