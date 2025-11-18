param(
    [int]$Users = 100,
    [int]$Uploads = 500,
    [int]$Days = 90,
    [string]$OutDir = ".\sample_data"
)

# Ensure output directory
if (-not (Test-Path $OutDir)) {
    New-Item -ItemType Directory -Path $OutDir | Out-Null
}

Write-Host "Generating sample data..." -ForegroundColor Cyan

# --- USERS ---
$users = @()
for ($i = 1; $i -le $Users; $i++) {
    $users += [PSCustomObject]@{
        user_id     = "U$i"
        name        = "User_$i"
        org_id      = "O$((Get-Random -Minimum 1 -Maximum 10))"
        role        = (Get-Random @("Admin", "Viewer", "Validator", "Analyst"))
        created_at  = (Get-Date).AddDays(-1 * (Get-Random -Minimum 1 -Maximum $Days))
    }
}
$users | Export-Csv "$OutDir/users.csv" -NoTypeInformation

# --- ORGANIZATIONS ---
$orgs = 1..10 | ForEach-Object {
    [PSCustomObject]@{
        org_id   = "O$_"
        org_name = "Organization_$_"
        region   = (Get-Random @("NA", "EU", "ASIA", "SA"))
    }
}
$orgs | Export-Csv "$OutDir/orgs.csv" -NoTypeInformation

# --- UPLOADS ---
$uploads = @()
for ($i = 1; $i -le $Uploads; $i++) {
    $uploads += [PSCustomObject]@{
        upload_id   = "UP$i"
        user_id     = "U$((Get-Random -Minimum 1 -Maximum $Users))"
        timestamp   = (Get-Date).AddMinutes(-1 * (Get-Random -Minimum 1 -Maximum ($Days * 1440)))
        size_kb     = [math]::Round((Get-Random -Minimum 100 -Maximum 5000), 2)
        status      = (Get-Random @("Pending", "Validated", "Failed"))
    }
}
$uploads | Export-Csv "$OutDir/uploads.csv" -NoTypeInformation

# --- KPI SUMMARY ---
$kpi = @{
    active_users = (Get-Random -Minimum 50 -Maximum $Users)
    total_uploads = $Uploads
    avg_size_kb = [math]::Round(($uploads.size_kb | Measure-Object -Average).Average, 2)
    success_rate = [math]::Round((($uploads | Where-Object {$_.status -eq "Validated"}).Count / $Uploads * 100), 2)
}
$kpi | ConvertTo-Json | Out-File "$OutDir/kpi_summary.json"

# --- TIMESERIES KPI ---
$timeSeries = @()
for ($d = $Days; $d -ge 0; $d--) {
    $date = (Get-Date).AddDays(-$d).ToString("yyyy-MM-dd")
    $value = [math]::Round((Get-Random -Minimum 10 -Maximum ($Users * 0.5)), 0)
    $timeSeries += [PSCustomObject]@{
        date = $date
        active_users = $value
        uploads = [math]::Round((Get-Random -Minimum 0 -Maximum $Uploads / $Days), 0)
    }
}
$timeSeries | Export-Csv "$OutDir/timeseries_kpi.csv" -NoTypeInformation

# --- PARAMETERS ---
$parameters = @(
    @{ param = "Temperature"; unit = "°C" },
    @{ param = "Pressure"; unit = "bar" },
    @{ param = "Humidity"; unit = "%" }
)
$parameters | ConvertTo-Json -Depth 2 | Out-File "$OutDir/parameters.json"

# --- VALIDATORS ---
$validators = 1..20 | ForEach-Object {
    [PSCustomObject]@{
        validator_id = "V$_"
        org_id = "O$((Get-Random -Minimum 1 -Maximum 10))"
        status = (Get-Random @("Online", "Offline", "Busy"))
    }
}
$validators | Export-Csv "$OutDir/validators.csv" -NoTypeInformation

# --- ALERTS ---
$alerts = 1..50 | ForEach-Object {
    [PSCustomObject]@{
        alert_id = "AL$_"
        type = (Get-Random @("Error", "Threshold", "System", "Validation"))
        message = "Random alert $_"
        created_at = (Get-Date).AddMinutes(-1 * (Get-Random -Minimum 1 -Maximum ($Days * 1440)))
        severity = (Get-Random @("Low", "Medium", "High"))
    }
}
$alerts | Export-Csv "$OutDir/alerts.csv" -NoTypeInformation

Write-Host "✅ Sample dataset generated successfully in $OutDir" -ForegroundColor Green
