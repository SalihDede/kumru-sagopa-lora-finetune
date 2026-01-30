"""
RunPod Serverless Handler for Kumru-2B-Sagopa-Lora Model (LoRA Adapter)
"""
import runpod
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import torch
import os

# Model configuration
BASE_MODEL = os.environ.get("BASE_MODEL", "vngrs-ai/Kumru-2B")
LORA_ADAPTER = os.environ.get("LORA_ADAPTER", "SalihHub/Kumru-2B-Sagopa-Lora")
MAX_NEW_TOKENS = int(os.environ.get("MAX_NEW_TOKENS", 512))

# Global model and tokenizer
model = None
tokenizer = None


def load_model():
    """Load base model with LoRA adapter"""
    global model, tokenizer

    print(f"Loading base model: {BASE_MODEL}")
    print(f"Loading LoRA adapter: {LORA_ADAPTER}")

    # Load tokenizer from LoRA adapter (has the fine-tuned config)
    tokenizer = AutoTokenizer.from_pretrained(
        LORA_ADAPTER,
        trust_remote_code=True
    )

    # Set pad token if not exists
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Load base model
    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        torch_dtype=torch.float16,
        device_map="auto",
        trust_remote_code=True
    )

    # Load LoRA adapter
    model = PeftModel.from_pretrained(
        base_model,
        LORA_ADAPTER,
        torch_dtype=torch.float16
    )

    model.eval()
    print("Model with LoRA adapter loaded successfully!")

    return model, tokenizer


def generate_response(prompt: str, params: dict) -> str:
    """Generate response from the model"""
    global model, tokenizer

    # Generation parameters
    max_new_tokens = params.get("max_new_tokens", MAX_NEW_TOKENS)
    temperature = params.get("temperature", 0.7)
    top_p = params.get("top_p", 0.9)
    top_k = params.get("top_k", 50)
    repetition_penalty = params.get("repetition_penalty", 1.1)
    do_sample = params.get("do_sample", True)

    # Tokenize
    inputs = tokenizer(
        prompt,
        return_tensors="pt",
        truncation=True,
        max_length=2048
    ).to(model.device)

    # Generate
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=temperature if do_sample else 1.0,
            top_p=top_p,
            top_k=top_k,
            repetition_penalty=repetition_penalty,
            do_sample=do_sample,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id
        )

    # Decode only new tokens
    generated_tokens = outputs[0][inputs["input_ids"].shape[1]:]
    response = tokenizer.decode(generated_tokens, skip_special_tokens=True)

    return response.strip()


def handler(event: dict) -> dict:
    """
    RunPod serverless handler function

    Input formats supported:
    1. Simple prompt: {"input": {"prompt": "Merhaba!"}}
    2. Chat format: {"input": {"messages": [{"role": "user", "content": "Merhaba!"}]}}

    Optional parameters:
    - max_new_tokens: int (default: 512)
    - temperature: float (default: 0.7)
    - top_p: float (default: 0.9)
    - top_k: int (default: 50)
    - repetition_penalty: float (default: 1.1)
    - do_sample: bool (default: True)
    """
    try:
        # Load model if not loaded
        global model, tokenizer
        if model is None:
            load_model()

        # Get input
        input_data = event.get("input", {})

        # Handle different input formats
        if "messages" in input_data:
            # Chat format - use tokenizer's chat template
            messages = input_data["messages"]
            prompt = tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
        elif "prompt" in input_data:
            # Simple prompt format
            prompt = input_data["prompt"]
        else:
            return {"error": "No 'prompt' or 'messages' provided in input"}

        # Extract generation parameters
        params = {
            "max_new_tokens": input_data.get("max_new_tokens", MAX_NEW_TOKENS),
            "temperature": input_data.get("temperature", 0.7),
            "top_p": input_data.get("top_p", 0.9),
            "top_k": input_data.get("top_k", 50),
            "repetition_penalty": input_data.get("repetition_penalty", 1.1),
            "do_sample": input_data.get("do_sample", True)
        }

        # Generate response
        response = generate_response(prompt, params)

        return {
            "output": response,
            "base_model": BASE_MODEL,
            "lora_adapter": LORA_ADAPTER,
            "usage": {
                "prompt_length": len(prompt),
                "response_length": len(response)
            }
        }

    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }


# Start the serverless worker
if __name__ == "__main__":
    print("Starting RunPod Serverless Worker...")
    print(f"Base Model: {BASE_MODEL}")
    print(f"LoRA Adapter: {LORA_ADAPTER}")
    runpod.serverless.start({"handler": handler})
