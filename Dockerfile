FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
	git \
	&& rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt && \
	pip install --no-cache-dir cvxpy jupyter

# Copy source code
COPY . .

# Install package in development mode
RUN pip install -e .

# Expose Jupyter port
EXPOSE 8888

# Default command: run tests
CMD ["pytest", "tests/", "-v"]
