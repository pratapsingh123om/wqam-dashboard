Write-Host "=== FIXING FRONTEND ERRORS ==="

$frontendPath = "frontend\src"

# 1. Fix React imports (missing import React, useState, useEffect)
Get-ChildItem -Path $frontendPath -Recurse -Include *.tsx | ForEach-Object {
    (Get-Content $_.FullName) |
        ForEach-Object {
            if ($_ -match "useState|useEffect" -and $_ -notmatch "import { useState") {
                "import React, { useState, useEffect } from 'react';"
            }
            elseif ($_ -match "^import React" -and $_ -match "never read") {
                # remove unused React import
                ""
            }
            else { $_ }
        } | Set-Content $_.FullName
}

Write-Host "[1] React imports fixed."

# 2. Fix main.tsx complaining about React UMD global
$main = "$frontendPath\main.tsx"
if (Test-Path $main) {
    (Get-Content $main) |
        ForEach-Object {
            $_ -replace "ReactDOM\.createRoot", "ReactDOM.createRoot"
        } | Set-Content $main
}

Write-Host "[2] main.tsx React module fix applied."

# 3. Fix MapView.tsx – bad cleanup return type & remove require()
$mapview = "$frontendPath\components\MapView.tsx"
if (Test-Path $mapview) {
    $content = Get-Content $mapview

    # remove require()
    $content = $content -replace "require\(.*\)", ""

    # fix cleanup return type
    $content = $content -replace "return \(\) => L\.Map", "return () => {}"

    Set-Content $mapview $content
}

Write-Host "[3] MapView fixes applied."

# 4. Fix wrong imports in services/api and Dashboard
$api = "$frontendPath\services\api.ts"
if (Test-Path $api) {
    (Get-Content $api) |
        ForEach-Object {
            $_ -replace "export const apiFetch", "export default function apiFetch"
        } | Set-Content $api
}

Write-Host "[4] API service fixed."

$dashboard = "$frontendPath\pages\Dashboard.tsx"
if (Test-Path $dashboard) {
    (Get-Content $dashboard) |
        ForEach-Object {
            $_ -replace "import { fetchDemo } from '../services/api'", "import fetchDemo from '../services/api'"
        } | Set-Content $dashboard
}

Write-Host "[5] Dashboard import fixed."

# 5. Install missing Node types
Write-Host "[6] Installing @types/node..."
npm --prefix frontend install --save-dev @types/node

Write-Host "=== FIX COMPLETED SUCCESSFULLY ==="
Write-Host "Now run:"
Write-Host "  docker compose build --no-cache"
Write-Host "  docker compose up -d"
