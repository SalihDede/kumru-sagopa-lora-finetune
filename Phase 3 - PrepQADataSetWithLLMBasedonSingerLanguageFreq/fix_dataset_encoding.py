#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sagopa Kajmer Dataset Encoding Düzeltme ve Temizleme Script'i
"""

import json
import sys
from pathlib import Path

def fix_encoding(input_file, output_file, min_output_length=20):
    """
    Dataset'teki encoding sorununu düzelt ve temizle
    
    Args:
        input_file: Bozuk dataset dosyası
        output_file: Düzeltilmiş dataset dosyası
        min_output_length: Minimum output uzunluğu (daha kısa olanlar atılır)
    """
    
    print("=" * 80)
    print("SAGOPA KAJMER DATASET DÜZELTİCİ")
    print("=" * 80)
    print()
    
    # Farklı encoding'leri dene
    encodings_to_try = ['utf-8', 'latin-1', 'windows-1254', 'iso-8859-9']
    
    dataset = []
    successful_encoding = None
    
    # Encoding'i bul
    print("🔍 Doğru encoding bulunuyor...")
    for enc in encodings_to_try:
        try:
            with open(input_file, 'r', encoding=enc) as f:
                lines = f.readlines()
                # İlk satırı test et
                test_data = json.loads(lines[0])
                # Türkçe karakter kontrolü
                text = test_data['input'] + test_data['output']
                if 'Ã' in text or 'Ä' in text or 'Å' in text:
                    # Hala bozuk karakterler var, doğru encoding değil
                    continue
                successful_encoding = enc
                print(f"✓ Doğru encoding bulundu: {enc}")
                break
        except:
            continue
    
    if not successful_encoding:
        # Hiçbir encoding çalışmadı, manuel düzeltme yap
        print("⚠️  Otomatik encoding bulunamadı, manuel düzeltme yapılacak...")
        successful_encoding = 'utf-8'
        manual_fix = True
    else:
        manual_fix = False
    
    print()
    print(f"📖 Dataset okunuyor: {input_file}")
    
    # Dataset'i oku
    with open(input_file, 'r', encoding=successful_encoding) as f:
        lines = f.readlines()
    
    total = len(lines)
    print(f"✓ {total} satır okundu")
    print()
    
    # İstatistikler
    stats = {
        'total': 0,
        'valid': 0,
        'empty_output': 0,
        'short_output': 0,
        'encoding_fixed': 0,
        'json_error': 0
    }
    
    print("🔧 Dataset işleniyor...")
    print("-" * 80)
    
    for i, line in enumerate(lines, 1):
        stats['total'] += 1
        
        try:
            # JSON parse
            data = json.loads(line.strip())
            
            instruction = data.get('instruction', '')
            user_input = data.get('input', '')
            output = data.get('output', '')
            
            # Manuel düzeltme gerekiyorsa
            if manual_fix:
                # UTF-8 karakterleri düzelt
                replacements = {
                    'Ä±': 'ı', 'Ä°': 'İ',
                    'ÅŸ': 'ş', 'Åž': 'Ş',
                    'Ã§': 'ç', 'Ã‡': 'Ç',
                    'ÄŸ': 'ğ', 'Äž': 'Ğ',
                    'Ã¶': 'ö', 'Ã–': 'Ö',
                    'Ã¼': 'ü', 'Ãœ': 'Ü',
                    'Ä±m': 'ım', 'Ä±n': 'ın',
                }
                
                for wrong, correct in replacements.items():
                    instruction = instruction.replace(wrong, correct)
                    user_input = user_input.replace(wrong, correct)
                    output = output.replace(wrong, correct)
                
                stats['encoding_fixed'] += 1
            
            # Boş output kontrolü
            if not output or output.strip() == '':
                stats['empty_output'] += 1
                if i <= 5:  # İlk 5'i göster
                    print(f"  ⚠️  Satır {i}: Boş output (atlandı)")
                continue
            
            # Kısa output kontrolü
            if len(output.strip()) < min_output_length:
                stats['short_output'] += 1
                if i <= 5:
                    print(f"  ⚠️  Satır {i}: Çok kısa output ({len(output)} < {min_output_length} karakter)")
                continue
            
            # Geçerli veri
            stats['valid'] += 1
            dataset.append({
                'instruction': instruction.strip(),
                'input': user_input.strip(),
                'output': output.strip()
            })
            
        except json.JSONDecodeError as e:
            stats['json_error'] += 1
            print(f"  ✗ Satır {i}: JSON parse hatası")
            continue
        except Exception as e:
            print(f"  ✗ Satır {i}: Beklenmeyen hata - {str(e)}")
            continue
    
    print("-" * 80)
    print()
    
    # Düzeltilmiş dataset'i kaydet
    print(f"💾 Düzeltilmiş dataset kaydediliyor: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        for item in dataset:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    print("✓ Kayıt tamamlandı!")
    print()
    
    # İstatistikleri göster
    print("=" * 80)
    print("📊 İSTATİSTİKLER")
    print("=" * 80)
    print(f"Toplam satır:           {stats['total']}")
    print(f"Geçerli örnekler:       {stats['valid']} ✓")
    print(f"Boş output:             {stats['empty_output']}")
    print(f"Çok kısa output:        {stats['short_output']}")
    print(f"JSON parse hatası:      {stats['json_error']}")
    if manual_fix:
        print(f"Encoding düzeltildi:    {stats['encoding_fixed']} satır")
    print()
    print(f"Başarı oranı:           {(stats['valid']/stats['total'])*100:.1f}%")
    print(f"Kaybedilen veri:        {stats['total'] - stats['valid']} örnek")
    print()
    
    # Önizleme
    print("=" * 80)
    print("📋 DÜZELTİLMİŞ VERİ ÖRNEKLERİ (İlk 3)")
    print("=" * 80)
    
    for i, item in enumerate(dataset[:3], 1):
        print(f"\n[Örnek {i}]")
        print(f"Soru:  {item['input'][:80]}...")
        print(f"Cevap: {item['output'][:100]}...")
        print("-" * 80)
    
    print()
    print("✅ İşlem tamamlandı!")
    print(f"✅ {stats['valid']} temiz örnek hazır!")
    print(f"✅ Artık LoRA eğitimi için kullanabilirsiniz!")
    print()

if __name__ == "__main__":
    # Dosya yolları
    input_file = r"C:\Users\Hp\Desktop\LoRA Finetune\Phase 3 - PrepQADataSetWithLLMBasedonSingerLanguageFreq\LoRAReadyToUseDataSet.jsonl"
    output_file = r"C:\Users\Hp\Desktop\LoRA Finetune\Phase 3 - PrepQADataSetWithLLMBasedonSingerLanguageFreq\LoRAReadyToUseDataSet_FIXED.jsonl"
    
    # Parametreler
    min_output_length = 20  # Minimum 20 karakter output
    
    print()
    print("⚙️  AYARLAR:")
    print(f"   Input:  {input_file}")
    print(f"   Output: {output_file}")
    print(f"   Min output uzunluğu: {min_output_length} karakter")
    print()
    
    try:
        fix_encoding(input_file, output_file, min_output_length)
    except FileNotFoundError:
        print(f"❌ HATA: '{input_file}' dosyası bulunamadı!")
        print("   Lütfen script'i dataset dosyasıyla aynı klasörde çalıştırın.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ HATA: {str(e)}")
        sys.exit(1)
