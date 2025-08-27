# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy the dependency files to the container
COPY pyproject.toml poetry.lock ./

# Install project dependencies
RUN poetry config virtualenvs.create false && poetry install --no-root --no-dev

# Copy the application code to the container
COPY ./agentic ./agentic

# Expose port 8000 for the uvicorn server
EXPOSE 8000

# Run the application
CMD ["poetry", "run", "uvicorn", "agentic.api:app", "--host", "0.0.0.0", "--port", "8000"]