import requests
from bs4 import BeautifulSoup
import time

BASE_URL = "https://www.basketball-reference.com"
PLAYERS_URL = f"{BASE_URL}/players/"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
                  ' Chrome/115.0 Safari/537.36'
}

def scrape_active_players(retries=3, delay=5):
    for attempt in range(retries):
        response = requests.get(PLAYERS_URL, headers=HEADERS)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            players = []
            for div in soup.find_all('div', id=lambda x: x and x.startswith('players_')):
                for link in div.find_all('a'):
                    name = link.text.strip()
                    url = BASE_URL + link['href']
                    next_sib = link.next_sibling
                    if next_sib and isinstance(next_sib, str) and '*' in next_sib:
                        players.append((name, url))
            return players
        elif response.status_code == 429:
            print(f"Received 429 Too Many Requests, retrying after {delay} seconds...")
            time.sleep(delay)
        else:
            response.raise_for_status()
    raise Exception("Failed to fetch page after retries due to rate limiting")

def save_players_to_file(players, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        for name, url in players:
            f.write(f"{name} | {url}\n")

if __name__ == "__main__":
    players = scrape_active_players()
    save_players_to_file(players, "active_players.txt")
