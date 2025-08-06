import streamlit as st
import pandas as pd
import plotly.graph_objs as go
import requests
import re
from bs4 import BeautifulSoup
from bs4 import Comment
from datetime import datetime

@st.cache_data
def load_players_from_file(file_path="data/players.txt"):
    players = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split('|')
            if len(parts) != 2:
                continue
            full_name = parts[0].strip()
            url = parts[1].strip()
            players.append((full_name, url))
    return players

@st.cache_data(show_spinner=True)
def scrape_player_profile(player_url):
    response = requests.get(player_url)
    response.encoding = 'utf-8' 
    soup = BeautifulSoup(response.text, 'lxml')
    profile = {}

    name_tag = soup.select_one('#meta h1')
    if not name_tag:
        name_tag = soup.find('h1')
    profile['full_name'] = name_tag.get_text(strip=True) if name_tag else None

    image_tag = soup.select_one('#meta .media-item img')
    profile['photo_url'] = image_tag['src'] if image_tag and image_tag.has_attr('src') else None

    meta_div = soup.find('div', id='meta')
    if not meta_div:
        return profile

    text_lines = meta_div.get_text(separator='\n').split('\n')

    profile['height'] = ''
    profile['weight'] = ''
    profile['height_weight'] = ''
    if not profile['height_weight']:
        for line in text_lines:
            if 'cm' in line and 'kg' in line:
                profile['height_weight'] = line.strip()
                break
    if not profile['height']:
        for line in text_lines:
            if re.match(r'^\d+-\d+$', line.strip()):
                profile['height'] = line.strip()
                break
    if not profile['weight']:
        for line in text_lines:
            if 'lb' in line:
                profile['weight'] = line.strip()
                break
    for line in text_lines:
        if 'Guard' in line or 'Forward' in line or 'Center' in line:
            profile['position'] = line.strip()
            break

    team_tag = meta_div.find('a', href=lambda x: x and '/teams/' in x)
    profile['current_team'] = team_tag.get_text(strip=True) if team_tag else 'Retired or Free Agent'


    profile['age'] = None
    birth_date = None
    month = day = year = None
    for i, line in enumerate(text_lines):
        l = line.strip()
        md_match = re.match(r'([A-Za-z]+)\s+(\d{1,2})$', l)
        if md_match:
            month, day = md_match.groups()
            for k in range(i+1, min(i+4, len(text_lines))):
                y_match = re.match(r'^(\d{4})$', text_lines[k].strip())
                if y_match:
                    year = y_match.group(1)
                    break
        if month and day and year:
            birth_date = datetime.strptime(f"{month} {day} {year}", "%B %d %Y")

            break
    if birth_date:
        today = datetime.today()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        profile['age'] = age

    categories = {
        'Championships': {'count': 0, 'years': []},
        'Finals MVP': {'count': 0, 'years': []},
        'MVP': {'count': 0, 'years': []},
        'All-NBA': {'count': 0, 'years': []},
        'All-Star': {'count': 0, 'years': []},
        'All-Defensive': {'count': 0, 'years': []},
        'DPOY': {'count': 0, 'years': []},
        'ROY': {'count': 0, 'years': []},
        '6MOTY': {'count': 0, 'years': []},
    }

    leaderboard_id_to_category = {
    'leaderboard_championships': 'Championships',
    'leaderboard_allstar': 'All-Star',
    }

    comments = soup.find_all(string=lambda text: isinstance(text, Comment))

    div_leaderboard = None
    for comment in comments:
        if 'div_leaderboard' in comment:
            commented_soup = BeautifulSoup(comment, 'html.parser')
            div_leaderboard = commented_soup.find('div', id='div_leaderboard')
            break

    if div_leaderboard:
        for div_id, category_key in leaderboard_id_to_category.items():
            category_div = div_leaderboard.find('div', id=div_id)
            if category_div:
                rows = category_div.find_all('tr')
                for row in rows:
                    year_td = row.find('td')
                    if year_td:
                        year_link = year_td.find('a')
                        if year_link:
                            year = year_link.get_text(strip=True).split()[0]
                            categories[category_key]['years'].append(year)
                categories[category_key]['count'] = len(categories[category_key]['years'])

    notable_div = div_leaderboard.find('div', id='leaderboard_notable-awards')
    if notable_div:
        notable_table = notable_div.find('table')
        if notable_table:
            for row in notable_table.find_all('tr'):
                year_td = row.find('td')
                if year_td:
                    year_link = year_td.find('a')
                    if year_link:
                        year = year_link.get_text(strip=True).split()[0]
                        award_lower = year_link.get_text().lower()
                        if 'bill russell' in award_lower:
                            categories['Finals MVP']['count'] += 1
                            categories['Finals MVP']['years'].append(year)
                        elif 'michael jordan' in award_lower:
                            categories['MVP']['count'] += 1
                            categories['MVP']['years'].append(year)
                        elif 'wilt chamberlain' in award_lower:
                            categories['ROY']['count'] += 1
                            categories['ROY']['years'].append(year)
                        elif 'hakeem olajuwon' in award_lower:
                            categories['DPOY']['count'] += 1
                            categories['DPOY']['years'].append(year)
                        elif 'john havlicek' in award_lower:
                            categories['6MOTY']['count'] += 1
                            categories['6MOTY']['years'].append(year)
                            

    all_league_div = div_leaderboard.find('div', id='leaderboard_all_league')
    if all_league_div:
        all_league_table = all_league_div.find('table')
        if all_league_table:
            for row in all_league_table.find_all('tr'):
                year_td = row.find('td')
                if year_td:
                    year_link = year_td.find('a')
                    if year_link:
                        year = year_link.get_text(strip=True).split()[0]
                        award_lower = year_td.get_text().lower()
                        if 'all-nba' in award_lower:
                            categories['All-NBA']['count'] += 1
                            categories['All-NBA']['years'].append(year)
                        elif 'all-defensive ' in award_lower:
                            categories['All-Defensive']['count'] += 1
                            categories['All-Defensive']['years'].append(year)
         
    profile.update(categories)
    return profile

@st.cache_data(show_spinner=True)
def scrape_season_stats(player_url):
    from io import StringIO
    resp = requests.get(player_url)
    try:
        all_tables = pd.read_html(StringIO(resp.text))
    except ValueError:
        return pd.DataFrame()
    for table in all_tables:
        if 'Season' in table.columns and 'PTS' in table.columns:
            df = table.dropna(subset=['Season'])
            df = df[df['Season'] != 'Season']  
            season_pattern = re.compile(r'^\d{4}-\d{2}$')
            df = df[df['Season'].apply(lambda x: bool(season_pattern.match(str(x))))]
            df.reset_index(drop=True, inplace=True)
            # Extract accolades from the last column if it exists
            if len(df.columns) > 0:
                last_col = df.columns[-1]
                df['Accolades'] = df[last_col].fillna("")
            return df
    return pd.DataFrame()

players = load_players_from_file("data/players.txt")
all_full_names = [p[0] for p in players]
all_urls = {p[0]: p[1] for p in players}


st.set_page_config(page_title="NBA Player Stats Dashboard", page_icon="🏀", layout="wide")

with open("assets/styles/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.sidebar.title("Player Selection")

nba_teams = {
    "Eastern Conference": {
        "Atlantic": [
            "Boston Celtics", "Brooklyn Nets", "New York Knicks", "Philadelphia 76ers", "Toronto Raptors"
        ],
        "Central": [
            "Chicago Bulls", "Cleveland Cavaliers", "Detroit Pistons", "Indiana Pacers", "Milwaukee Bucks"
        ],
        "Southeast": [
            "Atlanta Hawks", "Charlotte Hornets", "Miami Heat", "Orlando Magic", "Washington Wizards"
        ]
    },
    "Western Conference": {
        "Northwest": [
            "Denver Nuggets", "Minnesota Timberwolves", "Oklahoma City Thunder", "Portland Trail Blazers", "Utah Jazz"
        ],
        "Pacific": [
            "Golden State Warriors", "Los Angeles Clippers", "Los Angeles Lakers", "Phoenix Suns", "Sacramento Kings"
        ],
        "Southwest": [
            "Dallas Mavericks", "Houston Rockets", "Memphis Grizzlies", "New Orleans Pelicans", "San Antonio Spurs"
        ]
    }
}

all_teams = []
#for conf in nba_teams:
#    for div in nba_teams[conf]:
#        all_teams.extend(nba_teams[conf][div]) 
team_select_options = ["All Players"] #+ sorted(all_teams)

selected_team = st.sidebar.selectbox(
    "Select Team:",
    team_select_options,
    index=0,
    help="Choose a team to filter available players."
)

if selected_team == "All Players":
    filtered_full_names = all_full_names

#else:
#    team_name = selected_team 
#    filtered_full_names = []
#    for name in all_full_names:
#        url = all_urls[name]
#       profile = scrape_player_profile(url) TODO: Fix this so you dont scrape all players for teams each time
#        if profile.get("current_team", "").lower() == team_name.lower():
#           filtered_full_names.append(name)
#

selected_full_name = st.sidebar.selectbox(
    'Select a player',
    filtered_full_names,
    index=0 if filtered_full_names else None
)
player_url = all_urls[selected_full_name] if filtered_full_names else None

profile = None
player_data = pd.DataFrame()
if player_url:
    profile = scrape_player_profile(player_url)
    player_data = scrape_season_stats(player_url)

if not player_data.empty:
    stat_options = [col for col in ["PTS", "AST", "TRB", "G", "MP"] if col in player_data.columns]
else:
    stat_options = ["PTS"]
selected_stat = st.sidebar.selectbox(
    "Stat to chart:",
    stat_options,
    index=stat_options.index("PTS") if "PTS" in stat_options else 0,
    help="Choose which stat to display in the chart."
)

if profile:
    with st.container():
        cols = st.columns([1,6])
        with cols[0]:
            if profile['photo_url']:
                st.image(profile['photo_url'], width=150)
        with cols[1]:
            st.markdown("""
                <div style='min-height:180px;'>
                    <h1 style='margin-bottom:0;'>%s</h1>
                    <div><strong>Age:</strong> %s</div>
                    <div><strong>Height & Weight:</strong> %s</div>
                    <div><strong>Current Team:</strong> %s</div>
                    <div><strong>Position:</strong> %s</div>
                </div>
            """ % (
                profile.get('full_name') or selected_full_name,
                profile.get('age', 'N/A'),
                profile.get('height', 'N/A') + ', ' +  profile.get('weight', 'N/A') + '  ' +  profile.get('height_weight', 'N/A'),
                profile.get('current_team', 'N/A'),
                profile.get('position', 'N/A')
            ), unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["Stats Chart", "Career Accolades"])

    with tab1:
        if player_data.empty:
            st.warning("No season stats available for this player.")
        elif selected_stat not in player_data.columns:
            st.warning(f"No data available for {selected_stat}.")
        else:
            player_data = player_data.sort_values(by='Season')
            valid_rows = player_data[selected_stat].apply(lambda x: pd.notnull(x) and str(x).replace('.', '', 1).isdigit())
            filtered_data = player_data[valid_rows]
            filtered_data = filtered_data.drop_duplicates(subset=['Season'], keep='first')
            seasons = filtered_data['Season'].tolist()
            stat_values = pd.to_numeric(filtered_data[selected_stat], errors='coerce').fillna(0).tolist()
            if not seasons or not any(stat_values):
                st.warning(f"No valid {selected_stat} data to plot.")
            else:
                trace = go.Scatter(
                    x=seasons,
                    y=stat_values,
                    mode='lines+markers',
                    name=selected_stat,
                    line=dict(color='firebrick', width=2),
                    marker=dict(size=8)
                )
                layout = go.Layout(
                    title=f'{selected_stat} per Season for {profile.get("full_name", selected_full_name)}',
                    xaxis=dict(title='Season', type='category'),
                    yaxis=dict(title=selected_stat, rangemode='tozero'),
                    margin=dict(t=50, b=50),
                    hovermode='x unified'
                )
                fig = go.Figure(data=[trace], layout=layout)
                st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("Accolades Summary")

        accolade_keys = ['Championships', 'MVP', 'All-NBA', 'All-Star', 'All-Defensive', 'DPOY', 'ROY', '6MOTY']
        categories_display = {k: profile.get(k, {'count': 0, 'years': []}) for k in accolade_keys}
        finals_mvp = profile.get('Finals MVP', {'count': 0, 'years': []})

        if categories_display:
            grid_html = "<div class='acc-grid'>"
            for k, data in categories_display.items():
                count = data['count']
                years = data['years']
                years_str = ", ".join(years)
                years_html = ""
                if years_str:
                    years_html = f"<div class='year-item'>( {years_str} )</div>"

                if k == 'Championships':
                    if count > 0:
                        grid_html += (f"<div class='champ-item acc-focus champ-glow'>"
                                    f"<div class='champ-label' style='color:#FFD700;'>{k}</div>"
                                    f"<div style='color:#FFD700;'>{count}</div>"
                                    f"{years_html}"
                                    "</div>")
                    else:
                        grid_html += (f"<div class='champ-item'>"
                                    f"<div class='champ-label' style='color:#EEEEEE;'>{k}</div>"
                                    f"<div style='color:#EEEEEE;'>{count}</div>"
                                    f"{years_html}"
                                    "</div>")
                else:
                    if count > 0:
                        grid_html += (f"<div class='acc-item acc-focus acc-glow'>"
                                    f"<div class='acc-label' style='color:#FF4500;'>{k}</div>"
                                    f"<div style='color:#FF4500;;'>{count}</div>"
                                    f"{years_html}"
                                    "</div>")
                    else:
                        grid_html += (f"<div class='acc-item'>"
                                    f"<div class='acc-label' style='color:#EEEEEE;'>{k}</div>"
                                    f"<div style='color:#EEEEEE;'>{count}</div>"
                                    f"{years_html}"
                                    "</div>")
            grid_html += "</div>"

            st.markdown(grid_html, unsafe_allow_html=True)
        else:
            st.write("No accolades found.")

st.sidebar.markdown("---")

st.sidebar.title("Useful links")
st.sidebar.markdown( "Using data from :\n\n [Basketball Reference](https://www.basketball-reference.com/)")
st.sidebar.markdown( "Github repository :\n\n [Basketball Player Dashboard](https://github.com/JovanPaic/basketball-player-dashboard)")


st.sidebar.markdown("---")

st.sidebar.markdown("Built with Streamlit and Plotly")
st.sidebar.markdown("Made by Jovan Paić")



