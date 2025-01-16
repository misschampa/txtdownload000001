# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the requirements file into the container at /usr/src/app
COPY requirements.txt ./

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the working directory contents into the container at /usr/src/app
COPY . .

# Make port 80 available to the world outside this container
EXPOSE 80

# Define environment variables
ENV API_ID=27536109
ENV API_HASH=b84d7d4dfa33904d36b85e1ead16bd63
ENV BOT_TOKEN=8161679463:AAHPJiQFPkBf-dZEJJOPO3EdiEyEUUYJ3t0

# Run main.py when the container launches
CMD ["python", "./main.py"]
