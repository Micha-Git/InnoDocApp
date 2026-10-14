# Builder stage with git to install dependencies from GitHub
FROM python:3.14-slim AS builder

WORKDIR /build

# Install git and build essentials
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies including those from GitHub
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .

# Runtime stage
FROM python:3.14-slim

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY main.py ./

EXPOSE 80

CMD ["python", "-u", "main.py"]
