import aria2p
import subprocess
import time
import os
import threading

class DownloadManager:
    def __init__(self, download_dir):
        self.download_dir = os.path.abspath(download_dir)
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
        self.aria_process = None
        self.aria2 = None
        self.is_downloading = False

    def start_aria2(self):
        if not self.aria_process:
            self.aria_process = subprocess.Popen(
                ['aria2c', '--enable-rpc', '--rpc-listen-all=true'],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            time.sleep(2)
            self.aria2 = aria2p.API(aria2p.Client(host="http://localhost", port=6800))

    def stop_aria2(self):
        if self.aria_process:
            self.aria_process.terminate()
            self.aria_process = None
        self.is_downloading = False

    def download(self, magnet_link, progress_callback, complete_callback):
        self.is_downloading = True
        try:
            self.start_aria2()
            download_obj = self.aria2.add_magnet(magnet_link, options={'dir': self.download_dir})
            while self.is_downloading:
                time.sleep(1)
                download_obj.update()
                if download_obj.followed_by_ids:
                    download_obj = self.aria2.get_download(download_obj.followed_by_ids[0])
                    continue
                if download_obj.is_complete:
                    complete_callback(download_obj.dir)
                    break
                progress_callback(download_obj.progress_string(), download_obj.download_speed_string())
        except Exception as e:
            progress_callback(f"Error: {str(e)}", "0 KB/s")
        finally:
            self.is_downloading = False

    def download_async(self, magnet_link, progress_callback, complete_callback):
        thread = threading.Thread(
            target=self.download, 
            args=(magnet_link, progress_callback, complete_callback),
            daemon=True
        )
        thread.start()