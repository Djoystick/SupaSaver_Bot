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
        # Fallback на Cobalt API (публичные инстансы обходят блокировки IP)
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        data = {
            "url": url,
            "vQuality": "1080" if format_code == "best" else "720"
        }
        
        # Список известных публичных инстансов Cobalt (v7 API)
        instances = [
            "https://cobalt.owo.vc/api/json",
            "https://cobalt.kwiatechu.com/api/json",
            "https://api.cobalt.cat/api/json",
            "https://cobalt.mirn.in/api/json",
            "https://cobalt.canine.ly/api/json",
            "https://co.wuk.sh/api/json"
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
                
        raise Exception("Все инстансы Cobalt недоступны или заблокированы.")
