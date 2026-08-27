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
        import requests
        import random
        # Пытаемся получить список прокси
        try:
            proxy_url = "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=3000&country=all&ssl=all&anonymity=elite"
            r = requests.get(proxy_url, timeout=10)
            proxies_list = [p for p in r.text.strip().split('\r\n') if p]
        except:
            proxies_list = []

        ydl_opts_base = {
            'format': format_code,
            'outtmpl': output_path,
            'quiet': True,
            'noplaylist': True,
            'extractor_args': {'youtube': ['player_client=android,ios']},
            'merge_output_format': 'mp4'
        }

        success = False
        if proxies_list:
            print("Trying yt-dlp with free proxies...")
            for _ in range(3):
                proxy_ip = random.choice(proxies_list)
                print(f"yt-dlp proxy: {proxy_ip}")
                ydl_opts = ydl_opts_base.copy()
                ydl_opts['proxy'] = f"http://{proxy_ip}"
                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([url])
                        success = True
                        break
                except Exception as e:
                    print(f"yt-dlp proxy {proxy_ip} failed: {e}")
                    continue
        
        if not success:
            print("Trying yt-dlp without proxy...")
            with yt_dlp.YoutubeDL(ydl_opts_base) as ydl:
                ydl.download([url])

    except Exception as e:
        print(f"yt-dlp download failed, error: {e}")
        # Fallback на локальную библиотеку pytubefix (с использованием бесплатных прокси)
        print("Trying pytubefix with free proxies...")
        try:
            from pytubefix import YouTube
            import random
            import requests
            
            # Получаем свежий список элитных прокси
            proxy_url = "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=3000&country=all&ssl=all&anonymity=elite"
            r = requests.get(proxy_url, timeout=10)
            proxies_list = [p for p in r.text.strip().split('\r\n') if p]
            
            if proxies_list:
                # Пробуем до 3 случайных прокси
                for _ in range(3):
                    proxy_ip = random.choice(proxies_list)
                    proxy = {"http": f"http://{proxy_ip}", "https": f"http://{proxy_ip}"}
                    print(f"Testing proxy: {proxy_ip}")
                    try:
                        yt = YouTube(url, client='ANDROID', proxies=proxy)
                        stream = yt.streams.get_highest_resolution()
                        if stream:
                            print(f"pytubefix success with proxy, downloading to {output_path}...")
                            stream.download(filename=output_path)
                            return
                    except Exception as pe:
                        print(f"Proxy {proxy_ip} failed: {pe}")
                        continue
            
            # Если прокси не помогли, пробуем без них (вдруг повезет)
            yt = YouTube(url, client='ANDROID')
            stream = yt.streams.get_highest_resolution()
            if stream:
                stream.download(filename=output_path)
                return
            else:
                raise Exception("pytubefix не нашел подходящих потоков.")
        except Exception as e:
            print(f"pytubefix failed: {e}")
            raise Exception("Все методы скачивания (yt-dlp, pytubefix) заблокированы YouTube на этом сервере.")
