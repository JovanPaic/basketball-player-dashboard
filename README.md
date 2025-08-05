# Basketball Player Stats Dashboard

This project is an interactive web application built with Python and Streamlit, designed for exploring NBA player performance across multiple seasons. It provides a dynamic and intuitive interface to visualize player statistics and gain insights into career trajectories.

## Overview

The dashboard enables users to browse and compare NBA players through a clean, responsive interface. By selecting a player from the sidebar, users can view detailed season-by-season statistics, such as points per game, displayed through interactive Plotly charts. The application offers a seamless experience for analyzing player progress and performance trends over time.

## Technologies Employed

The application leverages the following core technologies:

- **Python** for data processing and application logic.
- **Streamlit** to create an interactive and user-friendly web interface.
- **Pandas** for efficient data manipulation and preparation.
- **Plotly** to deliver rich, responsive, and interactive visualizations.
- **Requests** and **BeautifulSoup** for web scraping and data extraction from reliable sources.

## Usage Instructions

You can either run the included **start.sh** shell script to set up and launch the app automatically,  
or follow the manual steps below to create a virtual environment, install dependencies, and run the dashboard.

### Manual Setup
1. Create a virtual environment (optional but recommended to keep dependencies isolated):

On Windows (using Command Prompt or PowerShell):
   ```
   python -m venv venv
   venv\Scripts\activate
   ```
On macOS/Linux:
  ```
  python3 -m venv venv
  source venv/bin/activate
  ```
  
2. Install the required dependencies inside the activated virtual environment:
```
pip install -r ./requirements.txt
```

3. Launch the dashboard:
```
streamlit run app.py
```

---

This project is open-source and welcomes contributions, suggestions, and customizations from the community.
