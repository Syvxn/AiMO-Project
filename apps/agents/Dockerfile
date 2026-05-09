FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install build tools for native extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml /app/pyproject.toml
COPY requirements.txt /app/requirements.txt
# README is required by setuptools for the editable install metadata
COPY README.md /app/README.md

# Copy src before installing so setuptools can find the package
COPY src /app/src

# Install the package and its ML dependencies
RUN pip install --no-cache-dir -e ".[dev]"
RUN pip install --no-cache-dir fastapi uvicorn[standard] httpx

COPY data /app/data

EXPOSE 8001

CMD ["uvicorn", "aimo_agents.server:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]
