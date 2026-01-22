"""
Runpod Serverless Handler for Sagopa Chatbot
This handler provides an API endpoint for the fine-tuned LLM model
"""

import runpod
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import os

# Global variables for model and tokenizer
model = None
tokenizer = None

def load_model():
    """Load the model and tokenizer into memory"""
    global model, tokenizer

    if model is None or tokenizer is None:
        print("Loading model and tokenizer...")

        # Try local path first, then download from HF if needed
        model_path = "/workspace/kumru-sagopa-merged"

        # If model not found locally, download from Hugging Face
        if not os.path.exists(os.path.join(model_path, "config.json")):
            print("Model not found locally, downloading from Hugging Face...")
            from huggingface_hub import snapshot_download
            hf_model_name = os.environ.get("MODEL_NAME", "SalihHub/kumru-sagopa-merged")
            print(f"Downloading model: {hf_model_name}")
            model_path = snapshot_download(
                repo_id=hf_model_name,
                local_dir=model_path,
                local_dir_use_symlinks=False
            )
            print(f"Model downloaded to {model_path}")

        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(model_path)

        # Load model with GPU support
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto",
            low_cpu_mem_usage=True
        )

        print("Model loaded successfully!")
        if torch.cuda.is_available():
            print(f"Using GPU: {torch.cuda.get_device_name(0)}")
        else:
            print("Using CPU")

    return model, tokenizer

def handler(job):
    """
    RunPod serverless handler function

    Expected input format:
    {
        "input": {
            "prompt": "User message here",
            "messages": [optional conversation history],
            "max_new_tokens": 128,
            "temperature": 0.7,
            "do_sample": true
        }
    }
    """
    try:
        # Get job input
        job_input = job.get('input', {})

        # Extract parameters
        user_prompt = job_input.get('prompt', '')
        messages = job_input.get('messages', [])
        max_new_tokens = job_input.get('max_new_tokens', 128)
        temperature = job_input.get('temperature', 0.7)
        do_sample = job_input.get('do_sample', True)

        # Validate input
        if not user_prompt:
            return {
                "error": "prompt field is required",
                "status": "error"
            }

        # Load model if not already loaded
        model, tokenizer = load_model()

        # Prepare messages
        messages.append({"role": "user", "content": user_prompt})

        # Create prompt using chat template
        prompt = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )

        # Tokenize input
        inputs = tokenizer(prompt, return_tensors="pt")
        if torch.cuda.is_available():
            inputs = {k: v.cuda() for k, v in inputs.items()}

        # Generate response
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                do_sample=do_sample,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id
            )

        # Decode response
        response = tokenizer.decode(
            outputs[0][inputs['input_ids'].shape[1]:],
            skip_special_tokens=True
        )

        # Update messages with assistant response
        messages.append({"role": "assistant", "content": response})

        # Return result
        return {
            "response": response,
            "messages": messages,
            "status": "success"
        }

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in handler: {error_trace}")

        return {
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": error_trace,
            "status": "error"
        }

if __name__ == "__main__":
    # Start the serverless worker
    print("Starting RunPod Serverless Worker...")
    runpod.serverless.start({"handler": handler})
