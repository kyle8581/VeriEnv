FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends gcc libffi-dev curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .
RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi
RUN if [ -f backend/requirements.txt ]; then pip install --no-cache-dir -r backend/requirements.txt; fi

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
