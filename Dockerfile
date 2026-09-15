# Use a lightweight Python image
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy simulator application code
COPY simulator.py .

# Create certs directory as mount point for runtime certificate injection
RUN mkdir -p /app/certs

# Run the simulator
CMD ["python", "simulator.py"]