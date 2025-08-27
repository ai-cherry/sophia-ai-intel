# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

# Copy the rest of the application's code
COPY ./src /app/src

# Make port 80 available to the world outside this container
EXPOSE 80

# Run the application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "80"]