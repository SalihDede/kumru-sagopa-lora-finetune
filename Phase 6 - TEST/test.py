from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
import torch

# Base model ve tokenizer
base_model_name = "vngrs-ai/Kumru-2B"
lora_adapter = "SalihHub/Kumru-2B-Sagopa-Lora"

# Tokenizer (base model'den)
tokenizer = AutoTokenizer.from_pretrained(base_model_name)

# Base model
model = AutoModelForCausalLM.from_pretrained(
    base_model_name,
    dtype=torch.float16,
    device_map="auto"
)

# LoRA adapter'ı yükle
model = PeftModel.from_pretrained(model, lora_adapter)
model.eval()

# Chat fonksiyonu
def chat_with_sagopa(question, max_new_tokens=200):
    system_prompt = """Sen Sagopa Kajmer'sin. Derin düşünen, melankolik ama samimi bir rap sanatçısısın.
Hayat, zaman, yalnızlık gibi temalardan bahsedersin. Kendi kelime dağarcığınla doğal ve içten konuşursun."""
    
    prompt = f"""<|im_start|>system
{system_prompt}
<|im_end|>
<|im_start|>user
{question}
<|im_end|>
<|im_start|>assistant
"""
    
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    # Remove token_type_ids if present (not used by this model)
    if "token_type_ids" in inputs:
        del inputs["token_type_ids"]

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=0.7,
            top_p=0.9,
            do_sample=True,
            repetition_penalty=1.2,
            pad_token_id=tokenizer.eos_token_id
        )
    
    response = tokenizer.decode(outputs[0], skip_special_tokens=False)
    answer = response.split("<|im_start|>assistant\n")[-1].split("<|im_end|>")[0].strip()
    return answer

# Örnek kullanım
print(chat_with_sagopa("Bugün nasılsın?"))
