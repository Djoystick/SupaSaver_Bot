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
        print(f"yt-dlp download failed, error: {e}")
        # Fallback на локальную библиотеку pytubefix (умеет обходить блокировки Android/iOS внутри себя)
        print("Trying pytubefix as fallback...")
        try:
            from pytubefix import YouTube
            yt = YouTube(url, client='ANDROID')
            
            # Выбираем поток (stream)
            if format_code == "best":
                # Для 1080p нужно скачивать видео и аудио отдельно, но для простоты 
                # попробуем взять лучший готовый поток (обычно 720p)
                stream = yt.streams.get_highest_resolution()
            else:
                stream = yt.streams.get_highest_resolution()
                
            if stream:
                print(f"pytubefix success, downloading to {output_path}...")
                stream.download(filename=output_path)
                return
            else:
                raise Exception("pytubefix не нашел подходящих потоков.")
        except Exception as e:
            print(f"pytubefix failed: {e}")
            raise Exception("Все методы скачивания (yt-dlp, pytubefix) заблокированы YouTube на этом сервере.")
