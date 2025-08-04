from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import pandas as pd

app = Flask(__name__)
CORS(app)

# Load player stats CSV into DataFrame
data = pd.read_csv('data/players_stats.csv')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/players')
def get_players():
    players = data['Player'].dropna().unique()
    players.sort()
    return jsonify(players.tolist())

@app.route('/api/player_stats')
def get_player_stats():
    name = request.args.get('name')
    if not name:
        return jsonify([])

    # Filter data for player, drop rows with missing or invalid PTS
    player_data = data[(data['Player'] == name) & (pd.to_numeric(data['PTS'], errors='coerce').notnull())]

    # Select columns and convert DataFrame to dict list
    result = player_data[['Season', 'PTS']].sort_values(by='Season').to_dict(orient='records')
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
