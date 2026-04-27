import requests
import urllib.parse

class TorrentAPI:
    @staticmethod
    def search_movie(keyword):
        headers = {'User-Agent': 'Mozilla/5.0'}
        url = f"https://apibay.org/q.php?q={keyword}&cat="
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                if data and data[0].get('id') != '0':
                    return data
        except Exception:
            pass
        return None

    @staticmethod
    def generate_magnet_link(info_hash, name):
        magnet = f"magnet:?xt=urn:btih:{info_hash}&dn={urllib.parse.quote(name)}"
        trackers = ['udp://tracker.opentrackr.org:1337/announce', 'udp://open.stealth.si:80/announce']
        for tr in trackers: magnet += f"&tr={urllib.parse.quote(tr)}"
        return magnet