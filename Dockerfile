FROM python:3.9-slim-buster  # Or your preferred Python version and base image

# Update package lists
RUN apt-get update

# Install Java (OpenJDK 11 is a common and good choice)
RUN apt-get install -y default-jre  # Installs the default Java Runtime Environment (JRE)
# OR
# RUN apt-get install -y default-jdk # Installs the default Java Development Kit (JDK) - if you need JDK tools, though JRE is usually enough for running JARs

# Install any other dependencies your Python app needs (like LibreOffice if onenote2pdf needs it, though usually it's bundled)
# Example for LibreOffice (if needed, check onenote2pdf documentation):
# RUN apt-get install -y libreoffice

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Copy your application code
COPY . .

# Expose port (if your Flask app listens on a specific port, usually 5000)
EXPOSE 5000

# Command to run your Flask application
CMD ["python", "app.py"]