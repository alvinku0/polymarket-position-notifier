# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies and uv
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && curl -LsSf https://astral.sh/uv/install.sh | sh

# Add uv to PATH
ENV PATH="/root/.local/bin:$PATH"

# Copy dependency files first for better layer caching
COPY pyproject.toml uv.lock ./

# Install Python dependencies using uv
RUN /root/.local/bin/uv sync --frozen

# Copy application code
COPY . .

# Create log directory and set up user
RUN mkdir -p /app/log && \
    useradd --create-home --shell /bin/bash --uid 1000 appuser && \
    chown -R appuser:appuser /app && \
    chmod -R 755 /app

# Copy uv binary for user access
RUN cp /root/.local/bin/uv /usr/local/bin/uv && \
    chmod +x /usr/local/bin/uv

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PATH="/usr/local/bin:$PATH"

# Switch user
USER appuser

# Default command
CMD ["uv", "run", "python", "main.py"]