import yt_dlp

def get_video_info(url: str):
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'noplaylist': True, # Игнорируем плейлисты, если в ссылке есть &list=
        'cookiefile': 'cookies.txt', # Подключаем куки для обхода блокировок YouTube
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            return {
                'title': info.get('title', 'Без названия'),
                'thumbnail': info.get('thumbnail'),
            }
        except Exception as e:
            print(f"Error extracting info: {e}")
            return {"error": str(e)}

def download_video(url: str, format_code: str, output_path: str):
    ydl_opts = {
        'format': format_code,
        'outtmpl': output_path,
        'quiet': True,
        'noplaylist': True,
        'cookiefile': 'cookies.txt', # Подключаем куки для скачивания
        'merge_output_format': 'mp4' # ffmpeg склеит в mp4
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
