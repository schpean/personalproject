# Use the official Python image as a parent image.
FROM python:3.9-slim-buster

# Set the working directory.
WORKDIR /app

# Copy the requirements file.
COPY requirements.txt .

# Install the dependencies.
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code.
COPY . .

# Set the environment variables.
ENV FLASK_APP=app.py
ENV FLASK_ENV=development

# Expose the port that the Flask app will listen on.
EXPOSE 5000

# Run the command to start the Flask app.
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
