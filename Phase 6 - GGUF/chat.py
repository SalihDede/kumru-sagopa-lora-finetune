# chat.py
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import sys

model_path = r"C:\Users\Hp\Desktop\LoRA Finetune\Phase 6 - GGUF\kumru-sagopa-merged"

print("Python:", sys.version)
print("Torch:", torch.__version__)
print("CUDA:", torch.cuda.is_available())
if torch.cuda.is_available():
    print("GPU:", torch.cuda.get_device_name(0))
    print("VRAM:", round(torch.cuda.get_device_properties(0).total_memory / 1024**3, 1), "GB")

try:
    print("\n1. Tokenizer yükleniyor...")
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    print("   Tokenizer OK!")
    
    print("2. Model yükleniyor (CPU)...")
    sys.stdout.flush()
    
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.float32,
        device_map="cpu",
        low_cpu_mem_usage=True
    )
    print("   Model OK!")
    
    print("\n=== Chat Başladı (çıkmak için 'q') ===\n")

    messages = []
    while True:
        user_input = input("Sen: ")
        if user_input.lower() in ["çık", "exit", "q"]:
            break
        
        messages.append({"role": "user", "content": user_input})
        
        prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = tokenizer(prompt, return_tensors="pt")
        
        print("Düşünüyor...", end=" ", flush=True)
        outputs = model.generate(
            **inputs,
            max_new_tokens=128,
            temperature=0.7,
            do_sample=True,
            pad_token_id=tokenizer.pad_token_id
        )
        
        response = tokenizer.decode(outputs[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)
        print(f"\nKumru: {response}\n")
        
        messages.append({"role": "assistant", "content": response})

except Exception as e:
    print(f"\nHATA: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

input("\nEnter'a bas...")