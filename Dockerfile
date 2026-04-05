# ── Bug Triage System — FINAL SUBMISSION ─────────────────────
FROM python:3.11-slim

WORKDIR /app

# Install system deps (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Set environment
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Expose API port
EXPOSE 8000

# Start FastAPI server (THIS IS THE IMPORTANT PART)
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]