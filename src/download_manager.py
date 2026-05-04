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
        self.current_download = None

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

    def pause_download(self):
        if self.current_download:
            try:
                self.current_download.pause()
                return True
            except Exception:
                return False
        return False

    def resume_download(self):
        if self.current_download:
            try:
                self.current_download.resume()
                return True
            except Exception:
                return False
        return False

    def cancel_download(self):
        self.is_downloading = False
        if self.current_download:
            try:
                self.current_download.remove(force=True, files=True)
                self.current_download = None
                return True
            except Exception:
                return False
        return False

    def stop_seeding(self):
        if self.current_download:
            try:
                self.current_download.remove(force=True, files=False)
                self.current_download = None
                return True
            except Exception:
                return False
        return False

    def download(self, magnet_link, progress_callback, complete_callback):
        self.is_downloading = True
        try:
            self.start_aria2()
            self.current_download = self.aria2.add_magnet(magnet_link, options={'dir': self.download_dir})

            while self.is_downloading:
                time.sleep(1)
                if not self.current_download:
                    break

                self.current_download.update()

                if self.current_download.followed_by_ids:
                    self.current_download = self.aria2.get_download(self.current_download.followed_by_ids[0])
                    continue

                status = self.current_download.status
                progress = self.current_download.progress
                num_seeders = getattr(self.current_download, 'num_seeders', 0)
                connections = getattr(self.current_download, 'connections', 0)
                stats = f"S:{num_seeders} C:{connections}"

                # Detect seeding: progress is 100 but status is still active (not complete)
                if progress >= 100 and status == "active" and self.current_download.is_torrent:
                    progress_callback("Seeding", stats)
                    continue

                if self.current_download.is_complete:
                    complete_callback(self.current_download.dir)
                    break

                if status == "paused":
                    progress_callback("Paused", stats)
                else:
                    speed = self.current_download.download_speed_string()
                    progress_callback(self.current_download.progress_string(), f"{speed} | {stats}")

        except Exception as e:
            if self.is_downloading:
                progress_callback(f"Error: {str(e)}", "0 KB/s")
        finally:
            self.is_downloading = False
            self.current_download = None

    def download_async(self, magnet_link, progress_callback, complete_callback):
        thread = threading.Thread(
            target=self.download, 
            args=(magnet_link, progress_callback, complete_callback),
            daemon=True
        )
        thread.start()