import os
import re
from collections import Counter
import nltk
from nltk import ngrams
import json

# Türkçe için gerekli NLTK verilerini indir
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

# Türkçe stopwords yükle
try:
    from nltk.corpus import stopwords
    turkish_stopwords = set(stopwords.words('turkish'))
except:
    print("⚠ Türkçe stopwords yüklenemedi, temel liste kullanılıyor")
    turkish_stopwords = {
        've', 'bir', 'bu', 'o', 'için', 'ile', 'de', 'da', 'mi', 'mu', 
        'mı', 'mü', 'gibi', 'ki', 'daha', 'ne', 'ya', 'her', 'ben'
    }

def clean_text(text):
    """Metni temizler ve normalize eder"""
    text = text.lower()
    text = re.sub(r'[^a-züğışöçıİĞŞÖÇÜ\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def get_tokens(text, remove_stopwords=True):
    """Metni token'lara ayırır"""
    text = clean_text(text)
    tokens = text.split()
    
    if remove_stopwords:
        tokens = [t for t in tokens if t not in turkish_stopwords and len(t) > 2]
    
    return tokens

def get_ngrams_from_text(text, n=1):
    """Metinden n-gramları çıkarır"""
    tokens = get_tokens(text)
    if n == 1:
        return tokens
    else:
        n_grams = list(ngrams(tokens, n))
        return [' '.join(gram) for gram in n_grams]

def extract_top_ngrams(folder_path, top_n=100):
    """Klasördeki tüm şarkılardan top N n-gramları çıkarır"""
    
    print(f"\n{'='*60}")
    print(f"TOP {top_n} N-GRAM ÇIKARMA")
    print(f"{'='*60}\n")
    
    # Tüm txt dosyalarını oku
    all_text = ""
    txt_files = [f for f in os.listdir(folder_path) if f.endswith('.txt')]
    
    if not txt_files:
        print(f"✗ {folder_path} klasöründe txt dosyası bulunamadı!")
        return None
    
    print(f"📁 {len(txt_files)} şarkı dosyası bulundu")
    
    for filename in txt_files:
        filepath = os.path.join(folder_path, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                all_text += f.read() + " "
        except Exception as e:
            print(f"✗ Dosya okuma hatası ({filename}): {e}")
    
    if not all_text.strip():
        print("✗ Hiç metin bulunamadı!")
        return None
    
    print("🔍 N-gramlar çıkarılıyor...\n")
    
    # N-gramları çıkar
    unigrams = get_ngrams_from_text(all_text, n=1)
    bigrams = get_ngrams_from_text(all_text, n=2)
    trigrams = get_ngrams_from_text(all_text, n=3)
    
    # Frekansları hesapla
    unigram_freq = Counter(unigrams)
    bigram_freq = Counter(bigrams)
    trigram_freq = Counter(trigrams)
    
    # Top N'i al
    top_unigrams = unigram_freq.most_common(top_n)
    top_bigrams = bigram_freq.most_common(top_n)
    top_trigrams = trigram_freq.most_common(top_n)
    
    # Sonuçları hazırla
    results = {
        "metadata": {
            "total_songs": len(txt_files),
            "top_n": top_n,
            "total_unique_unigrams": len(unigram_freq),
            "total_unique_bigrams": len(bigram_freq),
            "total_unique_trigrams": len(trigram_freq)
        },
        "top_1000_unigrams": [
            {"rank": i+1, "word": word, "frequency": count}
            for i, (word, count) in enumerate(top_unigrams)
        ],
        "top_1000_bigrams": [
            {"rank": i+1, "phrase": phrase, "frequency": count}
            for i, (phrase, count) in enumerate(top_bigrams)
        ],
        "top_1000_trigrams": [
            {"rank": i+1, "phrase": phrase, "frequency": count}
            for i, (phrase, count) in enumerate(top_trigrams)
        ]
    }
    
    return results

def save_results(results, output_file='top_1000_ngrams.json'):
    """Sonuçları JSON ve TXT olarak kaydet"""
    
    # JSON formatında kaydet
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"✓ JSON kaydedildi: {output_file}")
    
    # Okunabilir TXT formatında kaydet
    txt_file = output_file.replace('.json', '.txt')
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write("="*60 + "\n")
        f.write("TOP 1000 N-GRAM ANALİZ SONUÇLARI\n")
        f.write("="*60 + "\n\n")
        
        f.write(f"Toplam Şarkı: {results['metadata']['total_songs']}\n")
        f.write(f"Toplam Benzersiz Unigram: {results['metadata']['total_unique_unigrams']:,}\n")
        f.write(f"Toplam Benzersiz Bigram: {results['metadata']['total_unique_bigrams']:,}\n")
        f.write(f"Toplam Benzersiz Trigram: {results['metadata']['total_unique_trigrams']:,}\n\n")
        
        # Unigrams
        f.write("="*60 + "\n")
        f.write("TOP 1000 UNIGRAMS (TEK KELİMELER)\n")
        f.write("="*60 + "\n\n")
        for item in results['top_1000_unigrams']:
            f.write(f"{item['rank']:3d}. {item['word']:30s} ({item['frequency']:5d}x)\n")
        
        # Bigrams
        f.write("\n" + "="*60 + "\n")
        f.write("TOP 1000 BIGRAMS (İKİLİ KELIME GRUPLARI)\n")
        f.write("="*60 + "\n\n")
        for item in results['top_1000_bigrams']:
            f.write(f"{item['rank']:3d}. {item['phrase']:40s} ({item['frequency']:5d}x)\n")
        
        # Trigrams
        f.write("\n" + "="*60 + "\n")
        f.write("TOP 1000 TRIGRAMS (ÜÇLÜ KELIME GRUPLARI)\n")
        f.write("="*60 + "\n\n")
        for item in results['top_1000_trigrams']:
            f.write(f"{item['rank']:3d}. {item['phrase']:50s} ({item['frequency']:5d}x)\n")
    
    print(f"✓ TXT kaydedildi: {txt_file}")

def print_summary(results):
    """Özet bilgileri ekrana yazdır"""
    
    print("\n" + "="*60)
    print("ÖZET BİLGİLER")
    print("="*60)
    
    print(f"\n📊 Toplam Şarkı: {results['metadata']['total_songs']}")
    print(f"📚 Toplam Benzersiz Unigram: {results['metadata']['total_unique_unigrams']:,}")
    print(f"📚 Toplam Benzersiz Bigram: {results['metadata']['total_unique_bigrams']:,}")
    print(f"📚 Toplam Benzersiz Trigram: {results['metadata']['total_unique_trigrams']:,}")
    
    print(f"\n🏆 EN SIK KULLANILAN 10 KELİME:")
    for item in results['top_1000_unigrams'][:10]:
        print(f"   {item['rank']:2d}. {item['word']:20s} ({item['frequency']:4d}x)")
    
    print(f"\n🏆 EN SIK KULLANILAN 10 İFADE (2'Lİ):")
    for item in results['top_1000_bigrams'][:10]:
        print(f"   {item['rank']:2d}. \"{item['phrase']:30s}\" ({item['frequency']:4d}x)")
    
    print(f"\n🏆 EN SIK KULLANILAN 10 İFADE (3'LÜ):")
    for item in results['top_1000_trigrams'][:10]:
        print(f"   {item['rank']:2d}. \"{item['phrase']:35s}\" ({item['frequency']:4d}x)")
    
    print("\n" + "="*60)

# ============== ANA PROGRAM ==============

if __name__ == "__main__":
    # Klasör yolu
    FOLDER_PATH = r"C:\Users\Hp\Desktop\LoRA Finetune\Phase 1 - Web Scrapping\song"
    
    print("\n" + "="*60)
    print("TOP 1000 N-GRAM ÇIKARICI")
    print("="*60)
    
    # Klasör kontrolü
    if not os.path.exists(FOLDER_PATH):
        print(f"✗ HATA: '{FOLDER_PATH}' klasörü bulunamadı!")
        print("Lütfen klasör yolunu kontrol edin.")
        exit()
    
    # N-gramları çıkar
    results = extract_top_ngrams(FOLDER_PATH, top_n=1000)
    
    if results:
        # Sonuçları kaydet
        save_results(results)
        
        # Özet göster
        print_summary(results)
        
        print("\n✓ Tüm işlemler tamamlandı!")
        print("\n📄 Oluşturulan dosyalar:")
        print("   1. top_1000_ngrams.json - JSON formatında veri")
        print("   2. top_1000_ngrams.txt - Okunabilir metin formatı")
    else:
        print("\n✗ İşlem başarısız!")