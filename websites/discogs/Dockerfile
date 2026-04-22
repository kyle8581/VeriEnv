FROM python:3.11-slim AS builder

# Install Node.js 22 + build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl gcc libffi-dev gnupg psmisc procps && \
    curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Port environment variables from ports.json
ENV BACKEND_PORT=12138 FRONTEND_PORT=12093

# Copy everything
COPY . .

# Pre-install Python deps into venvs
RUN python3 -m venv backend/.venv && \
    . backend/.venv/bin/activate && \
    pip install --upgrade pip && \
    pip install --no-cache-dir -r backend/requirements.txt
RUN python3 -m venv .venv && \
    . .venv/bin/activate && \
    pip install --upgrade pip && \
    pip install --no-cache-dir -r backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Pre-install Node deps
RUN cd frontend && (npm ci 2>/dev/null || npm install)

# Pre-build frontend (saves 60-180s at container startup)
RUN cd frontend && BACKEND_PORT=12138 FRONTEND_PORT=12093 npm run build || true

# Strip devDependencies (no longer needed after build)
RUN cd frontend && npm prune --omit=dev 2>/dev/null || true

# Clean build caches
RUN rm -rf ~/.npm /tmp/* ~/.cache /root/.cache
RUN chmod +x start_servers.sh

# ---- runtime stage (no build tools) ----
FROM python:3.11-slim

# Runtime deps only — no gcc, no libffi-dev, no gnupg
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl psmisc procps gnupg && \
    curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get install -y nodejs && \
    apt-get purge -y gnupg && apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

ENV BACKEND_PORT=12138 FRONTEND_PORT=12093

# Copy application from builder
COPY --from=builder /app /app

# Copy system Python packages (for scripts using system python directly)
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

EXPOSE 12093 12138

# start_servers.sh backgrounds servers then exits;
# sleep infinity keeps the container alive.
CMD ["bash", "-c", "./start_servers.sh && sleep infinity"]
