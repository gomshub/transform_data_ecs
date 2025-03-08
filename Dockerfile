# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port your app will run on
EXPOSE 5000

# Define environment variable for Flask app
ENV FLASK_APP=main.py

# Run the Flask application
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
