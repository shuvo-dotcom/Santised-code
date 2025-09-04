FROM python:3.10-slim

WORKDIR /app

# Copy requirements file and install dependencies
COPY deployment/backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the API code
COPY deployment/backend/api /app/api

# Create necessary directories
RUN mkdir -p data

# Set environment variables
ENV DATA_FOLDER=/app/data
ENV PORT=8000
ENV OPENAI_MODEL=gpt-5-mini
ENV PYTHONPATH=/app
# OPENAI_API_KEY will be passed from docker-compose

# Expose the port the app runs on
EXPOSE ${PORT}

# Command to run the application
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
