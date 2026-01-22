# RunPod Serverless Deployment Guide

Bu doküman, Sagopa Chatbot modelini RunPod serverless ortamına deploy etmek için gereken adımları açıklar.

## 🚨 Önemli: Model Dosyalarını Hugging Face'e Yükleyin

GitHub'ın dosya boyutu limiti nedeniyle (2GB), model dosyalarınızı Hugging Face Hub'a yüklemeniz gerekiyor.

### Model Yükleme Adımları

1. **Hugging Face hesabı oluşturun**: [huggingface.co](https://huggingface.co)

2. **Access Token oluşturun**:
   - Settings → Access Tokens → New token
   - "Write" yetkisi verin

3. **Model yükleyin**:
```bash
# Gerekli paketi yükleyin
pip install huggingface_hub

# Login yapın
huggingface-cli login
# Token'ınızı yapıştırın

# Model yükleme scriptini çalıştırın
python upload_to_huggingface.py
```

Script `SalihDede/kumru-sagopa-merged` adında bir repo oluşturacak ve modelinizi yükleyecek.

**Alternatif**: Manuel yükleme:
```python
from huggingface_hub import HfApi
api = HfApi()
api.upload_folder(
    folder_path="./SagoChatBOTAPI/kumru-sagopa-merged",
    repo_id="SalihDede/kumru-sagopa-merged",
    repo_type="model",
)
```

## Kurulum Adımları

### 1. GitHub Secrets Ayarlama

GitHub reponuzda şu secrets'ları ekleyin:
- `Settings` → `Secrets and variables` → `Actions` → `New repository secret`

Gerekli secrets:
```
DOCKER_USERNAME: Docker Hub kullanıcı adınız
DOCKER_PASSWORD: Docker Hub şifreniz veya access token
```

### 2. GitHub'a Push

Model dosyaları artık GitHub'da değil, Hugging Face'de olacak:

```bash
# Git durumunu kontrol edin
git status

# Sadece kod dosyalarını ekleyin (model dosyaları HARİÇ)
git add .dockerignore .github/ Dockerfile RUNPOD_DEPLOYMENT.md handler.py requirements.txt test_handler.py upload_to_huggingface.py .gitignore

# Commit yapın
git commit -m "Add RunPod serverless configuration (model on HuggingFace)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# Push edin
git push origin main
```

Push yaptığınızda GitHub Actions otomatik olarak:
- Docker imajını build edecek
- Docker Hub'a push edecek
- Model HuggingFace'den otomatik indirilecek

### 3. RunPod'da Serverless Endpoint Oluşturma

1. [RunPod Console](https://www.runpod.io/console/serverless) → Serverless sekmesi
2. **"New Endpoint"** butonuna tıklayın
3. Ayarları yapın:

   **Endpoint Configuration:**
   - **Name**: `sagopa-chatbot`
   - **Select Template**: Custom (Docker image)
   - **Container Image**: `<DOCKER_USERNAME>/sagopa-chatbot-runpod:latest`
   - **Container Disk**: 20 GB (model indirme için yeterli alan)
   - **GPU Types**: GPU seçin (örn: RTX 4090, A4000, vb.)

   **Environment Variables (isteğe bağlı):**
   - `MODEL_NAME`: `SalihDede/kumru-sagopa-merged` (farklı bir model kullanıyorsanız)
   - `HF_TOKEN`: Hugging Face token (private model için gerekli)

   **Advanced Configuration:**
   - **Idle Timeout**: 5 seconds
   - **Execution Timeout**: 120 seconds (ilk yükleme uzun sürebilir)
   - **Min Workers**: 0
   - **Max Workers**: 3 (ihtiyacınıza göre)

4. **Deploy** butonuna tıklayın

⚠️ **Not**: İlk çalıştırmada model Hugging Face'den indirilecek, bu 30-60 saniye sürebilir. Sonraki istekler çok daha hızlı olacak.

### 4. API Endpoint'i Test Etme

Endpoint oluşturulduktan sonra bir API endpoint URL'i alacaksınız:
```
https://api.runpod.ai/v2/<ENDPOINT_ID>/runsync
```

Test için curl kullanın:

```bash
curl -X POST "https://api.runpod.ai/v2/<ENDPOINT_ID>/runsync" \
  -H "Authorization: Bearer <RUNPOD_API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "prompt": "Merhaba Sagopa, nasılsın?",
      "max_new_tokens": 128,
      "temperature": 0.7
    }
  }'
```

### 5. Frontend Entegrasyonu

Portfolio sitenizde bu endpoint'i kullanmak için örnek JavaScript kodu:

```javascript
async function chatWithSagopa(userMessage, conversationHistory = []) {
  const response = await fetch('https://api.runpod.ai/v2/<ENDPOINT_ID>/runsync', {
    method: 'POST',
    headers: {
      'Authorization': 'Bearer YOUR_RUNPOD_API_KEY',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      input: {
        prompt: userMessage,
        messages: conversationHistory,
        max_new_tokens: 128,
        temperature: 0.7,
        do_sample: true
      }
    })
  });

  const data = await response.json();

  if (data.status === 'COMPLETED') {
    return {
      response: data.output.response,
      messages: data.output.messages
    };
  } else {
    throw new Error('Request failed: ' + data.status);
  }
}

// Kullanım örneği
const result = await chatWithSagopa("Merhaba Sagopa!");
console.log(result.response);
```

**⚠️ GÜVENLİK UYARISI**: Frontend'de direkt API key kullanmayın! Kendi backend'iniz üzerinden proxy yapın:

```javascript
// Frontend'den kendi backend'inize istek gönderin
const response = await fetch('https://your-backend.com/api/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer USER_SESSION_TOKEN'  // Kendi auth sisteminiz
  },
  body: JSON.stringify({
    prompt: userMessage,
    messages: conversationHistory
  })
});

// Backend'inizde RunPod'a istek gönderin
// Backend API key'i güvenli tutar
```

## API Input Format

Handler şu parametreleri kabul eder:

```json
{
  "input": {
    "prompt": "Kullanıcı mesajı (zorunlu)",
    "messages": [
      {"role": "user", "content": "Önceki mesaj"},
      {"role": "assistant", "content": "Önceki cevap"}
    ],
    "max_new_tokens": 128,
    "temperature": 0.7,
    "do_sample": true
  }
}
```

## API Output Format

Başarılı response:
```json
{
  "delayTime": 1234,
  "executionTime": 5678,
  "id": "...",
  "status": "COMPLETED",
  "output": {
    "response": "Model cevabı",
    "messages": [...],
    "status": "success"
  }
}
```

Hata durumunda:
```json
{
  "status": "FAILED",
  "output": {
    "error": "Hata mesajı",
    "error_type": "ExceptionType",
    "status": "error"
  }
}
```

## Maliyet Optimizasyonu

1. **Idle Timeout**: Düşük tutun (5-10 saniye) - kullanılmadığında hızlıca kapanır
2. **Min Workers**: 0 yapın - hiç kullanılmadığında ücret alınmaz
3. **Cold Start**: İlk istek 30-60 saniye sürebilir (model indirme), sonraki istekler 2-5 saniye
4. **GPU Seçimi**:
   - **RTX 4090**: En hızlı, biraz daha pahalı
   - **A4000**: İyi denge, önerilen
   - **A5000**: Daha fazla VRAM gerekiyorsa
5. **Model Cache**: Container disk'i yeterli yapın (20GB+), model cache'lenir

## Proje Dosya Yapısı

```
.
├── handler.py                      # RunPod serverless handler
├── Dockerfile                      # Container konfigürasyonu
├── requirements.txt                # Python dependencies
├── upload_to_huggingface.py       # Model yükleme scripti
├── test_handler.py                # Lokal test scripti
├── .github/
│   └── workflows/
│       └── deploy-runpod.yml      # CI/CD pipeline
├── .dockerignore                   # Docker build optimizasyonu
└── SagoChatBOTAPI/
    └── kumru-sagopa-merged/       # (Sadece lokal, Git'e gitmiyor)
```

## Güvenlik Notları

1. **API Key'i gizleyin**:
   - Frontend'de ASLA direkt RunPod API key kullanmayın
   - Kendi backend'iniz üzerinden proxy yapın

2. **Backend Proxy Örneği** (Node.js/Express):
```javascript
app.post('/api/chat', authenticateUser, async (req, res) => {
  // Kullanıcı auth kontrolü
  if (!req.user) return res.status(401).json({ error: 'Unauthorized' });

  // Rate limiting
  const rateLimit = await checkUserRateLimit(req.user.id);
  if (!rateLimit.allowed) {
    return res.status(429).json({ error: 'Too many requests' });
  }

  // RunPod'a istek gönder
  const response = await fetch(RUNPOD_ENDPOINT, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${process.env.RUNPOD_API_KEY}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      input: {
        prompt: req.body.prompt,
        messages: req.body.messages,
        max_new_tokens: 128
      }
    })
  });

  const data = await response.json();
  res.json(data);
});
```

3. **Rate Limiting**: Aşırı kullanımı engellemek için:
   - Kullanıcı başına günlük/saatlik limit
   - IP bazlı rate limiting
   - Mesaj uzunluğu limiti

4. **Private Model**: Model'i private yapmak için:
   - Hugging Face'de model'i private yapın
   - RunPod environment variable olarak `HF_TOKEN` ekleyin

## Troubleshooting

### Model yüklenemiyor
```
Error: Repository not found
```
**Çözüm**:
- Model'in Hugging Face'e yüklendiğinden emin olun
- Private model için `HF_TOKEN` environment variable ekleyin
- Model adının doğru olduğunu kontrol edin (handler.py'de `MODEL_NAME`)

### Cold start çok uzun
```
Request timeout after 60s
```
**Çözüm**:
- Execution timeout'u 120 saniyeye çıkarın (ilk yükleme için)
- Daha hızlı internet bağlantısı olan bölge seçin
- Model quantization düşünün (4-bit, 8-bit)

### Out of Memory
```
CUDA out of memory
```
**Çözüm**:
- Daha fazla VRAM'li GPU seçin (RTX 4090: 24GB, A5000: 24GB)
- Model quantization kullanın
- `max_new_tokens` değerini düşürün

### Container build failed
```
Failed to build Docker image
```
**Çözüm**:
- GitHub Actions logs'ları kontrol edin
- Docker Hub'a login olduğunuzdan emin olun
- `DOCKER_USERNAME` ve `DOCKER_PASSWORD` secrets'ların doğru olduğunu kontrol edin

### Model download failed during build
Model build sırasında indirilemezse:
- Sorun değil! Model runtime'da indirilecek
- İlk API isteği biraz daha uzun sürer (30-60 saniye)
- Sonraki istekler normal hızda çalışır

## Güncelleme

Kodda değişiklik yaptığınızda:

```bash
git add .
git commit -m "Update handler configuration"
git push origin main
```

GitHub Actions yeni image'ı build edecek. RunPod otomatik olarak yeni image'ı kullanacaktır.

Model güncellemek için:
1. Yeni modeli Hugging Face'e yükleyin
2. `MODEL_NAME` environment variable'ını güncelleyin (RunPod endpoint'te)
3. Endpoint'i yeniden başlatın

## Lokal Test

Deploy etmeden önce lokal test yapabilirsiniz:

```bash
# Model'in lokal olduğundan emin olun
ls SagoChatBOTAPI/kumru-sagopa-merged/

# Test script'i çalıştırın
python test_handler.py
```

## Destek ve Kaynaklar

- [RunPod Documentation](https://docs.runpod.io/serverless/overview)
- [RunPod Discord](https://discord.gg/runpod)
- [Hugging Face Hub Docs](https://huggingface.co/docs/hub/index)
- [Transformers Documentation](https://huggingface.co/docs/transformers)

## Özet: Deployment Checklist

- [ ] Model'i Hugging Face'e yükleyin (`upload_to_huggingface.py`)
- [ ] GitHub Secrets'ları ekleyin (`DOCKER_USERNAME`, `DOCKER_PASSWORD`)
- [ ] Kodu GitHub'a push edin (model dosyaları HARİÇ)
- [ ] GitHub Actions'ın Docker build etmesini bekleyin
- [ ] RunPod'da endpoint oluşturun
- [ ] API'yi test edin
- [ ] Frontend'e entegre edin (backend proxy ile)
- [ ] Rate limiting ve güvenlik ekleyin
- [ ] Production'a deploy edin! 🚀
