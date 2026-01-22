# Runpod Serverless Dockerfile for Sagopa Chatbot
# Base image with CUDA support
FROM runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04

# Set working directory
WORKDIR /workspace

# Install system dependencies and clean up
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    wget \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies with minimal cache
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    rm -rf /root/.cache/pip /tmp/*

# Copy the handler script
COPY handler.py .

# Model will be downloaded from Hugging Face Hub at runtime
# Set this environment variable to your HF model repo
ENV MODEL_NAME="SalihHub/kumru-sagopa-merged"

# Install huggingface-hub for downloading models at runtime
RUN pip install --no-cache-dir huggingface-hub

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV TRANSFORMERS_CACHE=/workspace/cache
ENV HF_HOME=/workspace/cache

# Create cache directory
RUN mkdir -p /workspace/cache

# Test the handler can import successfully
RUN python -c "import runpod; from transformers import AutoModelForCausalLM, AutoTokenizer; import torch; print('All imports successful!')"

# The CMD is handled by RunPod infrastructure
# It will automatically call: python -u handler.py
CMD ["python", "-u", "handler.py"]
