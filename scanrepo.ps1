Write-Host ""
Write-Host "========================================="
Write-Host "     WQAM REPO DIAGNOSTIC SCANNER        "
Write-Host "========================================="
Write-Host ""

$root = Get-Location
Write-Host "Scanning repo at: $root"
Write-Host ""

# ---------------------------------------
# 1. Detect missing imports in frontend
# ---------------------------------------
Write-Host "→ Checking for broken imports in TS/TSX..."
$tsFiles = Get-ChildItem -Recurse -Include *.ts, *.tsx | Where-Object { $_.FullName -notmatch "node_modules" }

$brokenImports = @()

foreach ($file in $tsFiles) {
    $content = Get-Content $file.FullName
    foreach ($line in $content) {
        if ($line -match "import\s+\{(.+?)\}\s+from\s+['""](.+?)['""]") {
            $importName = $matches[1].Trim()
            $importSource = $matches[2].Trim()

            # Skip library imports
            if ($importSource -notmatch "^\." ) { continue }

            $targetPath = Join-Path $file.Directory.FullName "$importSource.ts"
            $targetPath2 = Join-Path $file.Directory.FullName "$importSource.tsx"
            $targetPath3 = Join-Path $file.Directory.FullName "$importSource/index.ts"
            $targetPath4 = Join-Path $file.Directory.FullName "$importSource/index.tsx"

            if (!(Test-Path $targetPath -or Test-Path $targetPath2 -or Test-Path $targetPath3 -or Test-Path $targetPath4)) {
                $brokenImports += "❌ $($file.Name) → import {$importName} from '$importSource'"
            }
        }
    }
}

if ($brokenImports.Count -eq 0) {
    Write-Host "   ✔ No broken imports found."
} else {
    Write-Host "   ⚠ Found broken imports:"
    $brokenImports | ForEach-Object { Write-Host "     $_" }
}

Write-Host ""

# ---------------------------------------
# 2. Detect API functions used but missing
# ---------------------------------------
Write-Host "→ Checking API calls..."

$apiFile = "$root\frontend\src\services\api.ts"
$apiFunctions = @()

if (Test-Path $apiFile) {
    $apiContent = Get-Content $apiFile
    foreach ($line in $apiContent) {
        if ($line -match "export\s+async\s+function\s+([a-zA-Z0-9_]+)") {
            $apiFunctions += $matches[1]
        }
    }
}

$usedFunctions = @()

foreach ($file in $tsFiles) {
    $content = Get-Content $file.FullName
    foreach ($line in $content) {
        if ($line -match "(\w+)\(") {
            $func = $matches[1]
            if ($func -match "fetch|get|post|login|register|create|update") {
                $usedFunctions += $func
            }
        }
    }
}

$usedFunctions = $usedFunctions | Sort-Object -Unique

$missing = @()

foreach ($func in $usedFunctions) {
    if ($apiFunctions -notcontains $func) {
        $missing += "❌ Missing API function: $func()"
    }
}

if ($missing.Count -eq 0) {
    Write-Host "   ✔ All API functions exist."
} else {
    Write-Host "   ⚠ Missing API functions:"
    $missing | ForEach-Object { Write-Host "     $_" }
}

Write-Host ""


# ---------------------------------------
# 3. Check Dockerfile references
# ---------------------------------------
Write-Host "→ Checking Dockerfiles..."

$dockerfiles = Get-ChildItem -Recurse -Include Dockerfile

foreach ($df in $dockerfiles) {
    $content = Get-Content $df.FullName | Out-String
    Write-Host "   Checking: $df"

    if ($content -match "COPY\s+frontend/") {
        Write-Host "     ❌ ERROR: This Dockerfile incorrectly references 'COPY frontend/'."
    }

    if ($content -match "npm run dev") {
        Write-Host "     ⚠ Dev server used. Production build missing."
    }
}

Write-Host ""


# ---------------------------------------
# 4. ENV file consistency
# ---------------------------------------
Write-Host "→ Checking environment variables..."

$frontendEnv = "$root\frontend\.env"
$backendEnv = "$root\backend\.env"

if (Test-Path $frontendEnv) {
    Write-Host "   Frontend ENV:"
    Get-Content $frontendEnv | ForEach-Object { Write-Host "     $_" }
}

if (Test-Path $backendEnv) {
    Write-Host ""
    Write-Host "   Backend ENV:"
    Get-Content $backendEnv | ForEach-Object { Write-Host "     $_" }
}

Write-Host ""
Write-Host "========================================="
Write-Host "           SCAN COMPLETED"
Write-Host "========================================="
