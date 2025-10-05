# Database Migration Management Script for Windows PowerShell
param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$Command,
    
    [Parameter(Position=1)]
    [string]$Message = "Auto migration"
)

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

function Invoke-AlembicCommand {
    param([string]$AlembicCommand)
    
    try {
        Write-Host "Executing: $AlembicCommand" -ForegroundColor Yellow
        Invoke-Expression $AlembicCommand
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Command completed successfully." -ForegroundColor Green
            return $true
        } else {
            Write-Host "Command failed with exit code: $LASTEXITCODE" -ForegroundColor Red
            return $false
        }
    }
    catch {
        Write-Host "Error executing command: $_" -ForegroundColor Red
        return $false
    }
}

switch ($Command.ToLower()) {
    "create" {
        Write-Host "Creating migration: $Message" -ForegroundColor Cyan
        $success = Invoke-AlembicCommand "alembic revision --autogenerate -m `"$Message`""
        if (-not $success) { exit 1 }
    }
    
    "migrate" {
        Write-Host "Running migrations..." -ForegroundColor Cyan
        $success = Invoke-AlembicCommand "alembic upgrade head"
        if (-not $success) { exit 1 }
    }
    
    "rollback" {
        if ($Message -and $Message -ne "Auto migration") {
            Write-Host "Rolling back to revision: $Message" -ForegroundColor Cyan
            $success = Invoke-AlembicCommand "alembic downgrade $Message"
        } else {
            Write-Host "Rolling back one migration..." -ForegroundColor Cyan
            $success = Invoke-AlembicCommand "alembic downgrade -1"
        }
        if (-not $success) { exit 1 }
    }
    
    "status" {
        Write-Host "Migration status:" -ForegroundColor Cyan
        Invoke-AlembicCommand "alembic current"
        Write-Host "`nMigration history:" -ForegroundColor Cyan
        Invoke-AlembicCommand "alembic history"
    }
    
    "help" {
        Write-Host @"
Database Migration Management Script

Usage:
    .\migrate.ps1 <command> [args]

Commands:
    create <message>    Create a new migration file with optional message
    migrate            Run all pending migrations
    rollback [rev]     Rollback migrations (to specific revision or one step back)
    status             Show current migration status and history
    help               Show this help message

Examples:
    .\migrate.ps1 create "Add user table"
    .\migrate.ps1 migrate
    .\migrate.ps1 rollback
    .\migrate.ps1 rollback base
    .\migrate.ps1 status
"@ -ForegroundColor White
    }
    
    default {
        Write-Host "Unknown command: $Command" -ForegroundColor Red
        Write-Host "Use '.\migrate.ps1 help' to see available commands." -ForegroundColor Yellow
        exit 1
    }
}