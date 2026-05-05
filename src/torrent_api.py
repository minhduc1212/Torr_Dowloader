import requests
import urllib.parse
from bs4 import BeautifulSoup

class TorrentAPI:
    @staticmethod
    def search_movie(keyword):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        url = f"https://apibay.org/q.php?q={urllib.parse.quote(keyword)}&cat="
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data and data[0].get('id') != '0':
                    return data
        except Exception:
            pass
        return None

    @staticmethod
    def search_nyaa(keyword, page=1):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        # Construct the exact URL as requested, adding the page parameter
        url = f"https://nyaa.si/?f=0&c=1_0&q={urllib.parse.quote_plus(keyword)}&p={page}"
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # Nyaa table uses class 'torrent-list'
                rows = soup.select('table.torrent-list tbody tr')
                if not rows:
                    return None
                
                results = []
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) < 8:
                        continue
                    
                    # Title link is the last 'a' tag in the second column (it avoids comment links)
                    title_links = cols[1].select('a:not(.comments)')
                    if not title_links:
                        continue
                    title_tag = title_links[-1]
                    title = title_tag.get('title') or title_tag.text.strip() or "Unknown"
                    
                    # Magnet link is in the third column
                    magnet_tag = cols[2].select_one('a[href^="magnet:"]')
                    magnet_link = magnet_tag.get('href') if magnet_tag else ""
                    
                    if magnet_link:
                        results.append({
                            "name": title,
                            "magnet": magnet_link,
                            "size": cols[3].text.strip(),
                            "seeders": cols[5].text.strip(),
                            "leechers": cols[6].text.strip()
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