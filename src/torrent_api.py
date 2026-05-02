import requests
import urllib.parse
from bs4 import BeautifulSoup

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
    def search_nyaa(keyword):
        headers = {'User-Agent': 'Mozilla/5.0'}
        url = f"https://nyaa.si/?f=0&c=1_0&q={urllib.parse.quote(keyword)}"
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                tbody = soup.select_one('div.table-responsive tbody')
                results = []
                if tbody:
                    for row in tbody.find_all('tr'):
                        title_tag = row.select_one('td[colspan="2"] a:not(.comments)')
                        title = title_tag.get('title') if title_tag else "Unknown"
                        
                        magnet_tag = row.select_one('a[href^="magnet:"]')
                        magnet_link = magnet_tag.get('href') if magnet_tag else ""
                        
                        if magnet_link:
                            results.append({
                                "name": title,
                                "magnet": magnet_link
                            })
                return results
        except Exception:
            pass
        return None

    @staticmethod
    def generate_magnet_link(info_hash, name):
        magnet = f"magnet:?xt=urn:btih:{info_hash}&dn={urllib.parse.quote(name)}"
        trackers = ['udp://tracker.opentrackr.org:1337/announce', 'udp://open.stealth.si:80/announce']
        for tr in trackers: magnet += f"&tr={urllib.parse.quote(tr)}"
        return magnet