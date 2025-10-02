# Start from a lightweight Python image
FROM python:3.11-slim

# Set working directory in container
WORKDIR /app

# Copy project files into container
COPY . /app

# Install dependencies (if you have requirements.txt)
RUN pip install --no-cache-dir -r requirements.txt

# Default command to run your app
CMD ["python", "main.py"]
