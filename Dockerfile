# LOCUS Cyber-Physical GNSS SOC — Streamlit Dashboard Container
# Target Deployment: Google Cloud Run / Docker Container Runtime
FROM python:3.11-slim

# Enforce clean unbuffered output and prevent bytecode caching
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080 \
    LOCUS_API_URL=https://locus-5b9g.onrender.com

WORKDIR /app

# Install thin-client frontend dependencies (no heavy backend ML frameworks)
COPY requirements-gui.txt .
RUN pip install --no-cache-dir -r requirements-gui.txt

# Copy application configuration and source code (thin client only)
COPY .streamlit/ .streamlit/
COPY dashboard.py .
COPY src/ui/ src/ui/
COPY configs/ configs/

# Expose Cloud Run default port
EXPOSE 8080

# Health check probe using Streamlit's native health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request, os; p = os.getenv('PORT', '8080'); urllib.request.urlopen(f'http://127.0.0.1:{p}/_stcore/health')" || exit 1

# Launch Streamlit with exec so SIGTERM is cleanly handled by the main process
ENTRYPOINT ["sh", "-c", "exec streamlit run dashboard.py --server.address 0.0.0.0 --server.port ${PORT:-8080} --browser.gatherUsageStats false"]
