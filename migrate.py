#!/usr/bin/env python3
"""
Database migration management CLI
"""
import os
import sys
import subprocess
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def run_command(command):
    """Run a shell command and return the result"""
    try:
        result = subprocess.run(command, shell=True, cwd=project_root, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running command: {e}", file=sys.stderr)
        return False

def create_migration(message="Auto migration"):
    """Create a new migration file"""
    print(f"Creating migration: {message}")
    command = f'alembic revision --autogenerate -m "{message}"'
    return run_command(command)

def run_migrations():
    """Run all pending migrations"""
    print("Running migrations...")
    command = "alembic upgrade head"
    return run_command(command)

def rollback_migration(revision=""):
    """Rollback to a specific revision or one step back"""
    if revision:
        print(f"Rolling back to revision: {revision}")
        command = f"alembic downgrade {revision}"
    else:
        print("Rolling back one migration...")
        command = "alembic downgrade -1"
    return run_command(command)

def show_migration_status():
    """Show current migration status"""
    print("Migration status:")
    command = "alembic current"
    run_command(command)
    
    print("\nMigration history:")
    command = "alembic history"
    run_command(command)

def show_help():
    """Show help information"""
    help_text = """
Database Migration Management CLI

Usage:
    python migrate.py <command> [args]

Commands:
    create <message>    Create a new migration file with optional message
    migrate            Run all pending migrations
    rollback [rev]     Rollback migrations (to specific revision or one step back)
    status             Show current migration status and history
    help               Show this help message

Examples:
    python migrate.py create "Add user table"
    python migrate.py migrate
    python migrate.py rollback
    python migrate.py rollback base
    python migrate.py status
"""
    print(help_text)

def main():
    """Main CLI entry point"""
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    if command == "create":
        message = sys.argv[2] if len(sys.argv) > 2 else "Auto migration"
        success = create_migration(message)
        if not success:
            sys.exit(1)
    
    elif command == "migrate":
        success = run_migrations()
        if not success:
            sys.exit(1)
    
    elif command == "rollback":
        revision = sys.argv[2] if len(sys.argv) > 2 else ""
        success = rollback_migration(revision)
        if not success:
            sys.exit(1)
    
    elif command == "status":
        show_migration_status()
    
    elif command == "help":
        show_help()
    
    else:
        print(f"Unknown command: {command}")
        show_help()
        sys.exit(1)

if __name__ == "__main__":
    main()