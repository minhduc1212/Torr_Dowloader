import requests
import urllib.parse
from bs4 import BeautifulSoup
import urllib3

# Disable SSL warnings for direct IP fallback connections
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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
        url = f"https://nyaa.si/?f=0&c=1_0&q={urllib.parse.quote_plus(keyword)}&p={page}"
        html_content = None

        # Try normal request first
        try:
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                html_content = response.text
        except Exception:
            pass

        # Bypassing DNS block using Cloudflare DoH and direct IP fallback
        if not html_content:
            try:
                # Query Cloudflare DoH to resolve nyaa.si
                doh_url = "https://1.1.1.1/dns-query?name=nyaa.si&type=A"
                doh_response = requests.get(doh_url, headers={'accept': 'application/dns-json'}, timeout=5)
                if doh_response.status_code == 200:
                    answers = doh_response.json().get('Answer', [])
                    if answers:
                        resolved_ip = answers[0].get('data')
                        if resolved_ip:
                            # Connect directly to the IP, specifying Host header and bypass SSL verification
                            fallback_url = f"https://{resolved_ip}/?f=0&c=1_0&q={urllib.parse.quote_plus(keyword)}&p={page}"
                            response = requests.get(
                                fallback_url,
                                headers={'Host': 'nyaa.si', 'User-Agent': headers['User-Agent']},
                                verify=False,
                                timeout=10
                            )
                            if response.status_code == 200:
                                html_content = response.text
            except Exception:
                pass

        if not html_content:
            return None

        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            rows = soup.select('table.torrent-list tbody tr')
            if not rows:
                return None
            
            results = []
            for row in rows:
                cols = row.find_all('td')
                if len(cols) < 8:
                    continue
                
                title_links = cols[1].select('a:not(.comments)')
                if not title_links:
                    continue
                title_tag = title_links[-1]
                title = title_tag.get('title') or title_tag.text.strip() or "Unknown"
                
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
    def search_yts(keyword, page=1):
        # YTS endpoints (falling back to active mirrors if the primary fails/is blocked)
        yts_domains = ['yts.lt', 'yts.movie', 'yts.do']
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        for domain in yts_domains:
            url = f"https://{domain}/api/v2/list_movies.json?query_term={urllib.parse.quote(keyword)}&limit=50&page={page}"
            try:
                response = requests.get(url, headers=headers, timeout=8)
                if response.status_code == 200:
                    data = response.json()
                    movies = data.get('data', {}).get('movies', [])
                    if movies:
                        results = []
                        for movie in movies:
                            torrents = movie.get('torrents', [])
                            for torrent in torrents:
                                title = f"{movie.get('title')} ({movie.get('year')}) [{torrent.get('quality')}] [{torrent.get('type', '').upper()}]"
                                info_hash = torrent.get('hash', '').lower()
                                size = torrent.get('size_bytes', 0)
                                seeders = torrent.get('seeds', 0)
                                leechers = torrent.get('peers', 0)
                                magnet = TorrentAPI.generate_magnet_link(info_hash, title)
                                results.append({
                                    "name": title,
                                    "magnet": magnet,
                                    "info_hash": info_hash,
                                    "size": size,
                                    "seeders": seeders,
                                    "leechers": leechers
                                })
                        return results
            except Exception:
                continue
        return None

    @staticmethod
    def search_eztv(keyword, page=1):
        # EZTV endpoints
        eztv_domains = ['eztv.wf', 'eztv.yt']
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

        # Step 1: Look up the IMDb ID of the show via Cinemeta API
        imdb_id = None
        cinemeta_url = f"https://v3-cinemeta.strem.io/catalog/series/cinemeta-search/search={urllib.parse.quote(keyword)}.json"
        try:
            response = requests.get(cinemeta_url, headers=headers, timeout=8)
            if response.status_code == 200:
                metas = response.json().get('metas', [])
                if metas:
                    imdb_id = metas[0].get('imdb_id')
        except Exception:
            pass

        if not imdb_id:
            return None

        # Step 2: Query EZTV using the resolved IMDb ID
        for domain in eztv_domains:
            url = f"https://{domain}/api/get-torrents?limit=100&page={page}&imdb_id={imdb_id}"
            try:
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    torrents = data.get('torrents', [])
                    if torrents:
                        results = []
                        for torrent in torrents:
                            results.append({
                                "name": torrent.get('title', 'Unknown'),
                                "magnet": torrent.get('magnet_url', ''),
                                "info_hash": torrent.get('hash', '').lower(),
                                "size": torrent.get('size_bytes', 0),
                                "seeders": torrent.get('seeds', 0),
                                "leechers": torrent.get('peers', 0)
                            })
                        return results
            except Exception:
                continue
        return None

    @staticmethod
    def generate_magnet_link(info_hash, name):
        magnet = f"magnet:?xt=urn:btih:{info_hash}&dn={urllib.parse.quote(name)}"
        trackers = ['udp://tracker.opentrackr.org:1337/announce', 'udp://open.stealth.si:80/announce']
        for tr in trackers: magnet += f"&tr={urllib.parse.quote(tr)}"
        return magnet

    @staticmethod
    def search_1337x(keyword, page=1):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        url = f"https://www.1377x.to/search/{urllib.parse.quote(keyword)}/{page}/"
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                rows = soup.select('table.table-list tbody tr')
                if not rows:
                    return None
                
                results = []
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) < 6:
                        continue
                    
                    links = cols[0].find_all('a')
                    if len(links) < 2:
                        continue
                    title_link = links[1]
                    title = title_link.text.strip()
                    href = title_link.get('href')
                    
                    seeders = cols[1].text.strip()
                    leechers = cols[2].text.strip()
                    size = cols[4].text.strip()
                    
                    if href.startswith('/'):
                        href = "https://www.1377x.to" + href
                        
                    results.append({
                        "name": title,
                        "link": href,
                        "size": size,
                        "seeders": seeders,
                        "leechers": leechers
                    })
                return results
        except Exception:
            pass
        return None

    @staticmethod
    def get_magnet_1337x(details_url):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        try:
            response = requests.get(details_url, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                magnet_el = soup.find('a', href=lambda href: href and href.startswith('magnet:'))
                if magnet_el:
                    return magnet_el.get('href')
        except Exception:
            pass
        return None