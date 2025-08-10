# Use Python 3.12 slim base image
FROM python:3.12-slim

# Create a non-root user for security (required by Hugging Face)
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

# Set working directory
WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Copy dependency files first (for better Docker caching)
COPY --chown=user pyproject.toml uv.lock ./

# Install dependencies inside the container
RUN uv sync --no-cache

# Copy the rest of the project
COPY --chown=user . .

# Expose Hugging Face Space port
EXPOSE 7860

# Run the FastAPI app with uvicorn
CMD ["uv", "run", "uvicorn", "resume_parser_agent:app", "--host", "0.0.0.0", "--port", "7860"]