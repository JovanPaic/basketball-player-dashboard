import streamlit as st
import pandas as pd
import plotly.graph_objs as go
import requests
from bs4 import BeautifulSoup
import re
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
for conf in nba_teams:
    for div in nba_teams[conf]:
        all_teams.extend(nba_teams[conf][div])
team_select_options = ["All Players"] + sorted(all_teams)

selected_team = st.sidebar.selectbox(
    "Select Team:",
    team_select_options,
    index=0,
    help="Choose a team to filter available players."
)

if selected_team == "All Players":
    filtered_full_names = all_full_names
else:
    team_name = selected_team
    filtered_full_names = []
    for name in all_full_names:
        url = all_urls[name]
        profile = scrape_player_profile(url)
        if profile.get("current_team", "").lower() == team_name.lower():
            filtered_full_names.append(name)

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
        categories = {
            'Championships': 0,
            'MVP': 0,
            'All-NBA': 0,
            'All-Star': 0,
            'All-Defense': 0,
            'DPOY': 0,
            'ROTY': 0,
            '6MOTY': 0,
        }
        if 'Awards' in player_data.columns:
            accolades = player_data['Accolades'].dropna()
            for accolade in accolades:
                text = str(accolade)
                categories['Championships'] = 0
                categories['MVP'] += len(re.findall(r'\bMVP-1\b', text))
                categories['All-NBA'] += len(re.findall(r'\bNBA1\b', text))
                categories['All-NBA'] += len(re.findall(r'\bNBA2\b', text))
                categories['All-NBA'] += len(re.findall(r'\bNBA3\b', text))
                categories['All-Star'] += len(re.findall(r'\bAS\b', text))
                categories['All-Defense'] += len(re.findall(r'\bDEF1\b', text))
                categories['All-Defense'] += len(re.findall(r'\bDEF2\b', text))
                categories['DPOY'] += len(re.findall(r'\bDPOY-1\b', text))
                categories['ROTY'] += len(re.findall(r'\bROTY-1\b', text))
                categories['6MOTY'] += len(re.findall(r'\b6MOY-1\b', text))
            grid_html = "<div class='acc-grid'>"
            for k, v in categories.items():
                if k == 'Championships':
                    if v > 0:
                        grid_html += f"<div class='champ-item acc-focus champ-glow'><div style='color:#FFD700'>{v}</div><div class='champ-label' style='color:#FFD700'>{k}</div></div>"
                    else:
                        grid_html += f"<div class='champ-item'><div style='color:#EEEEEE'>{v}</div><div class='champ-label' style='color:#EEEEEE'>{k}</div></div>"
                else:
                    if v > 0:
                        grid_html += f"<div class='acc-item acc-focus acc-glow'><div style='color:#FF4500'>{v}</div><div class='acc-label' style='color:#FF4500'>{k}</div></div>"
                    else:
                        grid_html += f"<div class='acc-item'><div style='color:#EEEEEE'>{v}</div><div class='acc-label' style='color:#EEEEEE'>{k}</div></div>"
            grid_html += "</div>"
            st.markdown(grid_html, unsafe_allow_html=True)
        else:
            st.write("No accolades found.")
st.sidebar.markdown("---")
st.sidebar.markdown("Built with 🏀 Streamlit and Plotly")
