import urllib.parse
import json
import aria2p
import time
import subprocess
import requests
import sys
import os

# Cấu hình danh sách các đuôi file AN TOÀN (Phim & Phụ đề)
SAFE_EXTENSIONS = {
    '.mp4', '.mkv', '.avi', '.mov', '.flv', '.wmv', '.webm', # Video
    '.srt', '.ass', '.sub', '.vtt',                         # Phụ đề
    '.nfo', '.txt'                                          # Thông tin (thường an toàn)
}

def clean_up_torrent_folder(folder_path):
    """
    Hàm này sẽ quét thư mục và xóa mọi file không nằm trong danh sách an toàn.
    """
    print(f"\n--- Đang bắt đầu quá trình lọc file tại: {folder_path} ---")
    files_deleted = 0
    files_kept = 0

    # os.walk giúp quét sạch cả các thư mục con bên trong
    for root, dirs, files in os.walk(folder_path, topdown=False):
        for name in files:
            file_path = os.path.join(root, name)
            extension = os.path.splitext(name)[1].lower()

            if extension in SAFE_EXTENSIONS:
                print(f"[GIỮ LẠI]: {name}")
                files_kept += 1
            else:
                try:
                    os.remove(file_path)
                    print(f"[ĐÃ XÓA NGUY HIỂM/RÁC]: {name}")
                    files_deleted += 1
                except Exception as e:
                    print(f"[LỖI XÓA]: {name} - {e}")

        # Sau khi xóa file, nếu thư mục trống thì xóa luôn thư mục đó
        if not os.listdir(root) and root != folder_path:
            os.rmdir(root)
            print(f"[XÓA THƯ MỤC TRỐNG]: {os.path.basename(root)}")

    print(f"\n=> Hoàn tất dọn dẹp: Đã giữ {files_kept} file phim/sub, đã xóa {files_deleted} file lạ.")

def get_json_data(keyword):
    headers = {'User-Agent': 'Mozilla/5.0'}
    url = f"https://apibay.org/q.php?q={keyword}&cat="
    try:
        response = requests.get(url, headers=headers)
        return response.json() if response.status_code == 200 else None
    except: return None

def generate_magnet_link(info_hash, name):
    magnet = f"magnet:?xt=urn:btih:{info_hash}&dn={urllib.parse.quote(name)}"
    trackers = ['udp://tracker.opentrackr.org:1337/announce', 'udp://open.stealth.si:80/announce']
    for tr in trackers: magnet += f"&tr={urllib.parse.quote(tr)}"
    return magnet

# 1. Khởi tạo thư mục tải về
QUARANTINE_DIR = os.path.abspath("./Phim_Da_Loc")
if not os.path.exists(QUARANTINE_DIR):
    os.makedirs(QUARANTINE_DIR)

print("--- TOOL TẢI PHIM AN TOÀN ---")
keyword = input("Nhập tên phim muốn tìm: ")
results = get_json_data(keyword)

if not results or results[0].get('id') == '0':
    print("Không tìm thấy phim."); sys.exit(0)

torrent_info = results[0]
final_link = generate_magnet_link(torrent_info["info_hash"], torrent_info["name"])

aria_process = subprocess.Popen(
    ['aria2c', '--enable-rpc', '--rpc-listen-all=true'],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
)
time.sleep(2)

try:
    aria2 = aria2p.API(aria2p.Client(host="http://localhost", port=6800))
    download = aria2.add_magnet(final_link, options={'dir': QUARANTINE_DIR})
    
    print(f"Đang tải vào: {QUARANTINE_DIR}")
    
    while True:
        time.sleep(1)
        download.update()
        if download.followed_by_ids:
            download = aria2.get_download(download.followed_by_ids[0])
            continue
        
        if download.is_complete: break
        print(f"Tiến độ: {download.progress_string()} | Tốc độ: {download.download_speed_string()}", end='\r')

    print("\n\n[1] Tải xong!")
    
    # 2. Thực hiện dọn dẹp file ngay sau khi tải xong
    # Lấy đường dẫn thư mục thực tế của phim (vì torrent thường tạo folder con)
    actual_path = download.dir
    clean_up_torrent_folder(actual_path)

    print("\nChúc bạn xem phim vui vẻ và an toàn!")

finally:
    aria_process.terminate()    