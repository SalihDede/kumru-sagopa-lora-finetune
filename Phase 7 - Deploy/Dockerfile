# RunPod Serverless Dockerfile for Kumru-2B-Sagopa-Lora (LoRA Adapter)
FROM runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV TRANSFORMERS_CACHE=/app/cache
ENV HF_HOME=/app/cache
ENV BASE_MODEL=vngrs-ai/Kumru-2B
ENV LORA_ADAPTER=SalihHub/Kumru-2B-Sagopa-Lora

# Install Python dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy handler script
COPY handler.py /app/handler.py

# Pre-download models during build to speed up cold starts
RUN python -c "from transformers import AutoModelForCausalLM, AutoTokenizer; \
    print('Downloading base model...'); \
    AutoTokenizer.from_pretrained('vngrs-ai/Kumru-2B', trust_remote_code=True); \
    AutoModelForCausalLM.from_pretrained('vngrs-ai/Kumru-2B', trust_remote_code=True); \
    print('Downloading LoRA adapter...'); \
    AutoTokenizer.from_pretrained('SalihHub/Kumru-2B-Sagopa-Lora', trust_remote_code=True); \
    print('Models downloaded successfully!')"

# Run the handler
CMD ["python", "-u", "handler.py"]
