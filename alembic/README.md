# Database Migration Guide

This directory contains Alembic database migrations for the Medical Image Diagnostics API. Alembic is a database migration tool that helps manage database schema changes over time.

## 📁 Directory Structure

```
alembic/
├── README.md                     # This file
├── env.py                        # Alembic environment configuration
├── script.py.mako               # Template for new migration files
└── versions/                     # Migration files directory
    ├── a9ef987fd631_create_user_table.py
    ├── f8ff2ab1fdfa_add_phone_number_to_user_table.py
    └── [future migrations...]
```

## 🚀 Quick Start

### Prerequisites
- PostgreSQL database running and accessible
- Environment variables configured in `.env` file
- Virtual environment activated

### Basic Commands

```bash
# Check current migration status
python migrate.py status

# Create a new migration (auto-detect changes)
python migrate.py create "Description of changes"

# Apply all pending migrations
python migrate.py migrate

# Rollback one migration
python migrate.py rollback

# Rollback to specific revision
python migrate.py rollback <revision_id>

# Rollback all migrations
python migrate.py rollback base
```

## 📝 Migration Workflow

### 1. Making Model Changes

When you need to modify the database schema:

1. **Edit your model files** in `app/models/`
   ```python
   # Example: Adding a new field to User model
   class User(Base):
       # ... existing fields
       phone_number = Column(String(20), nullable=True)  # New field
   ```

2. **Generate migration automatically**
   ```bash
   python migrate.py create "Add phone number to user table"
   ```

3. **Review the generated migration**
   - Check the migration file in `alembic/versions/`
   - Ensure the `upgrade()` and `downgrade()` functions are correct
   - Make manual adjustments if needed

4. **Apply the migration**
   ```bash
   python migrate.py migrate
   ```

### 2. Migration File Structure

Each migration file contains:

```python
"""Migration description

Revision ID: f8ff2ab1fdfa
Revises: a9ef987fd631
Create Date: 2025-09-16 18:49:48.928600
"""

# revision identifiers
revision: str = 'f8ff2ab1fdfa'
down_revision: Union[str, None] = 'a9ef987fd631'

def upgrade() -> None:
    """Apply changes to move forward"""
    op.add_column('users', sa.Column('phone_number', sa.String(length=20), nullable=True))

def downgrade() -> None:
    """Undo changes to move backward"""
    op.drop_column('users', 'phone_number')
```

## 🔄 Migration Types

### Automatic Detection
Alembic automatically detects:
- ✅ New tables and columns
- ✅ Dropped tables and columns
- ✅ Column type changes
- ✅ Index and constraint changes
- ✅ Foreign key relationships

### Manual Migrations
For complex changes that require custom logic:

```bash
# Create empty migration for manual editing
alembic revision -m "Custom data migration"
```

Then edit the generated file to include custom SQL or Python code.

## 🏗️ Common Migration Operations

### Adding a Column
```python
def upgrade():
    op.add_column('users', sa.Column('age', sa.Integer, nullable=True))

def downgrade():
    op.drop_column('users', 'age')
```

### Creating a Table
```python
def upgrade():
    op.create_table('posts',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'))
    )

def downgrade():
    op.drop_table('posts')
```

### Adding an Index
```python
def upgrade():
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

def downgrade():
    op.drop_index('ix_users_email', table_name='users')
```

### Data Migration
```python
def upgrade():
    # Schema change
    op.add_column('users', sa.Column('full_name', sa.String(255)))
    
    # Data migration
    connection = op.get_bind()
    connection.execute(
        "UPDATE users SET full_name = first_name || ' ' || last_name"
    )

def downgrade():
    op.drop_column('users', 'full_name')
```

## 🚨 Best Practices

### Development Workflow
1. **Always backup** your database before running migrations
2. **Test migrations** on a copy of production data
3. **Review generated migrations** before applying
4. **Use descriptive messages** for migration descriptions
5. **Keep migrations small** and focused on single changes

### Production Deployment
1. **Run migrations during maintenance windows**
2. **Have rollback plan ready**
3. **Monitor application after deployment**
4. **Test on staging environment first**

### Writing Good Migrations
```python
# ✅ Good: Descriptive and specific
python migrate.py create "Add phone_number field to user table"

# ❌ Bad: Vague and unclear
python migrate.py create "Update users"
```

## 🔧 Configuration

### Environment Setup
Migration behavior is controlled by:
- **`.env` file**: Database connection settings
- **`alembic.ini`**: Alembic configuration
- **`alembic/env.py`**: Runtime environment setup

### Database Connection
The system automatically uses the correct database based on your `.env` settings:

```bash
# PostgreSQL (Production)
USE_SQLITE=False
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DB=medical_image_diagnostics

# SQLite (Development)
USE_SQLITE=True
```

## 📊 Migration History

### Viewing Migration Status
```bash
# Current migration
python migrate.py status

# Full history
alembic history --verbose

# Show current head
alembic current
```

### Migration Chain
Migrations form a linear chain:
```
base → a9ef987fd631 → f8ff2ab1fdfa → [next migration]
       (create users)  (add phone)     (future changes)
```

## 🚨 Troubleshooting

### Common Issues

**Migration conflicts:**
```bash
# If you have conflicting migrations
alembic merge heads -m "Merge conflicting migrations"
```

**Reset to clean state:**
```bash
# Rollback all migrations
python migrate.py rollback base

# Re-apply all migrations
python migrate.py migrate
```

**Manual intervention needed:**
```bash
# Mark specific revision as current without running it
alembic stamp <revision_id>
```

### Error Recovery

1. **Check database connection** first
2. **Verify `.env` configuration**
3. **Check PostgreSQL is running**
4. **Review migration file** for syntax errors
5. **Check for data conflicts** (unique constraints, etc.)

## 🌐 Multi-Environment Setup

### Development
- Use SQLite for quick local development
- Run migrations frequently during development

### Staging
- Mirror production database structure
- Test migrations before production deployment

### Production
- Schedule migrations during maintenance windows
- Always have database backups
- Monitor for performance impact

## 📚 Additional Resources

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

## 🆘 Support

For migration issues:
1. Check this README first
2. Review the migration file that's causing issues
3. Check database logs for detailed error messages
4. Ensure all environment variables are correctly set

---

*Last updated: September 16, 2025*