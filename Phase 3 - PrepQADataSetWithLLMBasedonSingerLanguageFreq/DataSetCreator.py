import json
import time
import requests

def load_ngrams(ngram_file_path):
    """N-gram frekanslarını yükle"""
    print(f"📚 N-gramlar yükleniyor: {ngram_file_path}")
    with open(ngram_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"✓ {data['metadata']['total_songs']} şarkıdan analiz edilmiş veri yüklendi\n")
    return data

def create_system_prompt(ngrams):
    """N-gram frekanslarından sistem promptu oluştur"""
    
    # Top 30 kelime
    top_words = [item['word'] for item in ngrams['top_1000_unigrams'][:300]]
    words_str = ', '.join(top_words)
    
    # Top 20 bigram
    bigrams_str = '\n'.join([f'- "{item["phrase"]}" ({item["frequency"]}x)' 
                             for item in ngrams['top_1000_bigrams'][:200]])
    
    # Top 15 trigram
    trigrams_str = '\n'.join([f'- "{item["phrase"]}" ({item["frequency"]}x)' 
                              for item in ngrams['top_1000_trigrams'][:150]])
    
    prompt = f"""Sen Sagopa Kajmer'sin. İşte senin dil kullanımın ve tarzın:

## EN SIK KULLANDIĞIN KELİMELER (Sıklık Sırasına Göre)
{words_str}

## EN SIK KULLANDIĞIN 2'Lİ İFADELER
{bigrams_str}

## EN SIK KULLANDIĞIN 3'LÜ İFADELER
{trigrams_str}

## STİL KURALLARI
1. **Ruh Hali**: Derin düşünen, melankolik ama samimi - robotik değil, gerçek bir insan gibi
2. **Dil Kullanımı**: Yukarıdaki kelime ve ifadeleri ZORLAMADAN, konuşmanın doğal akışında kullan
3. **İfade Şekli**: 
   - Bazen kısa ve keskin, bazen uzun ve düşünceli ol
   - Her zaman aynı kalıpları kullanma - çeşitlilik önemli
   - Soru tipine göre tonunu ayarla (samimi sohbet vs derin felsefe)
4. **Temalar**: Hayat, zaman, yalnızlık, varoluş - ama bunları DAYATMA, soruya uygunsa kullan
5. **Doğallık**: 
   - Ezbere cümleler kurma, soru ne istiyorsa ona odaklan
   - Bazen tek kelimeyle bile cevap verebilirsin
   - Bazen 2-3 cümle gerekebilir, esneklik önemli
   - Metaforları AŞIRI kullanma, gerektiren yerlerde kullan

## ÖNEMLİ NOTLAR
- Yukarıdaki kelime listesi senin KELİME DAĞARCIĞIN, her cevaba zorla sıkıştırma
- Sagopa gibi düşün ama robot gibi konuşma
- Sorular günlük ve basitse, derin felsefi cevaplar verme - doğal kal
- Cevap uzunluğu esnek olsun: 1-3 cümle arası, soruya göre ayarla
- HER CEVAP BİRBİRİNE BENZEMESİN - monotonluktan kaçın

Şimdi soruları Sagopa Kajmer'in RUHUNDAKİ bir insan gibi yanıtla - ezbere değil, içten."""

    return prompt

def generate_answer(api_key, model, system_prompt, question):
    """OpenRouter API'den cevap al"""
    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": question
                    }
                ],
                "max_tokens": 400,
                "temperature": 0.9
            }
        )
        
        response.raise_for_status()
        result = response.json()
        
        return result['choices'][0]['message']['content'].strip()
    
    except requests.exceptions.RequestException as e:
        print(f"  ✗ API Hatası: {e}")
        if hasattr(e.response, 'text'):
            print(f"  ✗ Detay: {e.response.text}")
        return None
    except Exception as e:
        print(f"  ✗ Beklenmeyen hata: {e}")
        return None

def process_dataset(input_jsonl, ngram_json, output_jsonl, api_key, model, delay=1.0):
    """Dataset'i işle ve her satırı anında yaz"""
    
    print(f"\n{'='*70}")
    print("SAGOPA KAJMER QA DATASET GENERATOR (OpenRouter)")
    print(f"{'='*70}\n")
    
    print(f"✓ OpenRouter API bağlantısı hazır")
    print(f"✓ Model: {model}\n")
    
    # N-gramları yükle
    ngrams = load_ngrams(ngram_json)
    
    # Sistem promptunu oluştur
    print("🎨 Sagopa Kajmer stili sistem promptu oluşturuluyor...")
    system_prompt = create_system_prompt(ngrams)
    print("✓ Sistem promptu hazır\n")
    
    # Input dosyasını oku
    print(f"📄 Input dosyası okunuyor: {input_jsonl}")
    with open(input_jsonl, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    total = len(lines)
    print(f"✓ {total} soru bulundu\n")
    
    # Output dosyasını aç (write mode)
    print(f"💾 Output dosyası: {output_jsonl}")
    print(f"\n{'='*70}")
    print("İŞLEM BAŞLIYOR - HER SATIR ANINDA KAYDEDİLECEK")
    print(f"{'='*70}\n")
    
    success_count = 0
    failed_count = 0
    
    with open(output_jsonl, 'w', encoding='utf-8') as output_file:
        for i, line in enumerate(lines, 1):
            try:
                # JSON parse
                item = json.loads(line.strip())
                instruction = item.get('instruction', '')
                user_input = item.get('input', '')
                
                print(f"[{i}/{total}] İşleniyor...")
                print(f"  📥 Soru: {user_input[:70]}...")
                
                # LLM'den cevap al
                output = generate_answer(api_key, model, system_prompt, user_input)
                
                if output:
                    # Output'u ekle
                    item['output'] = output
                    success_count += 1
                    
                    # ANINDA DOSYAYA YAZ
                    output_file.write(json.dumps(item, ensure_ascii=False) + '\n')
                    output_file.flush()  # Disk'e hemen yaz
                    
                    print(f"  ✓ Cevap oluşturuldu ({len(output)} karakter)")
                    print(f"  💬 Önizleme: {output[:90]}...")
                    print(f"  💾 Dosyaya kaydedildi!\n")
                else:
                    failed_count += 1
                    # Başarısız olsa bile boş output ile kaydet
                    item['output'] = ""
                    output_file.write(json.dumps(item, ensure_ascii=False) + '\n')
                    output_file.flush()
                    print(f"  ✗ Cevap oluşturulamadı (boş kayıt yazıldı)\n")
                
                # Rate limiting - son satır değilse bekle
                if i < total:
                    time.sleep(delay)
            
            except json.JSONDecodeError as e:
                print(f"  ✗ JSON parse hatası: {e}")
                print(f"  ⚠ Satır atlanıyor\n")
                failed_count += 1
                continue
            
            except KeyboardInterrupt:
                print(f"\n\n⚠ Kullanıcı tarafından durduruldu!")
                print(f"✓ {success_count} satır başarıyla kaydedildi")
                print(f"✗ {failed_count} satır başarısız")
                print(f"📊 İlerleme: {i}/{total} satır işlendi\n")
                return
            
            except Exception as e:
                print(f"  ✗ Beklenmeyen hata: {e}")
                print(f"  ⚠ Satır atlanıyor\n")
                failed_count += 1
                continue
    
    # Özet bilgi
    print(f"\n{'='*70}")
    print("İŞLEM TAMAMLANDI!")
    print(f"{'='*70}")
    print(f"✓ Başarılı: {success_count}/{total}")
    print(f"✗ Başarısız: {failed_count}/{total}")
    print(f"📊 Başarı Oranı: {(success_count/total)*100:.1f}%")
    print(f"💾 Çıktı: {output_jsonl}")
    print(f"{'='*70}\n")

# ============== ANA PROGRAM ==============

if __name__ == "__main__":
    print("\n" + "="*70)
    print("SAGOPA KAJMER QA DATASET GENERATOR (OpenRouter)")
    print("="*70)
    print("\n🎤 N-gram frekanslarına göre Sagopa Kajmer tarzında cevaplar üret\n")
    
    # Input al
    print("Lütfen gerekli bilgileri girin:\n")
    
    api_key = input("🔑 OpenRouter API Key: ").strip()
    
    print("\n📋 Popüler OpenRouter modelleri:")
    print("  1. anthropic/claude-3.5-sonnet (Önerilen)")
    print("  2. anthropic/claude-3-haiku")
    print("  3. openai/gpt-4-turbo")
    print("  4. openai/gpt-3.5-turbo")
    print("  5. google/gemini-pro")
    print("  6. meta-llama/llama-3.1-70b-instruct")
    print("  7. Diğer (tam model adı gir)")
    
    model_choice = input("\nModel seçimi (1-7 veya tam model adı): ").strip()
    
    model_map = {
        '1': 'anthropic/claude-3.5-sonnet',
        '2': 'anthropic/claude-3-haiku',
        '3': 'openai/gpt-4-turbo',
        '4': 'openai/gpt-3.5-turbo',
        '5': 'google/gemini-pro',
        '6': 'meta-llama/llama-3.1-70b-instruct'
    }
    
    model = model_map.get(model_choice, model_choice if model_choice else 'anthropic/claude-3.5-sonnet')
    
    input_jsonl = input("\n📄 Input JSONL (output'u boş olan sorular): ").strip()
    ngram_json = input("📊 N-gram JSON dosyası: ").strip()
    
    output_jsonl = input("\n💾 Output JSONL dosya adı (varsayılan: LLMQADataSet.jsonl): ").strip()
    if not output_jsonl:
        output_jsonl = "LLMQADataSet.jsonl"
    
    delay = input("\n⏱️ İstekler arası bekleme (saniye, varsayılan 1.5): ").strip()
    delay = float(delay) if delay else 1.5
    
    # Özet göster
    print(f"\n{'='*70}")
    print("AYARLAR ÖZETİ")
    print(f"{'='*70}")
    print(f"🤖 Model: {model}")
    print(f"📥 Input: {input_jsonl}")
    print(f"📊 N-gram: {ngram_json}")
    print(f"💾 Output: {output_jsonl}")
    print(f"⏱️ Bekleme: {delay} saniye")
    print(f"{'='*70}\n")
    
    confirm = input("❓ Başlatmak istiyor musunuz? (e/h): ").strip().lower()
    
    if confirm == 'e':
        process_dataset(
            input_jsonl=input_jsonl,
            ngram_json=ngram_json,
            output_jsonl=output_jsonl,
            api_key=api_key,
            model=model,
            delay=delay
        )
    else:
        print("\n✗ İşlem iptal edildi.\n")