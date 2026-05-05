import customtkinter as ctk
from tkinter import ttk
import threading
from src.torrent_api import TorrentAPI
from src.file_manager import FileManager
from src.download_manager import DownloadManager

class SafeMovieDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Safe Movie Downloader")
        self.geometry("850x650")

        self.download_manager = DownloadManager("./Filtered_Movies")
        self.current_results = []
        self.current_page = 1
        self.current_keyword = ""

        # UI Elements Configuration
        self.label = ctk.CTkLabel(self, text="Safe Movie Downloader Tool", font=ctk.CTkFont(size=22, weight="bold"))
        self.label.pack(pady=20)

        self.search_frame = ctk.CTkFrame(self)
        self.search_frame.pack(pady=10, padx=20, fill="x")

        self.source_var = ctk.StringVar(value="The Pirate Bay")
        self.source_dropdown = ctk.CTkOptionMenu(self.search_frame, variable=self.source_var, values=["The Pirate Bay", "Nyaa.si"], width=140, height=35)
        self.source_dropdown.pack(side="left", padx=(10, 0), pady=10)

        self.search_entry = ctk.CTkEntry(self.search_frame, placeholder_text="Enter movie name to search...", height=35)
        self.search_entry.pack(side="left", expand=True, fill="x", padx=(10, 10), pady=10)

        self.search_button = ctk.CTkButton(self.search_frame, text="Search", command=self.on_search, height=35)
        self.search_button.pack(side="right", padx=(0, 10), pady=10)

        # Results Table
        self.results_frame = ctk.CTkFrame(self)
        self.results_frame.pack(pady=5, padx=20, fill="both", expand=True)

        self.tree = ttk.Treeview(self.results_frame, columns=("Name", "Seeders", "Leechers", "Size"), show="headings")
        self.tree.heading("Name", text="Name")
        self.tree.heading("Seeders", text="Seeders")
        self.tree.heading("Leechers", text="Leechers")
        self.tree.heading("Size", text="Size")
        
        self.tree.column("Name", width=450)
        self.tree.column("Seeders", width=70, anchor="center")
        self.tree.column("Leechers", width=70, anchor="center")
        self.tree.column("Size", width=100, anchor="center")
        
        self.tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        
        self.scrollbar = ttk.Scrollbar(self.results_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y", pady=10, padx=(0, 10))

        # Pagination Controls
        self.pagination_frame = ctk.CTkFrame(self)
        self.pagination_frame.pack(pady=5)

        self.prev_button = ctk.CTkButton(self.pagination_frame, text="< Previous", command=self.on_prev_page, width=100, state="disabled")
        self.prev_button.pack(side="left", padx=10)

        self.page_label = ctk.CTkLabel(self.pagination_frame, text="Page: 1", font=ctk.CTkFont(size=14))
        self.page_label.pack(side="left", padx=10)

        self.next_button = ctk.CTkButton(self.pagination_frame, text="Next >", command=self.on_next_page, width=100, state="disabled")
        self.next_button.pack(side="left", padx=10)

        self.controls_frame = ctk.CTkFrame(self)
        self.controls_frame.pack(pady=10)

        self.download_button = ctk.CTkButton(self.controls_frame, text="Download Selected", command=self.on_download_selected, state="disabled")
        self.download_button.pack(side="left", padx=5)

        self.pause_button = ctk.CTkButton(self.controls_frame, text="Pause", command=self.on_pause_resume, state="disabled")
        self.pause_button.pack(side="left", padx=5)

        self.cancel_button = ctk.CTkButton(self.controls_frame, text="Cancel", command=self.on_cancel, state="disabled")
        self.cancel_button.pack(side="left", padx=5)

        self.stop_seeder_button = ctk.CTkButton(self.controls_frame, text="Stop Seeder", command=self.on_stop_seeder, state="disabled")
        self.stop_seeder_button.pack(side="left", padx=5)

        self.status_label = ctk.CTkLabel(self, text="Ready", text_color="gray")
        self.status_label.pack(pady=5)

        self.progress_bar = ctk.CTkProgressBar(self)
        self.progress_bar.pack(pady=10, padx=20, fill="x")
        self.progress_bar.set(0)

        self.log_textbox = ctk.CTkTextbox(self, state="disabled", height=150)
        self.log_textbox.pack(pady=10, padx=20, fill="both", expand=True)

        self.setup_tree_styles()

    def setup_tree_styles(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", 
                        background="#2b2b2b", 
                        foreground="white", 
                        rowheight=25, 
                        fieldbackground="#2b2b2b",
                        bordercolor="#2b2b2b",
                        borderwidth=0)
        style.map("Treeview", background=[('selected', '#1f538d')])
        style.configure("Treeview.Heading", 
                        background="#333333", 
                        foreground="white", 
                        relief="flat")
        style.map("Treeview.Heading", background=[('active', '#444444')])

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

        self.current_page = 1
        self.current_keyword = keyword
        self._execute_search()

    def on_next_page(self):
        self.current_page += 1
        self._execute_search()

    def on_prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self._execute_search()

    def _execute_search(self):
        keyword = self.current_keyword
        source = self.source_var.get()
        self.status_label.configure(text=f"Searching for '{keyword}' (Page {self.current_page}) on {source}...", text_color="white")
        self.search_button.configure(state="disabled")
        self.download_button.configure(state="disabled")
        self.next_button.configure(state="disabled")
        self.prev_button.configure(state="disabled")
        self.log(f"\n--- Searching for: {keyword} (Page {self.current_page}) on {source} ---")

        # Clear existing results
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Start search in a separate thread
        threading.Thread(target=self._perform_search, args=(keyword, source, self.current_page), daemon=True).start()

    def _perform_search(self, keyword, source, page):
        try:
            if source == "The Pirate Bay":
                # Pirate Bay doesn't use page in this simple implementation, or it uses it differently
                # For now, we only support page for Nyaa.si as requested
                results = TorrentAPI.search_movie(keyword)
            else:
                results = TorrentAPI.search_nyaa(keyword, page)
        except Exception as e:
            results = None
            self.log(f"Search error: {str(e)}")
            
        # Update UI in the main thread
        self.after(0, self._update_search_results, results, keyword)

    def _update_search_results(self, results, keyword):
        source = self.source_var.get()
        if not results:
            self.status_label.configure(text=f"No results found on page {self.current_page}.", text_color="red")
            self.search_button.configure(state="normal")
            if self.current_page > 1:
                self.prev_button.configure(state="normal")
            self.next_button.configure(state="disabled")
            return

        self.current_results = results
        self.page_label.configure(text=f"Page: {self.current_page}")
        
        for idx, res in enumerate(results):
            # ... existing result processing ...
            name = res.get('name', 'Unknown')
            seeders = res.get('seeders', 'N/A')
            leechers = res.get('leechers', 'N/A')
            size = res.get('size', 'N/A')
            if size != 'N/A':
                try:
                    # Check if size is already a string with units (like from Nyaa)
                    if isinstance(size, str) and any(unit in size for unit in ['GiB', 'MiB', 'KiB', 'GB', 'MB', 'KB']):
                        pass 
                    else:
                        size_gb = float(size) / (1024**3)
                        size = f"{size_gb:.2f} GB"
                except:
                    pass
            
            self.tree.insert("", "end", iid=idx, values=(name, seeders, leechers, size))
            
        self.download_button.configure(state="normal")
        self.search_button.configure(state="normal")
        
        # Enable/Disable pagination buttons
        if source == "Nyaa.si":
            self.prev_button.configure(state="normal" if self.current_page > 1 else "disabled")
            self.next_button.configure(state="normal") # Assume there might be a next page unless it's empty
        else:
            self.prev_button.configure(state="disabled")
            self.next_button.configure(state="disabled")
        
        self.status_label.configure(text=f"Found {len(results)} results. Select one and click Download.", text_color="white")
        self.log(f"Found {len(results)} results for '{keyword}' on page {self.current_page}.")

    def on_download_selected(self):
        selected_item = self.tree.selection()
        if not selected_item:
            self.status_label.configure(text="Please select a torrent from the table.", text_color="yellow")
            return
            
        try:
            idx = int(selected_item[0])
            torrent_info = self.current_results[idx]
        except (IndexError, ValueError):
            self.log("Error extracting selected torrent.")
            return

        self.log(f"Selected: {torrent_info['name']}")
        self.download_button.configure(state="disabled")
        self.search_button.configure(state="disabled")
        self.pause_button.configure(state="normal", text="Pause")
        self.cancel_button.configure(state="normal")
        
        if "magnet" in torrent_info:
            magnet_link = torrent_info["magnet"]
        else:
            magnet_link = TorrentAPI.generate_magnet_link(torrent_info["info_hash"], torrent_info["name"])
        
        self.status_label.configure(text="Starting download...", text_color="green")
        self.progress_bar.set(0)
        self.progress_bar.start()

        self.download_manager.download_async(
            magnet_link, 
            progress_callback=self.update_progress, 
            complete_callback=self.on_download_complete
        )

    def on_pause_resume(self):
        if self.pause_button.cget("text") == "Pause":
            if self.download_manager.pause_download():
                self.pause_button.configure(text="Resume")
                self.log("Download paused.")
        else:
            if self.download_manager.resume_download():
                self.pause_button.configure(text="Pause")
                self.log("Download resumed.")

    def on_cancel(self):
        if self.download_manager.cancel_download():
            self.log("Download cancelled.")
            self.status_label.configure(text="Download cancelled.", text_color="yellow")
            self._reset_ui_after_download()

    def on_stop_seeder(self):
        # We need the download dir for cleanup
        download_dir = None
        if self.download_manager.current_download:
            download_dir = self.download_manager.current_download.dir
            
        if self.download_manager.stop_seeding():
            self.log("Seeding stopped.")
            if download_dir:
                 self.on_download_complete(download_dir)
            else:
                 self._reset_ui_after_download()

    def _reset_ui_after_download(self):
        self.progress_bar.stop()
        self.progress_bar.set(0)
        self.pause_button.configure(state="disabled", text="Pause")
        self.cancel_button.configure(state="disabled")
        self.stop_seeder_button.configure(state="disabled")
        self.search_button.configure(state="normal")
        self.download_button.configure(state="normal")

    def update_progress(self, progress_str, speed_str):
        # Safely pass callback data back to main thread
        self.after(0, self._update_progress_ui, progress_str, speed_str)

    def _update_progress_ui(self, progress_str, speed_str):
        if progress_str == "Paused":
            self.status_label.configure(text=f"Download Paused | {speed_str}", text_color="yellow")
        elif progress_str == "Seeding":
            self.status_label.configure(text=f"Seeding... | {speed_str}", text_color="green")
            self.pause_button.configure(state="disabled")
            self.cancel_button.configure(state="disabled")
            self.stop_seeder_button.configure(state="normal")
            self.progress_bar.set(1.0)
        else:
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
        self._reset_ui_after_download()

    def destroy(self):
        # Make sure aria2 terminates cleanly when window closes
        self.download_manager.stop_aria2()
        super().destroy()