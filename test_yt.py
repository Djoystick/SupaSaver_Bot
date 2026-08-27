import yt_dlp

url = "https://www.youtube.com/watch?v=txHlaw4Tatg&list=RDEMhBHkXKJNXUFB9oZnd1BOZQ&start_radio=1"
ydl_opts = {
    'quiet': True,
    'no_warnings': True,
    'extract_flat': False,
}
with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    try:
        info = ydl.extract_info(url, download=False)
        print("SUCCESS:", info.get('title'))
    except Exception as e:
        print("ERROR:", str(e))
