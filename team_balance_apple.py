import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from pulp import LpProblem, LpVariable, LpMinimize, lpSum, LpBinary, value, PULP_CBC_CMD
import random
from typing import Dict, List, Set, Tuple

# Page config - Apple-style minimalism
st.set_page_config(
    page_title="Team Balance",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Apple-inspired CSS - Clean, minimal, sophisticated
st.markdown("""
<style>
    /* Import SF Pro Display-like font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global Styles - Apple minimalism */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }
    
    .main {
        background: linear-gradient(180deg, #ffffff 0%, #f5f5f7 100%);
        padding: 0;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Hero Section */
    .hero {
        text-align: center;
        padding: 80px 20px 60px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 0 0 40px 40px;
        margin: -50px -50px 40px;
        box-shadow: 0 20px 60px rgba(102, 126, 234, 0.3);
    }
    
    .hero h1 {
        font-size: 56px;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.5px;
    }
    
    .hero p {
        font-size: 21px;
        font-weight: 400;
        opacity: 0.95;
        margin: 16px 0 0;
        letter-spacing: 0.3px;
    }
    
    /* Navigation Pills */
    .nav-pills {
        display: flex;
        justify-content: center;
        gap: 8px;
        padding: 20px;
        background: white;
        border-radius: 20px;
        box-shadow: 0 2px 20px rgba(0,0,0,0.06);
        margin: 40px auto;
        max-width: 800px;
        flex-wrap: wrap;
    }
    
    .nav-pill {
        padding: 12px 24px;
        border-radius: 12px;
        background: #f5f5f7;
        color: #1d1d1f;
        text-decoration: none;
        font-weight: 500;
        font-size: 14px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        border: 2px solid transparent;
        cursor: pointer;
    }
    
    .nav-pill:hover {
        background: #e8e8ed;
        transform: translateY(-2px);
    }
    
    .nav-pill.active {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
    
    /* Card Design - Apple style */
    .apple-card {
        background: white;
        border-radius: 24px;
        padding: 32px;
        margin: 20px 0;
        box-shadow: 0 4px 24px rgba(0,0,0,0.06);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        border: 1px solid rgba(0,0,0,0.04);
    }
    
    .apple-card:hover {
        box-shadow: 0 8px 40px rgba(0,0,0,0.12);
        transform: translateY(-4px);
    }
    
    .apple-card h2 {
        font-size: 32px;
        font-weight: 700;
        margin: 0 0 8px 0;
        color: #1d1d1f;
        letter-spacing: -0.5px;
    }
    
    .apple-card h3 {
        font-size: 24px;
        font-weight: 600;
        margin: 24px 0 16px 0;
        color: #1d1d1f;
    }
    
    .apple-card p {
        font-size: 17px;
        color: #86868b;
        line-height: 1.6;
        margin: 0;
    }
    
    /* Team Card - Premium design */
    .team-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 24px;
        padding: 32px;
        margin: 24px 0;
        color: white;
        box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .team-card:hover {
        transform: translateY(-6px);
        box-shadow: 0 20px 60px rgba(102, 126, 234, 0.4);
    }
    
    .team-card h2 {
        font-size: 36px;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.5px;
    }
    
    .team-card-subtitle {
        font-size: 17px;
        opacity: 0.9;
        margin: 8px 0 24px;
        font-weight: 400;
    }
    
    /* Color variants */
    .team-card-blue {
        background: linear-gradient(135deg, #0071e3 0%, #005bb5 100%);
        box-shadow: 0 10px 40px rgba(0, 113, 227, 0.3);
    }
    
    .team-card-purple {
        background: linear-gradient(135deg, #a855f7 0%, #7c3aed 100%);
        box-shadow: 0 10px 40px rgba(168, 85, 247, 0.3);
    }
    
    .team-card-pink {
        background: linear-gradient(135deg, #ec4899 0%, #be185d 100%);
        box-shadow: 0 10px 40px rgba(236, 72, 153, 0.3);
    }
    
    .team-card-green {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        box-shadow: 0 10px 40px rgba(16, 185, 129, 0.3);
    }
    
    .team-card-orange {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        box-shadow: 0 10px 40px rgba(245, 158, 11, 0.3);
    }
    
    .team-card-red {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        box-shadow: 0 10px 40px rgba(239, 68, 68, 0.3);
    }
    
    /* Player Card - Clean and minimal */
    .player-card {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        padding: 20px;
        margin: 12px 0;
        color: #1d1d1f;
        border: 1px solid rgba(255, 255, 255, 0.3);
        transition: all 0.3s ease;
    }
    
    .player-card:hover {
        background: rgba(255, 255, 255, 1);
        transform: translateX(4px);
    }
    
    .player-name {
        font-size: 17px;
        font-weight: 600;
        color: #1d1d1f;
        margin-bottom: 8px;
    }
    
    .player-stats {
        font-size: 14px;
        color: #86868b;
        font-weight: 400;
    }
    
    /* Metrics - Apple Numbers style */
    .metric-container {
        background: white;
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        border: 1px solid rgba(0,0,0,0.04);
        transition: all 0.3s ease;
    }
    
    .metric-container:hover {
        background: #f5f5f7;
        transform: translateY(-2px);
    }
    
    .metric-value {
        font-size: 32px;
        font-weight: 700;
        color: #1d1d1f;
        letter-spacing: -0.5px;
    }
    
    .metric-label {
        font-size: 13px;
        color: #86868b;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 4px;
    }
    
    /* Position Badge - Refined */
    .position-badge {
        display: inline-block;
        padding: 6px 12px;
        border-radius: 8px;
        font-size: 12px;
        font-weight: 600;
        margin-right: 8px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .pos-forward { background: rgba(239, 68, 68, 0.15); color: #dc2626; }
    .pos-midfielder { background: rgba(16, 185, 129, 0.15); color: #059669; }
    .pos-defender { background: rgba(59, 130, 246, 0.15); color: #2563eb; }
    .pos-goalkeeper { background: rgba(245, 158, 11, 0.15); color: #d97706; }
    
    /* Balance Bar - Elegant */
    .balance-comparison {
        margin: 32px 0;
    }
    
    .balance-bar-container {
        margin: 16px 0;
    }
    
    .balance-bar-label {
        font-size: 15px;
        font-weight: 600;
        color: #1d1d1f;
        margin-bottom: 8px;
    }
    
    .balance-bar {
        background: #f5f5f7;
        border-radius: 8px;
        height: 12px;
        overflow: hidden;
        position: relative;
    }
    
    .balance-fill {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        height: 100%;
        transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
        border-radius: 8px;
    }
    
    .balance-value {
        font-size: 13px;
        color: #86868b;
        margin-top: 4px;
    }
    
    /* Buttons - Apple style */
    .stButton>button {
        background: #0071e3;
        color: white;
        border: none;
        border-radius: 12px;
        padding: 12px 24px;
        font-size: 15px;
        font-weight: 500;
        transition: all 0.3s ease;
        box-shadow: 0 2px 8px rgba(0, 113, 227, 0.3);
    }
    
    .stButton>button:hover {
        background: #0077ed;
        box-shadow: 0 4px 16px rgba(0, 113, 227, 0.4);
        transform: translateY(-2px);
    }
    
    .stButton>button:active {
        transform: translateY(0);
    }
    
    /* Feature Cards */
    .feature-card {
        background: white;
        border-radius: 20px;
        padding: 40px;
        text-align: center;
        box-shadow: 0 4px 24px rgba(0,0,0,0.06);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        border: 1px solid rgba(0,0,0,0.04);
        height: 100%;
    }
    
    .feature-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 12px 48px rgba(0,0,0,0.12);
    }
    
    .feature-icon {
        font-size: 56px;
        margin-bottom: 24px;
    }
    
    .feature-title {
        font-size: 24px;
        font-weight: 600;
        color: #1d1d1f;
        margin-bottom: 12px;
    }
    
    .feature-desc {
        font-size: 15px;
        color: #86868b;
        line-height: 1.6;
    }
    
    /* Form Elements */
    .stTextInput>div>div>input,
    .stNumberInput>div>div>input,
    .stSelectbox>div>div>select {
        border-radius: 12px;
        border: 1px solid #d2d2d7;
        padding: 12px 16px;
        font-size: 15px;
        transition: all 0.3s ease;
    }
    
    .stTextInput>div>div>input:focus,
    .stNumberInput>div>div>input:focus,
    .stSelectbox>div>div>select:focus {
        border-color: #0071e3;
        box-shadow: 0 0 0 4px rgba(0, 113, 227, 0.1);
    }
    
    /* Slider */
    .stSlider>div>div>div {
        background: #0071e3;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: white;
        border-radius: 16px;
        padding: 8px;
        box-shadow: 0 2px 16px rgba(0,0,0,0.06);
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 12px;
        padding: 12px 24px;
        font-weight: 500;
        background: transparent;
        border: none;
    }
    
    .stTabs [aria-selected="true"] {
        background: #0071e3;
        color: white;
    }
    
    /* Dataframe */
    .dataframe {
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid rgba(0,0,0,0.06);
    }
    
    /* Section Divider */
    .section-divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, #d2d2d7, transparent);
        margin: 48px 0;
    }
    
    /* Smooth animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .animate-in {
        animation: fadeIn 0.6s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    /* Responsive */
    @media (max-width: 768px) {
        .hero h1 { font-size: 36px; }
        .hero p { font-size: 17px; }
        .nav-pills { flex-direction: column; }
        .apple-card { padding: 24px; }
    }
</style>
""", unsafe_allow_html=True)

# Data files
PLAYERS_FILE = "players_inventory.json"
GAMES_FILE = "games_history.json"
PARTNERSHIPS_FILE = "player_partnerships.json"
CONFLICTS_FILE = "player_conflicts.json"

# Position options
POSITIONS = ["Forward", "Midfielder", "Defender", "Goalkeeper"]

# Team color schemes
TEAM_COLORS = ["blue", "purple", "pink", "green", "orange", "red"]

def load_json(filename, default):
    """Load JSON file or return default if not exists"""
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    return default

def save_json(filename, data):
    """Save data to JSON file"""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

def load_players():
    """Load players from inventory"""
    return load_json(PLAYERS_FILE, [])

def save_players(players):
    """Save players to inventory"""
    save_json(PLAYERS_FILE, players)

def load_games():
    """Load game history"""
    return load_json(GAMES_FILE, [])

def save_game(game_data):
    """Save a game to history"""
    games = load_games()
    games.append(game_data)
    save_json(GAMES_FILE, games)

def load_partnerships():
    """Load player partnerships"""
    return load_json(PARTNERSHIPS_FILE, {})

def save_partnerships(partnerships):
    """Save player partnerships"""
    save_json(PARTNERSHIPS_FILE, partnerships)

def load_conflicts():
    """Load player conflicts"""
    return load_json(CONFLICTS_FILE, {})

def save_conflicts(conflicts):
    """Save player conflicts"""
    save_json(CONFLICTS_FILE, conflicts)

def calculate_player_score(player):
    """Calculate overall score for a player"""
    return (
        player.get('running_ability', 5) +
        player.get('goal_scoring', 5) +
        player.get('age', 25) / 5 +
        player.get('height', 170) / 34 +
        player.get('overall_skill', 5)
    )

def count_positions(team_players):
    """Count positions in a team"""
    positions = {"Forward": 0, "Midfielder": 0, "Defender": 0, "Goalkeeper": 0}
    for player in team_players:
        pos = player.get('position', 'Midfielder')
        positions[pos] += 1
    return positions

def calculate_team_metrics(team_players):
    """Calculate comprehensive team metrics"""
    if not team_players:
        return {
            'avg_running': 0,
            'avg_goals': 0,
            'avg_age': 0,
            'avg_height': 0,
            'avg_skill': 0,
            'total_score': 0,
            'position_dist': {"Forward": 0, "Midfielder": 0, "Defender": 0, "Goalkeeper": 0}
        }
    
    positions = count_positions(team_players)
    
    return {
        'avg_running': sum(p.get('running_ability', 5) for p in team_players) / len(team_players),
        'avg_goals': sum(p.get('goal_scoring', 5) for p in team_players) / len(team_players),
        'avg_age': sum(p.get('age', 25) for p in team_players) / len(team_players),
        'avg_height': sum(p.get('height', 170) for p in team_players) / len(team_players),
        'avg_skill': sum(p.get('overall_skill', 5) for p in team_players) / len(team_players),
        'total_score': sum(calculate_player_score(p) for p in team_players),
        'position_dist': positions
    }

def balance_teams_advanced(players, num_teams, partnerships, conflicts, locked_assignments):
    """Advanced team balancing with partnerships, conflicts, and position awareness"""
    try:
        prob = LpProblem("Team_Balancing", LpMinimize)
        
        assignments = {}
        for i, player in enumerate(players):
            for t in range(num_teams):
                assignments[(i, t)] = LpVariable(f"player_{i}_team_{t}", cat=LpBinary)
        
        for i in range(len(players)):
            prob += lpSum([assignments[(i, t)] for t in range(num_teams)]) == 1
        
        for player_name, team_idx in locked_assignments.items():
            player_idx = next((i for i, p in enumerate(players) if p['name'] == player_name), None)
            if player_idx is not None:
                prob += assignments[(player_idx, team_idx)] == 1
        
        team_size = len(players) // num_teams
        for t in range(num_teams):
            prob += lpSum([assignments[(i, t)] for i in range(len(players))]) >= team_size
            prob += lpSum([assignments[(i, t)] for i in range(len(players))]) <= team_size + 1
        
        team_scores = {}
        for t in range(num_teams):
            team_score = lpSum([
                assignments[(i, t)] * calculate_player_score(players[i])
                for i in range(len(players))
            ])
            team_scores[t] = team_score
        
        position_scores = {pos: {} for pos in POSITIONS}
        for pos in POSITIONS:
            for t in range(num_teams):
                position_count = lpSum([
                    assignments[(i, t)]
                    for i in range(len(players))
                    if players[i].get('position') == pos
                ])
                position_scores[pos][t] = position_count
        
        max_score = LpVariable("max_score")
        min_score = LpVariable("min_score")
        
        for t in range(num_teams):
            prob += team_scores[t] <= max_score
            prob += team_scores[t] >= min_score
        
        prob += max_score - min_score
        
        partnership_bonus = 0
        for player1, partners in partnerships.items():
            p1_idx = next((i for i, p in enumerate(players) if p['name'] == player1), None)
            if p1_idx is not None:
                for player2 in partners:
                    p2_idx = next((i for i, p in enumerate(players) if p['name'] == player2), None)
                    if p2_idx is not None and p1_idx < p2_idx:
                        for t in range(num_teams):
                            partnership_bonus += 10 * (2 - assignments[(p1_idx, t)] - assignments[(p2_idx, t)])
        
        prob += partnership_bonus
        
        conflict_penalty = 0
        for player1, conflicts_list in conflicts.items():
            p1_idx = next((i for i, p in enumerate(players) if p['name'] == player1), None)
            if p1_idx is not None:
                for player2 in conflicts_list:
                    p2_idx = next((i for i, p in enumerate(players) if p['name'] == player2), None)
                    if p2_idx is not None and p1_idx < p2_idx:
                        for t in range(num_teams):
                            conflict_penalty += 20 * (assignments[(p1_idx, t)] + assignments[(p2_idx, t)] - 1)
        
        prob += conflict_penalty
        
        prob.solve(PULP_CBC_CMD(msg=0))
        
        teams = [[] for _ in range(num_teams)]
        for i, player in enumerate(players):
            for t in range(num_teams):
                if value(assignments[(i, t)]) == 1:
                    teams[t].append(player)
                    break
        
        return teams
    
    except Exception as e:
        return balance_teams_greedy(players, num_teams, locked_assignments)

def balance_teams_greedy(players, num_teams, locked_assignments):
    """Greedy fallback algorithm"""
    sorted_players = sorted(players, key=calculate_player_score, reverse=True)
    teams = [[] for _ in range(num_teams)]
    
    assigned_players = set()
    for player_name, team_idx in locked_assignments.items():
        player = next((p for p in sorted_players if p['name'] == player_name), None)
        if player:
            teams[team_idx].append(player)
            assigned_players.add(player_name)
    
    sorted_players = [p for p in sorted_players if p['name'] not in assigned_players]
    
    for player in sorted_players:
        team_scores = [sum(calculate_player_score(p) for p in team) for team in teams]
        min_team = team_scores.index(min(team_scores))
        teams[min_team].append(player)
    
    return teams

# Initialize session state
if 'page' not in st.session_state:
    st.session_state.page = 'home'
if 'generated_teams' not in st.session_state:
    st.session_state.generated_teams = None
if 'locked_players' not in st.session_state:
    st.session_state.locked_players = {}
if 'swap_player' not in st.session_state:
    st.session_state.swap_player = None
if 'swap_from_team' not in st.session_state:
    st.session_state.swap_from_team = None

# Navigation function
def navigate_to(page):
    st.session_state.page = page
    st.rerun()

# Hero Section
if st.session_state.page == 'home':
    st.markdown("""
    <div class="hero animate-in">
        <h1>Team Balance</h1>
        <p>Create perfectly balanced teams with intelligent optimization</p>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)

# Navigation Pills
nav_options = {
    'home': ('🏠', 'Home'),
    'players': ('👥', 'Players'),
    'game': ('⚽', 'Create Game'),
    'partnerships': ('🤝', 'Relationships'),
    'history': ('📊', 'History')
}

nav_html = '<div class="nav-pills">'
for page_key, (emoji, label) in nav_options.items():
    active_class = 'active' if st.session_state.page == page_key else ''
    nav_html += f'<div class="nav-pill {active_class}" onclick="window.location.href=\'?page={page_key}\'">{emoji} {label}</div>'
nav_html += '</div>'

st.markdown(nav_html, unsafe_allow_html=True)

# Handle navigation from URL params
query_params = st.query_params
if 'page' in query_params:
    new_page = query_params['page']
    if new_page != st.session_state.page and new_page in nav_options:
        st.session_state.page = new_page
        st.rerun()

# HOME PAGE
if st.session_state.page == 'home':
    # Feature Cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card animate-in">
            <div class="feature-icon">⚡</div>
            <div class="feature-title">Smart Balancing</div>
            <div class="feature-desc">AI-powered optimization ensures fair teams every time</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card animate-in">
            <div class="feature-icon">🎯</div>
            <div class="feature-title">Position Aware</div>
            <div class="feature-desc">Balanced distribution of roles across all teams</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card animate-in">
            <div class="feature-icon">🤝</div>
            <div class="feature-title">Partnerships</div>
            <div class="feature-desc">Keep your best combinations together</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    
    # Quick Stats
    players = load_players()
    games = load_games()
    
    st.markdown('<div class="apple-card animate-in">', unsafe_allow_html=True)
    st.markdown('<h2>Quick Stats</h2>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-value">{len(players)}</div>
            <div class="metric-label">Players</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-value">{len(games)}</div>
            <div class="metric-label">Games</div>
        </div>
        """, unsafe_allow_html=True)
    
    if players:
        avg_skill = sum(p.get('overall_skill', 5) for p in players) / len(players)
        with col3:
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-value">{avg_skill:.1f}</div>
                <div class="metric-label">Avg Skill</div>
            </div>
            """, unsafe_allow_html=True)
        
        positions_count = {}
        for p in players:
            pos = p.get('position', 'Midfielder')
            positions_count[pos] = positions_count.get(pos, 0) + 1
        most_common_pos = max(positions_count, key=positions_count.get) if positions_count else "N/A"
        
        with col4:
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-value">{most_common_pos[:3]}</div>
                <div class="metric-label">Top Position</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Call to Action
    st.markdown('<div style="height: 40px;"></div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Create Your First Game", use_container_width=True, type="primary"):
            navigate_to('game')

# PLAYERS PAGE
elif st.session_state.page == 'players':
    st.markdown('<div class="apple-card animate-in">', unsafe_allow_html=True)
    st.markdown('<h2>Player Management</h2>', unsafe_allow_html=True)
    st.markdown('<p>Add and manage your player roster</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    players = load_players()
    
    tab1, tab2, tab3 = st.tabs(["➕ Add Player", "📝 Edit Players", "📥 Import/Export"])
    
    with tab1:
        st.markdown('<div class="apple-card">', unsafe_allow_html=True)
        with st.form("add_player_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Player Name*", placeholder="John Smith")
                position = st.selectbox("Position*", POSITIONS)
                running_ability = st.slider("Running Ability", 1, 10, 5)
                goal_scoring = st.slider("Goal Scoring", 1, 10, 5)
            
            with col2:
                age = st.number_input("Age", 10, 60, 25)
                height = st.number_input("Height (cm)", 140, 220, 175)
                overall_skill = st.slider("Overall Skill", 1, 10, 5)
            
            submitted = st.form_submit_button("Add Player", use_container_width=True, type="primary")
            
            if submitted:
                if not name:
                    st.error("Player name is required!")
                elif any(p['name'] == name for p in players):
                    st.error(f"Player '{name}' already exists!")
                else:
                    new_player = {
                        'name': name,
                        'position': position,
                        'running_ability': running_ability,
                        'goal_scoring': goal_scoring,
                        'age': age,
                        'height': height,
                        'overall_skill': overall_skill,
                        'created_at': datetime.now().isoformat()
                    }
                    players.append(new_player)
                    save_players(players)
                    st.success(f"✅ Added {name} to roster!")
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab2:
        if not players:
            st.info("No players yet. Add your first player!")
        else:
            for idx, player in enumerate(players):
                with st.expander(f"{player['name']} - {player.get('position', 'N/A')}", expanded=False):
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        player['name'] = st.text_input("Name", player['name'], key=f"name_{idx}")
                        player['position'] = st.selectbox("Position", POSITIONS, 
                                                         index=POSITIONS.index(player.get('position', 'Midfielder')),
                                                         key=f"pos_{idx}")
                    
                    with col2:
                        player['age'] = st.number_input("Age", 10, 60, player.get('age', 25), key=f"age_{idx}")
                        player['height'] = st.number_input("Height", 140, 220, player.get('height', 175), key=f"height_{idx}")
                    
                    with col3:
                        if st.button("Delete", key=f"del_{idx}", type="secondary"):
                            players.pop(idx)
                            save_players(players)
                            st.success("Deleted!")
                            st.rerun()
                    
                    col1, col2, col3 = st.columns(3)
                    player['running_ability'] = col1.slider("Running", 1, 10, player.get('running_ability', 5), key=f"run_{idx}")
                    player['goal_scoring'] = col2.slider("Goals", 1, 10, player.get('goal_scoring', 5), key=f"goal_{idx}")
                    player['overall_skill'] = col3.slider("Skill", 1, 10, player.get('overall_skill', 5), key=f"skill_{idx}")
            
            if st.button("💾 Save All Changes", type="primary", use_container_width=True):
                save_players(players)
                st.success("✅ Saved!")
                st.rerun()
    
    with tab3:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Export Players**")
            if players:
                df = pd.DataFrame(players)
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name=f"players_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            else:
                st.info("No players to export")
        
        with col2:
            st.markdown("**Import Players**")
            uploaded_file = st.file_uploader("Choose CSV file", type=['csv'])
            
            if uploaded_file:
                if st.button("Import Players", use_container_width=True):
                    try:
                        df = pd.read_csv(uploaded_file)
                        new_players = df.to_dict('records')
                        save_players(new_players)
                        st.success(f"✅ Imported {len(new_players)} players!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

# PARTNERSHIPS PAGE
elif st.session_state.page == 'partnerships':
    st.markdown('<div class="apple-card animate-in">', unsafe_allow_html=True)
    st.markdown('<h2>Player Relationships</h2>', unsafe_allow_html=True)
    st.markdown('<p>Define partnerships and conflicts for better balancing</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    players = load_players()
    partnerships = load_partnerships()
    conflicts = load_conflicts()
    
    if not players:
        st.warning("⚠️ Add players first!")
    else:
        tab1, tab2 = st.tabs(["🤝 Partnerships", "⚠️ Conflicts"])
        
        with tab1:
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown('<div class="apple-card">', unsafe_allow_html=True)
                st.markdown("**Add Partnership**")
                player1 = st.selectbox("Player 1", [p['name'] for p in players], key="partner1")
                remaining = [p['name'] for p in players if p['name'] != player1]
                
                if remaining:
                    player2 = st.selectbox("Player 2", remaining, key="partner2")
                    
                    if st.button("Add Partnership", use_container_width=True, type="primary"):
                        if player1 not in partnerships:
                            partnerships[player1] = []
                        if player2 not in partnerships:
                            partnerships[player2] = []
                        
                        if player2 not in partnerships[player1]:
                            partnerships[player1].append(player2)
                        if player1 not in partnerships[player2]:
                            partnerships[player2].append(player1)
                        
                        save_partnerships(partnerships)
                        st.success(f"✅ Partnership created")
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown('<div class="apple-card">', unsafe_allow_html=True)
                st.markdown("**Existing Partnerships**")
                if partnerships:
                    displayed_pairs = set()
                    for player, partners in partnerships.items():
                        for partner in partners:
                            pair = tuple(sorted([player, partner]))
                            if pair not in displayed_pairs:
                                displayed_pairs.add(pair)
                                col_a, col_b = st.columns([3, 1])
                                col_a.write(f"**{pair[0]}** ↔️ **{pair[1]}**")
                                if col_b.button("Remove", key=f"rp_{pair[0]}_{pair[1]}", type="secondary"):
                                    if pair[1] in partnerships.get(pair[0], []):
                                        partnerships[pair[0]].remove(pair[1])
                                    if pair[0] in partnerships.get(pair[1], []):
                                        partnerships[pair[1]].remove(pair[0])
                                    partnerships = {k: v for k, v in partnerships.items() if v}
                                    save_partnerships(partnerships)
                                    st.rerun()
                else:
                    st.info("No partnerships yet")
                st.markdown('</div>', unsafe_allow_html=True)
        
        with tab2:
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown('<div class="apple-card">', unsafe_allow_html=True)
                st.markdown("**Add Conflict**")
                player1 = st.selectbox("Player 1", [p['name'] for p in players], key="conflict1")
                remaining = [p['name'] for p in players if p['name'] != player1]
                
                if remaining:
                    player2 = st.selectbox("Player 2", remaining, key="conflict2")
                    
                    if st.button("Add Conflict", use_container_width=True, type="primary"):
                        if player1 not in conflicts:
                            conflicts[player1] = []
                        if player2 not in conflicts:
                            conflicts[player2] = []
                        
                        if player2 not in conflicts[player1]:
                            conflicts[player1].append(player2)
                        if player1 not in conflicts[player2]:
                            conflicts[player2].append(player1)
                        
                        save_conflicts(conflicts)
                        st.success(f"✅ Conflict added")
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown('<div class="apple-card">', unsafe_allow_html=True)
                st.markdown("**Existing Conflicts**")
                if conflicts:
                    displayed_pairs = set()
                    for player, conflict_list in conflicts.items():
                        for conflict in conflict_list:
                            pair = tuple(sorted([player, conflict]))
                            if pair not in displayed_pairs:
                                displayed_pairs.add(pair)
                                col_a, col_b = st.columns([3, 1])
                                col_a.write(f"**{pair[0]}** ⚠️ **{pair[1]}**")
                                if col_b.button("Remove", key=f"rc_{pair[0]}_{pair[1]}", type="secondary"):
                                    if pair[1] in conflicts.get(pair[0], []):
                                        conflicts[pair[0]].remove(pair[1])
                                    if pair[0] in conflicts.get(pair[1], []):
                                        conflicts[pair[1]].remove(pair[0])
                                    conflicts = {k: v for k, v in conflicts.items() if v}
                                    save_conflicts(conflicts)
                                    st.rerun()
                else:
                    st.info("No conflicts yet")
                st.markdown('</div>', unsafe_allow_html=True)

# CREATE GAME PAGE
elif st.session_state.page == 'game':
    st.markdown('<div class="apple-card animate-in">', unsafe_allow_html=True)
    st.markdown('<h2>Create Balanced Teams</h2>', unsafe_allow_html=True)
    st.markdown('<p>Select players and generate perfectly balanced teams</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    players = load_players()
    
    if not players:
        st.warning("⚠️ Add players first!")
    else:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown('<div class="apple-card">', unsafe_allow_html=True)
            game_name = st.text_input("Game Name", f"Game {len(load_games()) + 1}", placeholder="Friday Night Game")
            
            st.markdown("**Select Players**")
            col_a, col_b = st.columns(2)
            if col_a.button("Select All", use_container_width=True):
                st.session_state.selected_all = True
                st.rerun()
            if col_b.button("Clear All", use_container_width=True):
                st.session_state.selected_all = False
                st.rerun()
            
            selected_players = []
            for player in players:
                default_val = st.session_state.get('selected_all', True)
                if st.checkbox(
                    f"{player['name']} ({player.get('position', 'N/A')}) - Skill: {player.get('overall_skill', 5)}/10",
                    value=default_val,
                    key=f"select_{player['name']}"
                ):
                    selected_players.append(player)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="apple-card">', unsafe_allow_html=True)
            st.markdown(f"**{len(selected_players)} players selected**")
            
            if len(selected_players) >= 2:
                num_teams = st.number_input("Number of Teams", 2, min(len(selected_players), 10), 2)
                
                with st.expander("Lock Players (Optional)"):
                    for i in range(num_teams):
                        locked_to_this_team = st.multiselect(
                            f"Team {i+1} Locks",
                            [p['name'] for p in selected_players],
                            key=f"lock_team_{i}"
                        )
                        for player_name in locked_to_this_team:
                            st.session_state.locked_players[player_name] = i
            st.markdown('</div>', unsafe_allow_html=True)
        
        if len(selected_players) >= num_teams * 2:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("⚡ Generate Teams", type="primary", use_container_width=True):
                    with st.spinner("Optimizing..."):
                        partnerships = load_partnerships()
                        conflicts = load_conflicts()
                        
                        teams = balance_teams_advanced(
                            selected_players,
                            num_teams,
                            partnerships,
                            conflicts,
                            st.session_state.locked_players
                        )
                        
                        st.session_state.generated_teams = teams
                        st.session_state.game_name = game_name
                        st.session_state.selected_players = selected_players
                        st.success("✅ Teams generated!")
                        st.rerun()
        else:
            st.warning(f"⚠️ Need at least {num_teams * 2} players")
        
        # Display generated teams
        if st.session_state.generated_teams:
            st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
            
            # Action buttons
            col1, col2, col3 = st.columns(3)
            
            if col1.button("🔄 Regenerate", use_container_width=True):
                with st.spinner("Regenerating..."):
                    partnerships = load_partnerships()
                    conflicts = load_conflicts()
                    teams = balance_teams_advanced(
                        st.session_state.selected_players,
                        len(st.session_state.generated_teams),
                        partnerships,
                        conflicts,
                        st.session_state.locked_players
                    )
                    st.session_state.generated_teams = teams
                    st.rerun()
            
            if col2.button("💾 Save Game", use_container_width=True, type="primary"):
                game_data = {
                    'name': st.session_state.game_name,
                    'date': datetime.now().isoformat(),
                    'teams': st.session_state.generated_teams,
                    'num_teams': len(st.session_state.generated_teams),
                    'total_players': sum(len(team) for team in st.session_state.generated_teams)
                }
                save_game(game_data)
                st.success("✅ Game saved!")
            
            if col3.button("🔓 Clear Locks", use_container_width=True):
                st.session_state.locked_players = {}
                st.rerun()
            
            # Balance comparison
            st.markdown('<div class="apple-card balance-comparison">', unsafe_allow_html=True)
            st.markdown('<h3>Team Comparison</h3>', unsafe_allow_html=True)
            
            metrics_list = [calculate_team_metrics(team) for team in st.session_state.generated_teams]
            max_score = max(m['total_score'] for m in metrics_list) if metrics_list else 1
            
            for i, m in enumerate(metrics_list):
                progress = (m['total_score'] / max_score * 100) if max_score > 0 else 0
                st.markdown(f"""
                <div class="balance-bar-container">
                    <div class="balance-bar-label">Team {i+1}</div>
                    <div class="balance-bar">
                        <div class="balance-fill" style="width: {progress}%"></div>
                    </div>
                    <div class="balance-value">{m['total_score']:.1f} points</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Team cards
            for idx, team in enumerate(st.session_state.generated_teams):
                color = TEAM_COLORS[idx % len(TEAM_COLORS)]
                metrics = calculate_team_metrics(team)
                
                st.markdown(f"""
                <div class="team-card team-card-{color} animate-in">
                    <h2>Team {idx + 1}</h2>
                    <div class="team-card-subtitle">{len(team)} players • Score: {metrics['total_score']:.1f}</div>
                """, unsafe_allow_html=True)
                
                # Metrics
                col1, col2, col3, col4, col5 = st.columns(5)
                col1.metric("Running", f"{metrics['avg_running']:.1f}")
                col2.metric("Goals", f"{metrics['avg_goals']:.1f}")
                col3.metric("Skill", f"{metrics['avg_skill']:.1f}")
                col4.metric("Avg Age", f"{metrics['avg_age']:.0f}")
                col5.metric("Height", f"{metrics['avg_height']:.0f}cm")
                
                # Players
                for player in team:
                    pos_class = player.get('position', 'Midfielder').lower()
                    st.markdown(f"""
                    <div class="player-card">
                        <div class="player-name">
                            <span class='position-badge pos-{pos_class}'>{player.get('position', 'MID')[:3]}</span>
                            {player['name']}
                        </div>
                        <div class="player-stats">
                            Run: {player.get('running_ability', 5)}/10 • 
                            Goal: {player.get('goal_scoring', 5)}/10 • 
                            Skill: {player.get('overall_skill', 5)}/10
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)

# HISTORY PAGE
elif st.session_state.page == 'history':
    st.markdown('<div class="apple-card animate-in">', unsafe_allow_html=True)
    st.markdown('<h2>Game History</h2>', unsafe_allow_html=True)
    st.markdown('<p>View past games and team configurations</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    games = load_games()
    
    if not games:
        st.info("No games yet. Create your first game!")
    else:
        for idx, game in enumerate(reversed(games)):
            with st.expander(f"🎮 {game['name']} - {game['date'][:10]}", expanded=(idx == 0)):
                st.markdown('<div class="apple-card">', unsafe_allow_html=True)
                st.write(f"**Date:** {game['date'][:16]}")
                st.write(f"**Teams:** {game['num_teams']}")
                st.write(f"**Players:** {game['total_players']}")
                
                for team_idx, team in enumerate(game['teams']):
                    st.markdown(f"**Team {team_idx + 1}:** {', '.join(p['name'] for p in team)}")
                
                if st.button(f"Delete", key=f"del_game_{idx}", type="secondary"):
                    games.remove(game)
                    save_json(GAMES_FILE, games)
                    st.success("Deleted!")
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
