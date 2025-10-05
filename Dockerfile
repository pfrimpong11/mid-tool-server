FROM python:3.13.3-slim

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create app directory and config directory
WORKDIR /app

COPY requirements.txt .

# Install the application dependencies.
RUN uv pip install --no-cache-dir -r requirements.txt --system --index-url https://download.pytorch.org/whl/cpu --extra-index-url https://pypi.org/simple

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# running migration file
RUN uv alembic upgrade head

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]