# Proje Genel İşleyişi ve Uygulanan Teknikler

Bu döküman, projenin genel işleyişini ve her aşamada uygulanan teknikleri adım adım özetlemektedir.

## 1. Web Scraping (Aşama 1)
- **Amaç:** Sagopa'nın şarkı sözlerini internetten toplamak.
- **Teknikler:**
  - Python ile web scraping (webScrapper.py)
  - Sonuçlar CSV dosyasına ve metin dosyalarına kaydedildi.
  - Her şarkı için ayrı .txt dosyası oluşturuldu.

## 2. N-Gram Analizi (Aşama 2)
- **Amaç:** Şarkı sözlerinde en sık geçen kelime ve kelime gruplarını (n-gram) bulmak.
- **Teknikler:**
  - NLTK kütüphanesi ile n-gram çıkarımı (createN-Grams.py)
  - En sık geçen 1000 n-gram JSON ve TXT olarak kaydedildi.

## 3. Soru-Cevap Veri Seti Hazırlama (Aşama 3)
- **Amaç:** LLM tabanlı, şarkıcıya özgü dil frekansına dayalı QA veri seti oluşturmak.
- **Teknikler:**
  - Python ile veri seti oluşturma ve düzenleme (DataSetCreator.py, fix_dataset_encoding.py)
  - JSONL formatında LoRA için hazır veri seti üretildi.
  - Boş/eksik sorular tespit edilip ayrı dosyada toplandı.

## 4. LoRA ile İnce Ayar (Aşama 4)
- **Amaç:** LLM modelini Sagopa'nın diline uygun şekilde ince ayar yapmak.
- **Teknikler:**
  - LoRA (Low-Rank Adaptation) yöntemiyle model fine-tuning
  - Jupyter Notebook ile eğitim süreci (Fine_Tune_by_LoRA (1).ipynb)
  - Eğitim çıktıları ve model dosyaları ayrı klasörde saklandı.

## 5. Modelin GGUF Formatına Dönüştürülmesi (Aşama 6)
- **Amaç:** İnce ayar yapılan modeli GGUF formatına dönüştürmek ve kullanıma hazır hale getirmek.
- **Teknikler:**
  - Python script ile model dönüştürme (chat.py)
  - Son model ve ilgili dosyalar ayrı klasörde tutuldu.

## Ek Bilgiler
- Her aşama için açıklayıcı .md dosyaları ve çıktı dosyaları ilgili klasörlerde yer almaktadır.
- Proje adım adım ilerleyerek, ham veriden özel bir LLM modeline kadar tüm süreci kapsamaktadır.
