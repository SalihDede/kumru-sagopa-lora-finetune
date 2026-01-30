# RunPod Deployment - Kumru-2B-Sagopa-Lora

## Adım 1: Docker Image Build & Push

```bash
# Docker Hub'a giriş
docker login

# Bu klasöre gel
cd "Phase 7 - Deploy"

# Image build (kendi username'ini yaz)
docker build -t DOCKERHUB_USERNAME/kumru-sagopa-lora:latest .

# Push
docker push DOCKERHUB_USERNAME/kumru-sagopa-lora:latest
```

## Adım 2: RunPod Endpoint Oluştur

1. RunPod Dashboard → Serverless → **New Endpoint**
2. **Custom** seç
3. Ayarlar:
   - **Image:** `DOCKERHUB_USERNAME/kumru-sagopa-lora:latest`
   - **GPU:** T4 veya RTX A4000
   - **Container Disk:** 20 GB
   - **Active Workers:** 0
   - **Max Workers:** 3

## Adım 3: API Kullanımı

```python
import requests

response = requests.post(
    "https://api.runpod.ai/v2/ENDPOINT_ID/runsync",
    headers={"Authorization": "Bearer API_KEY"},
    json={
        "input": {
            "prompt": "Merhaba!",
            "max_new_tokens": 200
        }
    }
)
print(response.json())
```

## Parametreler

| Parametre | Default | Açıklama |
|-----------|---------|----------|
| prompt | - | Text prompt |
| messages | - | Chat format |
| max_new_tokens | 512 | Max token |
| temperature | 0.7 | Yaratıcılık |
| top_p | 0.9 | Nucleus sampling |
