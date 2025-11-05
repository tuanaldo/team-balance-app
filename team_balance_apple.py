import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from pulp import LpProblem, LpVariable, LpMinimize, lpSum, LpBinary, value, PULP_CBC_CMD
from typing import Dict, List
import supabase

# Page config
st.set_page_config(
    page_title="Team Balance",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Modern, clean CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }
    
    .main {
        background: #fafafa;
        padding: 0;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Simple Header */
    .app-header {
        background: white;
        padding: 20px 40px;
        border-bottom: 1px solid #e0e0e0;
        margin: -60px -60px 40px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    
    .app-title {
        font-size: 24px;
        font-weight: 600;
        color: #1a1a1a;
    }
    
    /* Navigation Tabs */
    .nav-container {
        display: flex;
        gap: 4px;
        background: white;
        padding: 4px;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    /* Cards */
    .card {
        background: white;
        border-radius: 16px;
        padding: 32px;
        margin: 16px 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        border: 1px solid #f0f0f0;
    }
    
    .card h2 {
        font-size: 24px;
        font-weight: 600;
        color: #1a1a1a;
        margin: 0 0 8px 0;
    }
    
    .card p {
        font-size: 15px;
        color: #666;
        margin: 0;
    }
    
    /* Team Cards */
    .team-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 16px;
        padding: 24px;
        margin: 16px 0;
        color: white;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
    }
    
    .team-card h3 {
        font-size: 20px;
        font-weight: 600;
        margin: 0 0 16px 0;
    }
    
    .team-card-blue { background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); }
    .team-card-green { background: linear-gradient(135deg, #10b981 0%, #059669 100%); }
    .team-card-purple { background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%); }
    .team-card-orange { background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); }
    .team-card-red { background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); }
    .team-card-pink { background: linear-gradient(135deg, #ec4899 0%, #db2777 100%); }
    
    /* Player Cards */
    .player-card {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 12px;
        padding: 16px;
        margin: 8px 0;
        color: #1a1a1a;
    }
    
    .player-name {
        font-size: 15px;
        font-weight: 600;
        margin-bottom: 4px;
    }
    
    .player-stats {
        font-size: 13px;
        color: #666;
    }
    
    /* Position Badge */
    .badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-right: 8px;
    }
    
    .badge-forward { background: #fee; color: #dc2626; }
    .badge-midfielder { background: #efe; color: #059669; }
    .badge-defender { background: #eef; color: #2563eb; }
    .badge-goalkeeper { background: #ffe; color: #d97706; }
    
    /* Buttons */
    .stButton>button {
        background: #667eea;
        color: white;
        border: none;
        border-radius: 10px;
        padding: 10px 20px;
        font-weight: 500;
        transition: all 0.2s;
    }
    
    .stButton>button:hover {
        background: #5568d3;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }
    
    /* Metrics */
    .metric {
        background: white;
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        border: 1px solid #f0f0f0;
    }
    
    .metric-value {
        font-size: 28px;
        font-weight: 700;
        color: #1a1a1a;
    }
    
    .metric-label {
        font-size: 12px;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 4px;
    }
    
    /* Forms */
    .stTextInput>div>div>input,
    .stNumberInput>div>div>input,
    .stSelectbox>div>div>select {
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        padding: 10px 14px;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: white;
        border-radius: 12px;
        padding: 4px;
        border: 1px solid #f0f0f0;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        background: #667eea;
        color: white;
    }
    
    /* Hide default nav */
    [data-testid="stSidebarNav"] {
        display: none;
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
TEAM_COLORS = ["blue", "green", "purple", "orange", "red", "pink"]

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
    response = supabase.table('players').select('*').execute()
    return response.data

def save_player(player):
    supabase.table('players').insert(player).execute()

def load_games():
    return load_json(GAMES_FILE, [])

def save_game(game_data):
    games = load_games()
    games.append(game_data)
    save_json(GAMES_FILE, games)

def load_partnerships():
    return load_json(PARTNERSHIPS_FILE, {})

def save_partnerships(partnerships):
    save_json(PARTNERSHIPS_FILE, partnerships)

def load_conflicts():
    return load_json(CONFLICTS_FILE, {})

def save_conflicts(conflicts):
    save_json(CONFLICTS_FILE, conflicts)

def calculate_player_score(player):
    return (
        player.get('running_ability', 5) +
        player.get('goal_scoring', 5) +
        player.get('age', 25) / 5 +
        player.get('height', 170) / 34 +
        player.get('overall_skill', 5)
    )

def count_positions(team_players):
    positions = {"Forward": 0, "Midfielder": 0, "Defender": 0, "Goalkeeper": 0}
    for player in team_players:
        pos = player.get('position', 'Midfielder')
        positions[pos] += 1
    return positions

def calculate_team_metrics(team_players):
    if not team_players:
        return {
            'avg_running': 0, 'avg_goals': 0, 'avg_age': 0,
            'avg_height': 0, 'avg_skill': 0, 'total_score': 0,
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
    except:
        return balance_teams_greedy(players, num_teams, locked_assignments)

def balance_teams_greedy(players, num_teams, locked_assignments):
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

# Header with navigation
col1, col2 = st.columns([1, 3])

with col1:
    st.markdown('<div class="app-title">⚽ Team Balance</div>', unsafe_allow_html=True)

with col2:
    nav_cols = st.columns(5)
    
    if nav_cols[0].button("Home", use_container_width=True, type="primary" if st.session_state.page == 'home' else "secondary"):
        st.session_state.page = 'home'
        st.rerun()
    
    if nav_cols[1].button("Players", use_container_width=True, type="primary" if st.session_state.page == 'players' else "secondary"):
        st.session_state.page = 'players'
        st.rerun()
    
    if nav_cols[2].button("Create Game", use_container_width=True, type="primary" if st.session_state.page == 'game' else "secondary"):
        st.session_state.page = 'game'
        st.rerun()
    
    if nav_cols[3].button("Relationships", use_container_width=True, type="primary" if st.session_state.page == 'relationships' else "secondary"):
        st.session_state.page = 'relationships'
        st.rerun()
    
    if nav_cols[4].button("History", use_container_width=True, type="primary" if st.session_state.page == 'history' else "secondary"):
        st.session_state.page = 'history'
        st.rerun()

st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)

# HOME PAGE
if st.session_state.page == 'home':
    players = load_players()
    games = load_games()
    
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<h2>Dashboard</h2>', unsafe_allow_html=True)
    st.markdown('<p>Quick overview of your team management</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric">
            <div class="metric-value">{len(players)}</div>
            <div class="metric-label">Players</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric">
            <div class="metric-value">{len(games)}</div>
            <div class="metric-label">Games</div>
        </div>
        """, unsafe_allow_html=True)
    
    if players:
        avg_skill = sum(p.get('overall_skill', 5) for p in players) / len(players)
        with col3:
            st.markdown(f"""
            <div class="metric">
                <div class="metric-value">{avg_skill:.1f}</div>
                <div class="metric-label">Avg Skill</div>
            </div>
            """, unsafe_allow_html=True)
        
        positions_count = {}
        for p in players:
            pos = p.get('position', 'Midfielder')
            positions_count[pos] = positions_count.get(pos, 0) + 1
        most_common = max(positions_count, key=positions_count.get) if positions_count else "None"
        
        with col4:
            st.markdown(f"""
            <div class="metric">
                <div class="metric-value">{most_common[:3]}</div>
                <div class="metric-label">Top Position</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Create New Game", use_container_width=True, type="primary"):
            st.session_state.page = 'game'
            st.rerun()

# PLAYERS PAGE
elif st.session_state.page == 'players':
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<h2>Players</h2>', unsafe_allow_html=True)
    st.markdown('<p>Manage your player roster</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    players = load_players()
    
    tab1, tab2, tab3 = st.tabs(["Add Player", "Edit Players", "Import/Export"])
    
    with tab1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        with st.form("add_player"):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Player Name*")
                position = st.selectbox("Position*", POSITIONS)
                running = st.slider("Running Ability", 1, 10, 5)
                goals = st.slider("Goal Scoring", 1, 10, 5)
            
            with col2:
                age = st.number_input("Age", 10, 60, 25)
                height = st.number_input("Height (cm)", 140, 220, 175)
                skill = st.slider("Overall Skill", 1, 10, 5)
            
            if st.form_submit_button("Add Player", use_container_width=True, type="primary"):
                if not name:
                    st.error("Name required")
                elif any(p['name'] == name for p in players):
                    st.error(f"Player '{name}' exists")
                else:
                    players.append({
                        'name': name, 'position': position,
                        'running_ability': running, 'goal_scoring': goals,
                        'age': age, 'height': height, 'overall_skill': skill,
                        'created_at': datetime.now().isoformat()
                    })
                    save_players(players)
                    st.success(f"✅ Added {name}")
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab2:
        if not players:
            st.info("No players yet")
        else:
            for idx, player in enumerate(players):
                with st.expander(f"{player['name']} - {player.get('position', 'N/A')}"):
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        player['name'] = st.text_input("Name", player['name'], key=f"n{idx}")
                        player['position'] = st.selectbox("Position", POSITIONS, 
                                                         index=POSITIONS.index(player.get('position', 'Midfielder')),
                                                         key=f"p{idx}")
                    with col2:
                        player['age'] = st.number_input("Age", 10, 60, player.get('age', 25), key=f"a{idx}")
                        player['height'] = st.number_input("Height", 140, 220, player.get('height', 175), key=f"h{idx}")
                    
                    with col3:
                        if st.button("Delete", key=f"d{idx}", type="secondary"):
                            players.pop(idx)
                            save_players(players)
                            st.rerun()
                    
                    col1, col2, col3 = st.columns(3)
                    player['running_ability'] = col1.slider("Running", 1, 10, player.get('running_ability', 5), key=f"r{idx}")
                    player['goal_scoring'] = col2.slider("Goals", 1, 10, player.get('goal_scoring', 5), key=f"g{idx}")
                    player['overall_skill'] = col3.slider("Skill", 1, 10, player.get('overall_skill', 5), key=f"s{idx}")
            
            if st.button("💾 Save Changes", type="primary", use_container_width=True):
                save_players(players)
                st.success("✅ Saved")
                st.rerun()
    
    with tab3:
        col1, col2 = st.columns(2)
        
        with col1:
            if players:
                csv = pd.DataFrame(players).to_csv(index=False)
                st.download_button("📥 Download CSV", csv, 
                                 f"players_{datetime.now().strftime('%Y%m%d')}.csv",
                                 mime="text/csv", use_container_width=True)
        
        with col2:
            uploaded = st.file_uploader("Import CSV", type=['csv'])
            if uploaded and st.button("Import", use_container_width=True):
                try:
                    df = pd.read_csv(uploaded)
                    save_players(df.to_dict('records'))
                    st.success(f"✅ Imported {len(df)} players")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

# RELATIONSHIPS PAGE
elif st.session_state.page == 'relationships':
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<h2>Relationships</h2>', unsafe_allow_html=True)
    st.markdown('<p>Define partnerships and conflicts</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    players = load_players()
    partnerships = load_partnerships()
    conflicts = load_conflicts()
    
    if not players:
        st.warning("Add players first")
    else:
        tab1, tab2 = st.tabs(["Partnerships", "Conflicts"])
        
        with tab1:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.subheader("Add Partnership")
                p1 = st.selectbox("Player 1", [p['name'] for p in players], key="p1")
                remaining = [p['name'] for p in players if p['name'] != p1]
                
                if remaining:
                    p2 = st.selectbox("Player 2", remaining, key="p2")
                    if st.button("Add", use_container_width=True, type="primary"):
                        if p1 not in partnerships: partnerships[p1] = []
                        if p2 not in partnerships: partnerships[p2] = []
                        if p2 not in partnerships[p1]: partnerships[p1].append(p2)
                        if p1 not in partnerships[p2]: partnerships[p2].append(p1)
                        save_partnerships(partnerships)
                        st.success("✅ Added")
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.subheader("Existing")
                if partnerships:
                    displayed = set()
                    for player, partners in partnerships.items():
                        for partner in partners:
                            pair = tuple(sorted([player, partner]))
                            if pair not in displayed:
                                displayed.add(pair)
                                c1, c2 = st.columns([3, 1])
                                c1.write(f"{pair[0]} ↔️ {pair[1]}")
                                if c2.button("×", key=f"rp{pair}"):
                                    if pair[1] in partnerships.get(pair[0], []): partnerships[pair[0]].remove(pair[1])
                                    if pair[0] in partnerships.get(pair[1], []): partnerships[pair[1]].remove(pair[0])
                                    partnerships = {k: v for k, v in partnerships.items() if v}
                                    save_partnerships(partnerships)
                                    st.rerun()
                else:
                    st.info("No partnerships")
                st.markdown('</div>', unsafe_allow_html=True)
        
        with tab2:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.subheader("Add Conflict")
                c1 = st.selectbox("Player 1", [p['name'] for p in players], key="c1")
                remaining = [p['name'] for p in players if p['name'] != c1]
                
                if remaining:
                    c2 = st.selectbox("Player 2", remaining, key="c2")
                    if st.button("Add", use_container_width=True, type="primary"):
                        if c1 not in conflicts: conflicts[c1] = []
                        if c2 not in conflicts: conflicts[c2] = []
                        if c2 not in conflicts[c1]: conflicts[c1].append(c2)
                        if c1 not in conflicts[c2]: conflicts[c2].append(c1)
                        save_conflicts(conflicts)
                        st.success("✅ Added")
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.subheader("Existing")
                if conflicts:
                    displayed = set()
                    for player, conflict_list in conflicts.items():
                        for conflict in conflict_list:
                            pair = tuple(sorted([player, conflict]))
                            if pair not in displayed:
                                displayed.add(pair)
                                c1, c2 = st.columns([3, 1])
                                c1.write(f"{pair[0]} ⚠️ {pair[1]}")
                                if c2.button("×", key=f"rc{pair}"):
                                    if pair[1] in conflicts.get(pair[0], []): conflicts[pair[0]].remove(pair[1])
                                    if pair[0] in conflicts.get(pair[1], []): conflicts[pair[1]].remove(pair[0])
                                    conflicts = {k: v for k, v in conflicts.items() if v}
                                    save_conflicts(conflicts)
                                    st.rerun()
                else:
                    st.info("No conflicts")
                st.markdown('</div>', unsafe_allow_html=True)

# CREATE GAME PAGE
elif st.session_state.page == 'game':
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<h2>Create Game</h2>', unsafe_allow_html=True)
    st.markdown('<p>Select players and generate balanced teams</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    players = load_players()
    
    if not players:
        st.warning("Add players first")
    else:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            game_name = st.text_input("Game Name", f"Game {len(load_games()) + 1}")
            
            col_a, col_b = st.columns(2)
            if col_a.button("Select All", use_container_width=True):
                st.session_state.selected_all = True
                st.rerun()
            if col_b.button("Clear", use_container_width=True):
                st.session_state.selected_all = False
                st.rerun()
            
            selected = []
            for player in players:
                default = st.session_state.get('selected_all', True)
                if st.checkbox(f"{player['name']} ({player.get('position', 'N/A')}) - {player.get('overall_skill', 5)}/10",
                             value=default, key=f"sel{player['name']}"):
                    selected.append(player)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.write(f"**{len(selected)} selected**")
            
            if len(selected) >= 2:
                num_teams = st.number_input("Teams", 2, min(len(selected), 10), 2)
                
                with st.expander("Lock Players"):
                    for i in range(num_teams):
                        locked = st.multiselect(f"Team {i+1}", [p['name'] for p in selected], key=f"lock{i}")
                        for pname in locked:
                            st.session_state.locked_players[pname] = i
            st.markdown('</div>', unsafe_allow_html=True)
        
        if len(selected) >= num_teams * 2:
            if st.button("⚡ Generate Teams", type="primary", use_container_width=True):
                with st.spinner("Optimizing..."):
                    teams = balance_teams_advanced(selected, num_teams, 
                                                  load_partnerships(), load_conflicts(),
                                                  st.session_state.locked_players)
                    st.session_state.generated_teams = teams
                    st.session_state.game_name = game_name
                    st.success("✅ Generated")
                    st.rerun()
        
        if st.session_state.generated_teams:
            st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            if col1.button("🔄 Regenerate", use_container_width=True):
                teams = balance_teams_advanced(selected, len(st.session_state.generated_teams),
                                              load_partnerships(), load_conflicts(),
                                              st.session_state.locked_players)
                st.session_state.generated_teams = teams
                st.rerun()
            
            if col2.button("💾 Save", use_container_width=True, type="primary"):
                save_game({
                    'name': st.session_state.game_name,
                    'date': datetime.now().isoformat(),
                    'teams': st.session_state.generated_teams,
                    'num_teams': len(st.session_state.generated_teams),
                    'total_players': sum(len(t) for t in st.session_state.generated_teams)
                })
                st.success("✅ Saved")
            
            if col3.button("Clear Locks", use_container_width=True):
                st.session_state.locked_players = {}
                st.rerun()
            
            for idx, team in enumerate(st.session_state.generated_teams):
                color = TEAM_COLORS[idx % len(TEAM_COLORS)]
                metrics = calculate_team_metrics(team)
                
                st.markdown(f"""
                <div class="team-card team-card-{color}">
                    <h3>Team {idx + 1}</h3>
                    <div style="opacity: 0.9; margin-bottom: 16px;">
                        {len(team)} players • Score: {metrics['total_score']:.1f}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2, col3, col4, col5 = st.columns(5)
                col1.metric("Running", f"{metrics['avg_running']:.1f}")
                col2.metric("Goals", f"{metrics['avg_goals']:.1f}")
                col3.metric("Skill", f"{metrics['avg_skill']:.1f}")
                col4.metric("Age", f"{metrics['avg_age']:.0f}")
                col5.metric("Height", f"{metrics['avg_height']:.0f}cm")
                
                for player in team:
                    pos = player.get('position', 'Midfielder').lower()
                    st.markdown(f"""
                    <div class="player-card">
                        <div class="player-name">
                            <span class="badge badge-{pos}">{player.get('position', 'MID')[:3]}</span>
                            {player['name']}
                        </div>
                        <div class="player-stats">
                            Run: {player.get('running_ability', 5)}/10 • 
                            Goal: {player.get('goal_scoring', 5)}/10 • 
                            Skill: {player.get('overall_skill', 5)}/10
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

# HISTORY PAGE
elif st.session_state.page == 'history':
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<h2>Game History</h2>', unsafe_allow_html=True)
    st.markdown('<p>View past games</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    games = load_games()
    
    if not games:
        st.info("No games yet")
    else:
        for idx, game in enumerate(reversed(games)):
            with st.expander(f"🎮 {game['name']} - {game['date'][:10]}"):
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.write(f"**Date:** {game['date'][:16]}")
                st.write(f"**Teams:** {game['num_teams']}")
                st.write(f"**Players:** {game['total_players']}")
                
                for team_idx, team in enumerate(game['teams']):
                    st.markdown(f"**Team {team_idx + 1}:** {', '.join(p['name'] for p in team)}")
                
                if st.button("Delete", key=f"del{idx}", type="secondary"):
                    games.remove(game)
                    save_json(GAMES_FILE, games)
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
