FROM python:3.11-slim AS builder

# Install Node.js 22 + build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl gcc libffi-dev gnupg psmisc procps && \
    curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Port environment variables from ports.json
ENV API_PORT=12127 BACKEND_PORT=12127 FRONTEND_PORT=12125 PORT=12125 WEB_PORT=12125

# Copy everything
COPY . .

# Pre-install Python deps into venvs
RUN python3 -m venv backend/.venv && \
    . backend/.venv/bin/activate && \
    pip install --upgrade pip && \
    pip install --no-cache-dir -r backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Pre-install Node deps
RUN cd frontend && (npm ci 2>/dev/null || npm install)

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

ENV API_PORT=12127 BACKEND_PORT=12127 FRONTEND_PORT=12125 PORT=12125 WEB_PORT=12125

# Copy application from builder
COPY --from=builder /app /app

# Copy system Python packages (for scripts using system python directly)
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

EXPOSE 12125 12127

# start_servers.sh backgrounds servers then exits;
# sleep infinity keeps the container alive.
CMD ["bash", "-c", "./start_servers.sh && sleep infinity"]
