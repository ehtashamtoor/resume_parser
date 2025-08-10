# Use Python 3.12 slim base image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Copy dependency files first 
COPY pyproject.toml uv.lock ./

# Install dependencies inside the container
RUN uv sync --no-cache

# Copy the rest of the project
COPY . .

# Expose FastAPI port
EXPOSE 7860
# EXPOSE 8000

# Run the app using uv
CMD ["uv", "run", "python", "main.py"]
