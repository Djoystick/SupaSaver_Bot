import yt_dlp
import requests
import uuid

def get_video_info(url: str):
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'noplaylist': True,
        'extractor_args': {'youtube': ['player_client=android,ios']},
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            return {
                'title': info.get('title', 'Без названия'),
                'thumbnail': info.get('thumbnail'),
            }
        except Exception as e:
            # Fallback для получения заголовка
            print(f"yt-dlp info error: {e}")
            return {"title": "Видео из YouTube", "thumbnail": None}

def download_video(url: str, format_code: str, output_path: str):
    try:
        ydl_opts = {
            'format': format_code,
            'outtmpl': output_path,
            'quiet': True,
            'noplaylist': True,
            'extractor_args': {'youtube': ['player_client=android,ios']},
            'merge_output_format': 'mp4'
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        print(f"yt-dlp download failed, trying Cobalt API... Error: {e}")
        # Fallback на Cobalt API (совместимость с v7 и v8)
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        data = {
            "url": url,
            "vQuality": "1080" if format_code == "best" else "720", # v7
            "videoQuality": "1080" if format_code == "best" else "720" # v8
        }
        
        # Список актуальных инстансов Cobalt (смесь v7 и v8)
        instances = [
            "https://cobalt.owo.vc/",
            "https://api.cobalt.cat/",
            "https://cobalt.mirn.in/",
            "https://cobalt.owo.vc/api/json",
            "https://api.cobalt.cat/api/json"
        ]
        
        for api_url in instances:
            try:
                print(f"Trying Cobalt instance: {api_url}")
                response = requests.post(api_url, json=data, headers=headers, timeout=10)
                if response.status_code == 200:
                    result = response.json()
                    if "url" in result:
                        download_url = result["url"]
                        print(f"Cobalt success on {api_url}, downloading stream...")
                        with requests.get(download_url, stream=True) as r:
                            r.raise_for_status()
                            with open(output_path, 'wb') as f:
                                for chunk in r.iter_content(chunk_size=8192):
                                    f.write(chunk)
                        return # Успешный выход
            except Exception as e:
                print(f"Failed on {api_url}: {e}")
                continue
        
        # Если Cobalt полностью мертв, пробуем Itzpire REST API (еще один популярный бесплатный сервис)
        try:
            print("Trying Itzpire API...")
            itz_url = f"https://itzpire.com/download/youtube?url={url}"
            itz_res = requests.get(itz_url, headers=headers, timeout=15)
            if itz_res.status_code == 200:
                itz_data = itz_res.json()
                if itz_data.get("status") == "success" and "data" in itz_data:
                    video_url = itz_data["data"].get("video")
                    if video_url:
                        print("Itzpire success, downloading stream...")
                        with requests.get(video_url, stream=True) as r:
                            r.raise_for_status()
                            with open(output_path, 'wb') as f:
                                for chunk in r.iter_content(chunk_size=8192):
                                    f.write(chunk)
                        return
        except Exception as e:
            print(f"Itzpire failed: {e}")
                
        raise Exception("Все инстансы Cobalt и Itzpire недоступны или заблокированы.")
