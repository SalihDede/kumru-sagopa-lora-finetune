"""
Runpod Serverless Handler for Sagopa Chatbot
This handler provides an API endpoint for the fine-tuned LLM model
Uses base Kumru-2B model + LoRA adapters
"""

import runpod
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import torch
import os
import gc

# Global variables for model and tokenizer
model = None
tokenizer = None

# Configuration
BASE_MODEL_NAME = "vngrs-ai/Kumru-2B"
LORA_ADAPTER_NAME = os.environ.get("LORA_ADAPTER", "SalihHub/kumru-sagopa-lora-adapter")

# System prompt for Sagopa character
SYSTEM_PROMPT = """Sen Sagopa Kajmer'sin. Derin düşünen, melankolik ama samimi bir rap sanatçısısın.
Hayat, zaman, yalnızlık gibi temalardan bahsedersin. Kendi kelime dağarcığınla doğal ve içten konuşursun."""


def load_model():
    """Load the base model and LoRA adapters with comprehensive error handling"""
    global model, tokenizer

    if model is not None and tokenizer is not None:
        return model, tokenizer

    print("=" * 60)
    print("Loading Sagopa Chatbot Model...")
    print("=" * 60)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if torch.cuda.is_available() else torch.float32

    print(f"Device: {device}")
    if torch.cuda.is_available():
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")

    # Step 1: Load tokenizer
    print(f"\n[1/3] Loading tokenizer from {BASE_MODEL_NAME}...")
    try:
        tokenizer = AutoTokenizer.from_pretrained(
            BASE_MODEL_NAME,
            trust_remote_code=True,
            use_fast=True
        )
        tokenizer.pad_token = tokenizer.eos_token
        tokenizer.padding_side = "right"
        print("Tokenizer loaded successfully!")
    except Exception as e:
        print(f"ERROR loading tokenizer: {e}")
        raise RuntimeError(f"Failed to load tokenizer: {e}")

    # Step 2: Load base model
    print(f"\n[2/3] Loading base model from {BASE_MODEL_NAME}...")
    try:
        # Clear GPU memory before loading
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            gc.collect()

        base_model = AutoModelForCausalLM.from_pretrained(
            BASE_MODEL_NAME,
            torch_dtype=dtype,
            device_map="auto",
            low_cpu_mem_usage=True,
            trust_remote_code=True
        )
        print("Base model loaded successfully!")

        if torch.cuda.is_available():
            mem_used = torch.cuda.memory_allocated() / 1024**3
            print(f"GPU Memory Used: {mem_used:.2f} GB")

    except Exception as e:
        print(f"ERROR loading base model: {e}")
        raise RuntimeError(f"Failed to load base model: {e}")

    # Step 3: Load LoRA adapters
    print(f"\n[3/3] Loading LoRA adapters from {LORA_ADAPTER_NAME}...")
    try:
        model = PeftModel.from_pretrained(
            base_model,
            LORA_ADAPTER_NAME,
            torch_dtype=dtype
        )
        print("LoRA adapters loaded successfully!")
    except Exception as e:
        print(f"ERROR loading LoRA adapters: {e}")
        print("Falling back to base model without LoRA...")
        model = base_model

    # Set model to evaluation mode
    model.eval()

    print("\n" + "=" * 60)
    print("Model loaded and ready!")
    print("=" * 60)

    return model, tokenizer


def format_prompt(user_input: str) -> str:
    """Format the prompt in ChatML format for Kumru model"""
    return f"""<|im_start|>system
{SYSTEM_PROMPT}
<|im_end|>
<|im_start|>user
{user_input}
<|im_end|>
<|im_start|>assistant
"""


def extract_response(full_text: str) -> str:
    """Extract assistant response from ChatML formatted output"""
    if "<|im_start|>assistant" in full_text:
        response = full_text.split("<|im_start|>assistant")[-1]
        # Remove trailing tokens
        if "<|im_end|>" in response:
            response = response.split("<|im_end|>")[0]
        if "<|im_start|>" in response:
            response = response.split("<|im_start|>")[0]
        return response.strip()
    return full_text.strip()


def handler(job):
    """
    RunPod serverless handler function

    Expected input format:
    {
        "input": {
            "prompt": "User message here",
            "max_new_tokens": 128,
            "temperature": 0.7,
            "do_sample": true
        }
    }
    """
    try:
        # Get job input
        job_input = job.get('input', {})

        # Extract parameters with defaults
        user_prompt = job_input.get('prompt', '')
        max_new_tokens = min(job_input.get('max_new_tokens', 128), 512)  # Cap at 512
        temperature = max(0.1, min(job_input.get('temperature', 0.7), 2.0))  # Clamp 0.1-2.0
        do_sample = job_input.get('do_sample', True)
        top_p = job_input.get('top_p', 0.9)
        top_k = job_input.get('top_k', 50)
        repetition_penalty = job_input.get('repetition_penalty', 1.2)

        # Validate input
        if not user_prompt:
            return {
                "error": "prompt field is required",
                "status": "error"
            }

        if len(user_prompt) > 2000:
            return {
                "error": "prompt too long (max 2000 characters)",
                "status": "error"
            }

        # Load model if not already loaded
        model, tokenizer = load_model()

        # Format prompt
        prompt = format_prompt(user_prompt)

        # Tokenize input
        inputs = tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=1024
        )

        # Move to GPU if available
        if torch.cuda.is_available():
            inputs = {k: v.cuda() for k, v in inputs.items()}

        # Generate response
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                do_sample=do_sample,
                top_p=top_p,
                top_k=top_k,
                repetition_penalty=repetition_penalty,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id,
                use_cache=True
            )

        # Decode response
        full_response = tokenizer.decode(outputs[0], skip_special_tokens=False)

        # Extract assistant response
        response = extract_response(full_response)

        # Clean up any remaining special tokens
        response = response.replace("<|im_end|>", "").replace("<|im_start|>", "").strip()

        # Return result
        return {
            "response": response,
            "status": "success",
            "tokens_generated": len(outputs[0]) - len(inputs['input_ids'][0])
        }

    except torch.cuda.OutOfMemoryError:
        # Clear GPU memory and return error
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            gc.collect()
        return {
            "error": "GPU out of memory. Try reducing max_new_tokens.",
            "status": "error"
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
    print("Starting RunPod Serverless Worker...")
    print(f"Base Model: {BASE_MODEL_NAME}")
    print(f"LoRA Adapter: {LORA_ADAPTER_NAME}")
    runpod.serverless.start({"handler": handler})
