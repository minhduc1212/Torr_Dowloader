import customtkinter as ctk
from src.torrent_api import TorrentAPI
from src.file_manager import FileManager
from src.download_manager import DownloadManager

class SafeMovieDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Safe Movie Downloader")
        self.geometry("650x550")

        self.download_manager = DownloadManager("./Filtered_Movies")

        # UI Elements Configuration
        self.label = ctk.CTkLabel(self, text="Safe Movie Downloader Tool", font=ctk.CTkFont(size=22, weight="bold"))
        self.label.pack(pady=20)

        self.search_frame = ctk.CTkFrame(self)
        self.search_frame.pack(pady=10, padx=20, fill="x")

        self.search_entry = ctk.CTkEntry(self.search_frame, placeholder_text="Enter movie name to search...", height=35)
        self.search_entry.pack(side="left", expand=True, fill="x", padx=(10, 10), pady=10)

        self.search_button = ctk.CTkButton(self.search_frame, text="Search & Download", command=self.on_search, height=35)
        self.search_button.pack(side="right", padx=(0, 10), pady=10)

        self.status_label = ctk.CTkLabel(self, text="Ready", text_color="gray")
        self.status_label.pack(pady=5)

        self.progress_bar = ctk.CTkProgressBar(self)
        self.progress_bar.pack(pady=10, padx=20, fill="x")
        self.progress_bar.set(0)

        self.log_textbox = ctk.CTkTextbox(self, state="disabled", height=200)
        self.log_textbox.pack(pady=10, padx=20, fill="both", expand=True)

    def log(self, message):
        """Appends a message to the UI log output box."""
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", message + "\n")
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")

    def on_search(self):
        keyword = self.search_entry.get().strip()
        if not keyword:
            self.status_label.configure(text="Please enter a movie name.", text_color="red")
            return

        self.status_label.configure(text=f"Searching for '{keyword}'...", text_color="white")
        self.search_button.configure(state="disabled")
        self.log(f"\n--- Searching for: {keyword} ---")

        results = TorrentAPI.search_movie(keyword)
        if not results:
            self.status_label.configure(text="Movie not found.", text_color="red")
            self.search_button.configure(state="normal")
            return

        torrent_info = results[0]
        self.log(f"Found: {torrent_info['name']}")
        
        magnet_link = TorrentAPI.generate_magnet_link(torrent_info["info_hash"], torrent_info["name"])
        
        self.status_label.configure(text="Starting download...", text_color="green")
        self.progress_bar.set(0)
        self.progress_bar.start()

        self.download_manager.download_async(
            magnet_link, 
            progress_callback=self.update_progress, 
            complete_callback=self.on_download_complete
        )

    def update_progress(self, progress_str, speed_str):
        # Safely pass callback data back to main thread
        self.after(0, self._update_progress_ui, progress_str, speed_str)

    def _update_progress_ui(self, progress_str, speed_str):
        self.status_label.configure(text=f"Progress: {progress_str} | Speed: {speed_str}", text_color="cyan")
        try:
            self.progress_bar.stop()
            self.progress_bar.set(float(progress_str.strip('%')) / 100.0)
        except ValueError:
            pass

    def on_download_complete(self, download_dir):
        # Safely pass callback data back to main thread
        self.after(0, self._on_download_complete_ui, download_dir)

    def _on_download_complete_ui(self, download_dir):
        self.progress_bar.stop()
        self.progress_bar.set(1.0)
        self.status_label.configure(text="Download complete! Cleaning up...", text_color="green")
        self.log("\n[1] Download complete!")
        
        FileManager.clean_up_torrent_folder(download_dir, log_callback=self.log)
        
        self.status_label.configure(text="Enjoy your safe movie watching!", text_color="green")
        self.search_button.configure(state="normal")

    def destroy(self):
        # Make sure aria2 terminates cleanly when window closes
        self.download_manager.stop_aria2()
        super().destroy()