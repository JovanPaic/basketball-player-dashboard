document.addEventListener('DOMContentLoaded', () => {
  const playerSelect = document.getElementById('playerSelect');
  const chartDiv = document.getElementById('chart');

  fetch('/api/players')
    .then(response => response.json())
    .then(players => {
      playerSelect.innerHTML = '<option value="" disabled selected>Select a player</option>';
      players.forEach(player => {
        const option = document.createElement('option');
        option.value = player;
        option.textContent = player;
        playerSelect.appendChild(option);
      });
    })
    .catch(() => {
      playerSelect.innerHTML = '<option value="" disabled>Error loading players</option>';
    });

  playerSelect.addEventListener('change', () => {
    const player = playerSelect.value;
    if (!player) return;

    fetch(`/api/player_stats?name=${encodeURIComponent(player)}`)
      .then(response => response.json())
      .then(data => {
        if (!data.length) {
          chartDiv.innerHTML = 'No data available for this player.';
          return;
        }

        const seasons = data.map(row => row.Season);
        const pts = data.map(row => parseFloat(row.PTS));

        const trace = {
          x: seasons,
          y: pts,
          type: 'scatter',
          mode: 'lines+markers',
          name: 'PTS per Season',
          line: { shape: 'linear' },
        };

        const layout = {
          title: `Points Per Game for ${player}`,
          xaxis: { title: 'Season' },
          yaxis: { title: 'Points Per Game', rangemode: 'tozero' },
          margin: { t: 40, b: 50 },
        };

        Plotly.newPlot(chartDiv, [trace], layout, { responsive: true });
      })
      .catch(() => {
        chartDiv.innerHTML = 'Error loading player stats.';
      });
  });
});
