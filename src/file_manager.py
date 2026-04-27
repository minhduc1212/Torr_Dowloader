import os

SAFE_EXTENSIONS = {
    '.mp4', '.mkv', '.avi', '.mov', '.flv', '.wmv', '.webm', # Video
    '.srt', '.ass', '.sub', '.vtt',                         # Subtitles
    '.nfo', '.txt'                                          # Info
}

class FileManager:
    @staticmethod
    def clean_up_torrent_folder(folder_path, log_callback=print):
        log_callback(f"\n--- Starting file filtering process at: {folder_path} ---")
        files_deleted = 0
        files_kept = 0

        for root, dirs, files in os.walk(folder_path, topdown=False):
            for name in files:
                file_path = os.path.join(root, name)
                extension = os.path.splitext(name)[1].lower()
                if extension in SAFE_EXTENSIONS:
                    log_callback(f"[KEPT]: {name}")
                    files_kept += 1
                else:
                    try:
                        os.remove(file_path)
                        log_callback(f"[DELETED DANGEROUS/JUNK]: {name}")
                        files_deleted += 1
                    except Exception as e:
                        log_callback(f"[DELETE ERROR]: {name} - {e}")
            if not os.listdir(root) and root != folder_path:
                os.rmdir(root)
                log_callback(f"[DELETED EMPTY DIRECTORY]: {os.path.basename(root)}")
        log_callback(f"\n=> Cleanup complete: Kept {files_kept} files, deleted {files_deleted} unknown files.")