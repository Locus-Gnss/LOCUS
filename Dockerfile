# LOCUS Cyber-Physical GNSS SOC — Production Unified Container
# Target Deployment: Docker / Cloud Run / Kubernetes / Render
FROM python:3.11-slim

# Prevent bytecode caching and enable unbuffered output
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8501 \
    LOCUS_API_PORT=8000

WORKDIR /app

# Install system dependencies (curl for healthchecks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install application dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application configuration and source code
COPY .streamlit/ .streamlit/
COPY configs/ configs/
COPY data/ data/
COPY models/ models/
COPY src/ src/
COPY scripts/ scripts/
COPY dashboard.py .

# Expose ports for both GUI and FastAPI backend
EXPOSE 8501
EXPOSE 8000

# Health check probe against both FastAPI and Streamlit endpoints
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request, os; \
p = os.getenv('PORT', '8501'); \
ap = os.getenv('LOCUS_API_PORT', '8000'); \
urllib.request.urlopen(f'http://127.0.0.1:{ap}/api/health'); \
urllib.request.urlopen(f'http://127.0.0.1:{p}/_stcore/health')" || exit 1

# Launch unified orchestration runner (FastAPI + Streamlit GUI)
ENTRYPOINT ["python", "scripts/run_container.py"]
