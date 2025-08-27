# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the dependency definitions
COPY pyproject.toml ./

# Install pip and poetry, then install dependencies
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev --no-interaction --no-ansi

# Copy the rest of the application code
COPY . .

# Command to run the application
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "80"]