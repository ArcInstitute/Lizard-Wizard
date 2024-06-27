# Use an official Python runtime as a base image
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    software-properties-common \
    build-essential \
    libpq-dev \
    curl \
    less \
    tree \
    screen \
    vim \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements.txt file into the container
COPY requirements.txt .

# Install Python dependencies
RUN pip3 install -r requirements.txt


