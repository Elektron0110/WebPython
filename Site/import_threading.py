import threading
import yt_dlp
import logging
import random
import string
import datetime
from my_lib import Log, file_to_list

logging = Log('Down.log')
folder = file_to_list('links.helpfile', sort=False)[0]


def load(video_url: tuple[str]):
    vurl = ""
    for s in video_url:
        vurl += s
    print(vurl)

    def download_video(v_url: str):
        try:
            timestr = datetime.datetime.now().strftime('%d%m%Y_%H%M%S_%f')[:-4]
            random_suffix = ''.join(random.choices(
                string.ascii_letters + string.digits, k=4))

            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(v_url, download=False)
                title = info.get('title', 'video').strip().replace(
                    '/', '_').replace('\\', '_').replace('#', '_')
            filename_base = f"{title}_{timestr}_{random_suffix}"

            outtmpl = f'{folder}/{filename_base}.mp4'

            ydl_opts = {
                'outtmpl': outtmpl,
                'quiet': True,
                'no_warnings': True,
                'logtostderr': False,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([v_url])

            logging.log(f'[{datetime.now().strftime("%d.%m.%Y %H:%M:%S")}]  "[{v_url}] Успешно"')

        except Exception as e:
            logging.log(f'[{datetime.now().strftime("%d.%m.%Y %H:%M:%S")}]  "[{v_url}] Ошибка: {e}"')

    t = threading.Thread(target=download_video, args=(vurl,))
    t.daemon = True
    t.start()
