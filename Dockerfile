# Use an official lightweight Python image
FROM python:3.9

# Set the working directory
WORKDIR /app

# Copy the dependencies file and install them
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files
COPY . .

# Set environment variables
ENV PORT 8080
EXPOSE 8080

# Run the Flask app
CMD ["python", "main.py"]


