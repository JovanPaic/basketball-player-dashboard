import requests
from bs4 import BeautifulSoup
import time
import random

BASE_URL = "https://www.basketball-reference.com"
BASE_PLAYERS_URL = f"{BASE_URL}/players/"

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/115.0 Safari/537.36'
    ),
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': BASE_URL,
}

def scrape_active_players(retries=3, delay=5):
    letters = [chr(i) for i in range(ord('a'), ord('z') + 1)]
    all_players = []

    for letter in letters:
        url = f"{BASE_PLAYERS_URL}{letter}/"
        for attempt in range(1, retries + 1):
            try:
                response = requests.get(url, headers=HEADERS)
                response.encoding = 'utf-8'
                status = response.status_code

                if status == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    players_div = soup.find('div', id='players')
                    if not players_div:
                        print(f"No div#players found on {url}")
                        break

                    links = players_div.find_all('a')
                    count_in_letter = 0

                    for link in links:
                        strong = link.find('strong')
                        if strong:
                            href = link.get('href', '')
                            if href.startswith('/players/'):
                                full_name = strong.text.strip()
                                profile_url = BASE_URL + href
                                all_players.append((full_name, profile_url))
                                count_in_letter += 1

                    print(f"Found {count_in_letter} active players in letter '{letter.upper()}'")
                    time.sleep(3 + random.uniform(0.5, 1.5))
                    break  

                elif status == 429:
                    print(f"Rate limited on {url}, attempt {attempt}. Sleeping {delay} seconds...")
                    time.sleep(delay)
                    delay *= 2 

                else:
                    print(f"Failed to fetch {url}, status code {status}")
                    break

            except Exception as e:
                print(f"Error fetching {url}: {e}")
                time.sleep(delay)
        else:
            print(f"Skipping letter '{letter.upper()}' after {retries} retries.")

    print(f"Total active players found: {len(all_players)}")
    return all_players

def save_players_to_file(players, filename="active_players.txt"):
    """
    Save the list of players to a text file with UTF-8 encoding.
    """
    with open(filename, 'w', encoding='utf-8') as f:
        for name, url in players:
            f.write(f"{name} | {url}\n")
    print(f"Saved {len(players)} players to {filename}")

if __name__ == "__main__":
    try:
        players = scrape_active_players()
        if players:
            for player in players:
                print(player)
            save_players_to_file(players, filename="./data/players.txt")
        else:
            print("No active players were found.")

    except Exception as e:
        print("An error occurred:", e)
