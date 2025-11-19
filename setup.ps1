# Quick setup script for WQAM Dashboard (PowerShell)
# Improved version with error handling and validation

param(
    [string]$AdminUsername = "admin",
    [string]$AdminPassword = "admin123",
    [switch]$SkipBuild = $false,
    [switch]$SkipAdmin = $false
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message, [string]$Color = "Cyan")
    Write-Host ""
    Write-Host $Message -ForegroundColor $Color
}

function Write-Success {
    param([string]$Message)
    Write-Host "[OK] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Gray
}

function Test-Command {
    param([string]$Command)
    $null = Get-Command $Command -ErrorAction SilentlyContinue
    return $?
}

function Invoke-DockerCommand {
    param(
        [string]$Command,
        [string]$Description
    )
    Write-Host "   $Description..." -ForegroundColor Gray
    $output = & docker-compose $Command.Split(' ') 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed: $Description"
        Write-Host $output -ForegroundColor Red
        throw "Docker command failed: $Command"
    }
    return $output
}

# Header
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  WQAM Dashboard Docker Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check prerequisites
Write-Step "[*] Checking prerequisites..."

if (-not (Test-Command "docker")) {
    Write-Error "Docker is not installed or not in PATH"
    Write-Host "Please install Docker Desktop from: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    exit 1
}
Write-Success "Docker found"

if (-not (Test-Command "docker-compose")) {
    Write-Error "Docker Compose is not installed or not in PATH"
    Write-Host "Docker Compose should be included with Docker Desktop" -ForegroundColor Yellow
    exit 1
}
Write-Success "Docker Compose found"

# Check if Docker is running
try {
    $null = docker info 2>&1
    Write-Success "Docker daemon is running"
} catch {
    Write-Error "Docker daemon is not running"
    Write-Host "Please start Docker Desktop and try again" -ForegroundColor Yellow
    exit 1
}

# Check if we're in the right directory
if (-not (Test-Path "docker-compose.yml")) {
    Write-Error "docker-compose.yml not found. Are you in the project root?"
    exit 1
}
Write-Success "Project structure verified"

# Create backend .env if it doesn't exist
Write-Step "[*] Setting up environment files..."

if (-not (Test-Path "backend\.env")) {
    Write-Host "   Creating backend/.env..." -ForegroundColor Yellow
    try {
        # Generate secure random secret key
        $secretKey = -join ((48..57) + (65..70) + (97..102) | Get-Random -Count 64 | ForEach-Object {[char]$_})
        $envContent = @"
DATABASE_URL=postgresql://wqam:wqam_pass@postgres:5432/wqamdb
SECRET_KEY=$secretKey
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
FRONTEND_URL=http://localhost:5173
REDIS_URL=redis://redis:6379/0
"@
        $envContent | Out-File -FilePath "backend\.env" -Encoding utf8
        Write-Success "Created backend/.env"
    } catch {
        Write-Error "Failed to create backend/.env: $_"
        exit 1
    }
} else {
    Write-Info "backend/.env already exists (skipping)"
}

# Create frontend .env if it doesn't exist
if (-not (Test-Path "frontend\.env")) {
    Write-Host "   Creating frontend/.env..." -ForegroundColor Yellow
    try {
        @"
VITE_API_URL=http://localhost:8000
"@ | Out-File -FilePath "frontend\.env" -Encoding utf8
        Write-Success "Created frontend/.env"
    } catch {
        Write-Error "Failed to create frontend/.env: $_"
        exit 1
    }
} else {
    Write-Info "frontend/.env already exists (skipping)"
}

# Check if ML model exists
Write-Step "[*] Checking ML model..."
if (Test-Path "ml\model\water_model.pkl") {
    Write-Success "ML model found at ml/model/water_model.pkl"
} else {
    Write-Warning "ML model not found at ml/model/water_model.pkl"
    Write-Info "The system will work but ML features will be disabled"
}

# Build Docker images
if (-not $SkipBuild) {
    Write-Step "[*] Building Docker images..."
    try {
        Invoke-DockerCommand "build" "Building containers" | Out-Null
        Write-Success "Docker images built successfully"
    } catch {
        Write-Error "Failed to build Docker images"
        Write-Host "Try running: docker-compose build --no-cache" -ForegroundColor Yellow
        exit 1
    }
} else {
    Write-Info "Skipping build (--SkipBuild flag set)"
}

# Start services
Write-Step "[*] Starting services..."
try {
    Invoke-DockerCommand "up -d" "Starting containers" | Out-Null
    Write-Success "Services started"
} catch {
    Write-Error "Failed to start services"
    Write-Host "Check logs with: docker-compose logs" -ForegroundColor Yellow
    exit 1
}

# Wait for services to be ready
Write-Step "[*] Waiting for services to initialize..."
$maxAttempts = 30
$attempt = 0
$backendReady = $false

while ($attempt -lt $maxAttempts -and -not $backendReady) {
    Start-Sleep -Seconds 2
    $attempt++
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/api/health" -TimeoutSec 2 -UseBasicParsing -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            $backendReady = $true
            Write-Success "Backend is ready"
        }
    } catch {
        Write-Host "   Waiting... ($attempt/$maxAttempts)" -ForegroundColor Gray
    }
}

if (-not $backendReady) {
    Write-Warning "Backend did not become ready in time, but continuing..."
    Write-Info "You can check status with: docker-compose ps"
}

# Create admin user
if (-not $SkipAdmin) {
    Write-Step "[*] Creating admin user..."
    try {
        $adminOutput = docker-compose exec -T backend python create_admin.py $AdminUsername $AdminPassword 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Admin user created successfully"
        } else {
            # Check if user already exists
            if ($adminOutput -match "already exists") {
                Write-Info "Admin user already exists (skipping)"
            } else {
                Write-Warning "Could not create admin user automatically"
                Write-Info "You can create it manually: docker-compose exec backend python create_admin.py $AdminUsername $AdminPassword"
            }
        }
    } catch {
        Write-Warning "Error creating admin user: $_"
        Write-Info "You can create it manually: docker-compose exec backend python create_admin.py $AdminUsername $AdminPassword"
    }
} else {
    Write-Info "Skipping admin creation (--SkipAdmin flag set)"
}

# Final summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  [OK] Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

Write-Step "[*] Access Points:" "Cyan"
Write-Host "   Frontend Dashboard: " -NoNewline -ForegroundColor White
Write-Host "http://localhost:5173" -ForegroundColor Cyan
Write-Host "   Backend API:         " -NoNewline -ForegroundColor White
Write-Host "http://localhost:8000" -ForegroundColor Cyan
Write-Host "   API Documentation:  " -NoNewline -ForegroundColor White
Write-Host "http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "   MinIO Console:      " -NoNewline -ForegroundColor White
Write-Host "http://localhost:9001" -ForegroundColor Cyan

Write-Host ""
Write-Step "[*] Login Credentials:" "Cyan"
Write-Host "   Username: " -NoNewline -ForegroundColor White
Write-Host $AdminUsername -ForegroundColor Yellow
Write-Host "   Password: " -NoNewline -ForegroundColor White
Write-Host $AdminPassword -ForegroundColor Yellow

Write-Host ""
Write-Step "[*] Useful Commands:" "Cyan"
Write-Host "   View logs:        " -NoNewline -ForegroundColor White
Write-Host "docker-compose logs -f" -ForegroundColor Gray
Write-Host "   View backend logs: " -NoNewline -ForegroundColor White
Write-Host "docker-compose logs -f backend" -ForegroundColor Gray
Write-Host "   Stop services:    " -NoNewline -ForegroundColor White
Write-Host "docker-compose down" -ForegroundColor Gray
Write-Host "   Restart service:  " -NoNewline -ForegroundColor White
Write-Host 'docker-compose restart <service>' -ForegroundColor Gray
Write-Host "   Check status:     " -NoNewline -ForegroundColor White
Write-Host "docker-compose ps" -ForegroundColor Gray

Write-Host ""
Write-Host "Happy Monitoring!" -ForegroundColor Green
Write-Host ""

