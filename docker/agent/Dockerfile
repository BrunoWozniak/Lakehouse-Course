FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for Dremio Flight
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY agent/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY agent/app.py .
COPY agent/chainlit.md .

# Expose Chainlit default port
EXPOSE 8501

# Run Chainlit
CMD ["chainlit", "run", "app.py", "--host", "0.0.0.0", "--port", "8501"]
