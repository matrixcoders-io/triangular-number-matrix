# ─── Build stage ─────────────────────────────────────────────────────────────
# Use full Debian image — required for gmpy2 native compilation against libgmp
FROM python:3.11

# Install GMP and MPFR system libraries required by gmpy2
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgmp-dev \
    libmpfr-dev \
    libmpc-dev \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (cached layer — only re-runs if requirements.txt changes)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source (respects .dockerignore at build context root)
COPY . .

# Ensure output directories exist with correct ownership before volume mount
# Docker will overlay these with the PVC/bind mount at runtime, but pre-creating
# them guarantees the app can write even if no volume is attached (e.g. local test
# without docker-compose volume).
RUN mkdir -p \
    static/output/tn-files \
    static/output/we-files \
    static/output/stat-files

EXPOSE 5000

# 1 worker + 4 threads:
#   - Single worker process avoids file-write races on run_history.json / leaderboard.json
#   - 4 threads handle concurrent requests (I/O wait between gunicorn and Flask)
#   - Triangular number calculations are CPU-bound; GIL limits true thread parallelism
#     but concurrent researchers submitting jobs get queued gracefully
CMD ["gunicorn", \
     "--worker-class", "gthread", \
     "--workers", "1", \
     "--threads", "4", \
     "--bind", "0.0.0.0:5000", \
     "--timeout", "300", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "app:app"]
