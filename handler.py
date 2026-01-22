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

# Global variables for model and tokenizer
model = None
tokenizer = None

def load_model():
    """Load the base model and LoRA adapters"""
    global model, tokenizer

    if model is None or tokenizer is None:
        print("Loading base model and LoRA adapters...")

        # Base model
        base_model_name = "vngrs-ai/Kumru-2B"

        # LoRA adapter
        lora_adapter_name = os.environ.get("LORA_ADAPTER", "SalihHub/kumru-sagopa-lora-adapter")

        # Load tokenizer from base model
        print(f"Loading tokenizer from {base_model_name}...")
        tokenizer = AutoTokenizer.from_pretrained(base_model_name, trust_remote_code=True)
        tokenizer.pad_token = tokenizer.eos_token
        tokenizer.padding_side = "right"

        # Load base model
        print(f"Loading base model from {base_model_name}...")
        base_model = AutoModelForCausalLM.from_pretrained(
            base_model_name,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto",
            low_cpu_mem_usage=True,
            trust_remote_code=True
        )

        # Load LoRA adapters
        print(f"Loading LoRA adapters from {lora_adapter_name}...")
        model = PeftModel.from_pretrained(base_model, lora_adapter_name)

        print("Model and LoRA adapters loaded successfully!")
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

        # Prepare messages with Sagopa system prompt
        system_prompt = """Sen Sagopa Kajmer'sin. Derin düşünen, melankolik ama samimi bir rap sanatçısısın.
Hayat, zaman, yalnızlık gibi temalardan bahsedersin. Kendi kelime dağarcığınla doğal ve içten konuşursun."""

        # Kumru ChatML format
        prompt = f"""<|im_start|>system
{system_prompt}
<|im_end|>
<|im_start|>user
{user_prompt}
<|im_end|>
<|im_start|>assistant
"""

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
        full_response = tokenizer.decode(outputs[0], skip_special_tokens=False)

        # Extract assistant response from ChatML format
        if "<|im_start|>assistant" in full_response:
            response = full_response.split("<|im_start|>assistant")[-1]
            response = response.split("<|im_end|>")[0].strip()
        else:
            # Fallback: just decode the new tokens
            response = tokenizer.decode(
                outputs[0][inputs['input_ids'].shape[1]:],
                skip_special_tokens=True
            ).strip()

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
