# Use the official Python image
FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# Copy requirements file and install dependencies
# COPY requirements.txt .
RUN pip install --no-cache-dir Flask mysql-connector-python Flask-Dance pycountry dotenv

# Copy the rest of the application code
COPY . .

# Expose the port Flask runs on
EXPOSE 5000

# Run the Flask app
CMD ["python", "app.py"]
