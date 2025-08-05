import streamlit as st
import pandas as pd
import plotly.graph_objs as go

# Load the CSV data once at app start
@st.cache_data
def load_data():
    data = pd.read_csv('data/players_stats.csv')
    return data

data = load_data()

# Sidebar dropdown for player selection
player_list = sorted(data['Player'].dropna().unique())
selected_player = st.sidebar.selectbox('Select a player', player_list)

# Filter data for the selected player
player_data = data[(data['Player'] == selected_player) & (pd.to_numeric(data['PTS'], errors='coerce').notnull())]

if player_data.empty:
    st.write("No data available for this player.")
else:
    # Sort by Season
    player_data = player_data.sort_values(by='Season')

    seasons = player_data['Season'].tolist()
    pts = player_data['PTS'].astype(float).tolist()

    # Create Plotly line chart
    trace = go.Scatter(
        x=seasons,
        y=pts,
        mode='lines+markers',
        name='Points Per Game'
    )

    layout = go.Layout(
        title=f'Points Per Game for {selected_player}',
        xaxis=dict(title='Season', type='category'),  # Ensure categorical axis for seasons
        yaxis=dict(title='Points Per Game', rangemode='tozero'),
        margin=dict(t=40, b=50)
    )

    fig = go.Figure(data=[trace], layout=layout)

    # Display the plotly chart
    st.plotly_chart(fig, use_container_width=True)
