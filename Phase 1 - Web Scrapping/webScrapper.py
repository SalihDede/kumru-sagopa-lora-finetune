import requests
from bs4 import BeautifulSoup
import csv
import time
import re

# User-Agent ekleyelim (bazı siteler bunu kontrol eder)
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

def get_song_list(url):
    """Şarkı listesini ve URL'lerini çeker"""
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        songs = []
        # #listAlbum içindeki tüm linkleri bul
        list_album = soup.select('#listAlbum a')
        
        for link in list_album:
            song_name = link.text.strip()
            song_url = link.get('href')
            
            # Relative URL ise tam URL'e çevir
            if song_url and not song_url.startswith('http'):
                song_url = 'https://www.azlyrics.com' + song_url
            
            if song_name and song_url:
                songs.append({
                    'name': song_name,
                    'url': song_url
                })
        
        print(f"✓ {len(songs)} şarkı bulundu")
        return songs
    
    except Exception as e:
        print(f"✗ Hata: {e}")
        return []

def save_to_csv(songs, filename='sagopaSongs.csv'):
    """Şarkı listesini CSV'ye kaydeder"""
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['name', 'url'])
            writer.writeheader()
            writer.writerows(songs)
        print(f"✓ {filename} oluşturuldu")
    except Exception as e:
        print(f"✗ CSV kaydetme hatası: {e}")

def get_lyrics(song_url):
    """Şarkı sözlerini çeker"""
    try:
        time.sleep(2)  # Rate limiting - siteye yük bindirmemek için
        response = requests.get(song_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Belirtilen selector'ı dene
        lyrics_div = soup.select_one('br + div')
        
        if lyrics_div:
            # Script ve diğer istenmeyen etiketleri temizle
            for tag in lyrics_div(['script', 'style']):
                tag.decompose()
            
            lyrics = lyrics_div.get_text(strip=True, separator='\n')
            return lyrics
        else:
            print("  ⚠ Şarkı sözleri bulunamadı")
            return None
            
    except Exception as e:
        print(f"  ✗ Hata: {e}")
        return None

def sanitize_filename(name):
    """Dosya adı için güvenli string oluşturur"""
    # Özel karakterleri temizle
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    # Boşlukları alt çizgi yap
    name = name.replace(' ', '_')
    return name[:50]  # Maksimum 50 karakter

def scrape_all_lyrics(csv_filename='sagopaSongs.csv'):
    """CSV'deki tüm şarkıların sözlerini çeker"""
    try:
        with open(csv_filename, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            songs = list(reader)
        
        print(f"\n{len(songs)} şarkı için sözler çekiliyor...\n")
        
        for i, song in enumerate(songs, 1):
            song_name = song['name']
            song_url = song['url']
            
            print(f"[{i}/{len(songs)}] {song_name}")
            
            lyrics = get_lyrics(song_url)
            
            if lyrics:
                filename = f"{sanitize_filename(song_name)}_lyrics_default.txt"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(lyrics)
                print(f"  ✓ {filename} kaydedildi")
            
            # Rate limiting
            time.sleep(2)
        
        print("\n✓ Tüm işlemler tamamlandı!")
        
    except FileNotFoundError:
        print(f"✗ {csv_filename} bulunamadı!")
    except Exception as e:
        print(f"✗ Hata: {e}")

# ============== ANA PROGRAM ==============

if __name__ == "__main__":
    print("=" * 50)
    print("ŞARKI SÖZLERİ SCRAPER")
    print("=" * 50)
    print("\n⚠️  DİKKAT: Bu kodu kullanmadan önce:")
    print("   - Sitenin kullanım şartlarını okuyun")
    print("   - robots.txt dosyasını kontrol edin")
    print("   - Telif hakkı yasalarına uyun")
    print("=" * 50)
    
    # 1. ADIM: Şarkı listesini al
    print("\n[1. ADIM] Şarkı listesi çekiliyor...")
    base_url = "https://www.azlyrics.com/s/sagopakajmer.html"
    songs = get_song_list(base_url)
    
    if not songs:
        print("✗ Şarkı listesi alınamadı. Program sonlandırılıyor.")
        exit()
    
    # 2. ADIM: CSV'ye kaydet
    print("\n[2. ADIM] CSV dosyası oluşturuluyor...")
    save_to_csv(songs)
    
    # 3. ADIM: Şarkı sözlerini çek
    print("\n[3. ADIM] Şarkı sözleri çekiliyor...")
    user_input = input("\nDevam etmek istiyor musunuz? (e/h): ")
    
    if user_input.lower() == 'e':
        scrape_all_lyrics()
    else:
        print("Program sonlandırıldı.")