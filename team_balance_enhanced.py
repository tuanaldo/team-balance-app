import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from pulp import LpProblem, LpVariable, LpMinimize, lpSum, LpBinary, value, PULP_CBC_CMD
import random
from typing import Dict, List, Set, Tuple

# Page config
st.set_page_config(
    page_title="Team Balancer Pro",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .team-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 15px;
        color: white;
        margin: 10px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .team-card-blue {
        background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%);
    }
    .team-card-red {
        background: linear-gradient(135deg, #f44336 0%, #d32f2f 100%);
    }
    .team-card-green {
        background: linear-gradient(135deg, #4CAF50 0%, #388E3C 100%);
    }
    .team-card-orange {
        background: linear-gradient(135deg, #FF9800 0%, #F57C00 100%);
    }
    .team-card-purple {
        background: linear-gradient(135deg, #9C27B0 0%, #7B1FA2 100%);
    }
    .team-card-cyan {
        background: linear-gradient(135deg, #00BCD4 0%, #0097A7 100%);
    }
    .player-card {
        background: white;
        padding: 12px;
        border-radius: 8px;
        margin: 8px 0;
        color: #333;
        border-left: 4px solid #667eea;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .metric-card {
        background: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        border: 2px solid #e9ecef;
    }
    .balance-bar {
        background: #e9ecef;
        border-radius: 10px;
        height: 20px;
        overflow: hidden;
        margin: 5px 0;
    }
    .balance-fill {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        height: 100%;
        transition: width 0.3s;
    }
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
    }
    .position-badge {
        display: inline-block;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 0.85em;
        font-weight: 600;
        margin-right: 5px;
    }
    .pos-forward { background: #f44336; color: white; }
    .pos-midfielder { background: #4CAF50; color: white; }
    .pos-defender { background: #2196F3; color: white; }
    .pos-goalkeeper { background: #FF9800; color: white; }
</style>
""", unsafe_allow_html=True)

# Data files
PLAYERS_FILE = "players_inventory.json"
GAMES_FILE = "games_history.json"
PARTNERSHIPS_FILE = "player_partnerships.json"
CONFLICTS_FILE = "player_conflicts.json"

# Position options
POSITIONS = ["Forward", "Midfielder", "Defender", "Goalkeeper"]

# Color schemes for teams
TEAM_COLORS = ["blue", "red", "green", "orange", "purple", "cyan"]

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
    """Calculate overall score for a player (equal weights)"""
    return (
        player.get('running_ability', 5) +
        player.get('goal_scoring', 5) +
        player.get('age', 25) / 5 +  # Normalize age
        player.get('height', 170) / 34 +  # Normalize height
        player.get('overall_skill', 5)
    )

def get_position_value(position):
    """Map position to numeric value for role fit"""
    position_map = {
        "Forward": 4,
        "Midfielder": 3,
        "Defender": 2,
        "Goalkeeper": 1
    }
    return position_map.get(position, 2.5)

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
    """
    Advanced team balancing with partnerships, conflicts, and position awareness
    """
    try:
        prob = LpProblem("Team_Balancing", LpMinimize)
        
        # Decision variables
        assignments = {}
        for i, player in enumerate(players):
            for t in range(num_teams):
                assignments[(i, t)] = LpVariable(f"player_{i}_team_{t}", cat=LpBinary)
        
        # Each player assigned to exactly one team
        for i in range(len(players)):
            prob += lpSum([assignments[(i, t)] for t in range(num_teams)]) == 1
        
        # Lock players to specific teams
        for player_name, team_idx in locked_assignments.items():
            player_idx = next((i for i, p in enumerate(players) if p['name'] == player_name), None)
            if player_idx is not None:
                prob += assignments[(player_idx, team_idx)] == 1
        
        # Team size constraints
        team_size = len(players) // num_teams
        for t in range(num_teams):
            prob += lpSum([assignments[(i, t)] for i in range(len(players))]) >= team_size
            prob += lpSum([assignments[(i, t)] for i in range(len(players))]) <= team_size + 1
        
        # Calculate team scores
        team_scores = {}
        for t in range(num_teams):
            team_score = lpSum([
                assignments[(i, t)] * calculate_player_score(players[i])
                for i in range(len(players))
            ])
            team_scores[t] = team_score
        
        # Position balance - each team should have similar position distribution
        position_scores = {pos: {} for pos in POSITIONS}
        for pos in POSITIONS:
            for t in range(num_teams):
                position_count = lpSum([
                    assignments[(i, t)]
                    for i in range(len(players))
                    if players[i].get('position') == pos
                ])
                position_scores[pos][t] = position_count
        
        # Minimize variance in team scores
        max_score = LpVariable("max_score")
        min_score = LpVariable("min_score")
        
        for t in range(num_teams):
            prob += team_scores[t] <= max_score
            prob += team_scores[t] >= min_score
        
        prob += max_score - min_score  # Minimize difference
        
        # Add partnership bonuses (encourage partnerships to be on same team)
        partnership_bonus = 0
        for player1, partners in partnerships.items():
            p1_idx = next((i for i, p in enumerate(players) if p['name'] == player1), None)
            if p1_idx is not None:
                for player2 in partners:
                    p2_idx = next((i for i, p in enumerate(players) if p['name'] == player2), None)
                    if p2_idx is not None and p1_idx < p2_idx:  # Avoid double counting
                        for t in range(num_teams):
                            # Penalty if partners are NOT together
                            partnership_bonus += 10 * (2 - assignments[(p1_idx, t)] - assignments[(p2_idx, t)])
        
        prob += partnership_bonus
        
        # Add conflict penalties (separate conflicting players)
        conflict_penalty = 0
        for player1, conflicts_list in conflicts.items():
            p1_idx = next((i for i, p in enumerate(players) if p['name'] == player1), None)
            if p1_idx is not None:
                for player2 in conflicts_list:
                    p2_idx = next((i for i, p in enumerate(players) if p['name'] == player2), None)
                    if p2_idx is not None and p1_idx < p2_idx:
                        for t in range(num_teams):
                            # Penalty if conflicts are together
                            conflict_penalty += 20 * (assignments[(p1_idx, t)] + assignments[(p2_idx, t)] - 1)
        
        prob += conflict_penalty
        
        # Solve
        prob.solve(PULP_CBC_CMD(msg=0))
        
        # Extract solution
        teams = [[] for _ in range(num_teams)]
        for i, player in enumerate(players):
            for t in range(num_teams):
                if value(assignments[(i, t)]) == 1:
                    teams[t].append(player)
                    break
        
        return teams
    
    except Exception as e:
        st.error(f"Optimization failed: {e}")
        # Fallback to greedy algorithm
        return balance_teams_greedy(players, num_teams, locked_assignments)

def balance_teams_greedy(players, num_teams, locked_assignments):
    """Greedy fallback algorithm with position awareness"""
    # Sort players by score
    sorted_players = sorted(players, key=calculate_player_score, reverse=True)
    teams = [[] for _ in range(num_teams)]
    
    # First, assign locked players
    assigned_players = set()
    for player_name, team_idx in locked_assignments.items():
        player = next((p for p in sorted_players if p['name'] == player_name), None)
        if player:
            teams[team_idx].append(player)
            assigned_players.add(player_name)
    
    # Remove assigned players from sorted list
    sorted_players = [p for p in sorted_players if p['name'] not in assigned_players]
    
    # Distribute remaining players
    for player in sorted_players:
        # Find team with lowest total score
        team_scores = [sum(calculate_player_score(p) for p in team) for team in teams]
        min_team = team_scores.index(min(team_scores))
        teams[min_team].append(player)
    
    return teams

def render_team_card(team_name, team_players, team_idx, show_swap=False):
    """Render a beautiful team card with metrics"""
    color = TEAM_COLORS[team_idx % len(TEAM_COLORS)]
    metrics = calculate_team_metrics(team_players)
    
    st.markdown(f"""
    <div class="team-card team-card-{color}">
        <h2 style="margin:0; font-size: 28px;">🏆 {team_name}</h2>
        <p style="margin: 5px 0; opacity: 0.9;">{len(team_players)} players • Score: {metrics['total_score']:.1f}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Metrics in columns
    cols = st.columns(5)
    cols[0].metric("Running", f"{metrics['avg_running']:.1f}")
    cols[1].metric("Goals", f"{metrics['avg_goals']:.1f}")
    cols[2].metric("Skill", f"{metrics['avg_skill']:.1f}")
    cols[3].metric("Avg Age", f"{metrics['avg_age']:.0f}")
    cols[4].metric("Avg Height", f"{metrics['avg_height']:.0f}cm")
    
    # Position distribution
    st.write("**Position Distribution:**")
    pos_cols = st.columns(4)
    for idx, pos in enumerate(POSITIONS):
        count = metrics['position_dist'][pos]
        pos_cols[idx].markdown(f"<span class='position-badge pos-{pos.lower()}'>{pos[:3]}: {count}</span>", unsafe_allow_html=True)
    
    # Players
    st.write("**Players:**")
    for player in team_players:
        pos_class = player.get('position', 'Midfielder').lower()
        st.markdown(f"""
        <div class="player-card">
            <span class='position-badge pos-{pos_class}'>{player.get('position', 'MID')[:3]}</span>
            <strong>{player['name']}</strong> • 
            Run: {player.get('running_ability', 5)}/10 • 
            Goal: {player.get('goal_scoring', 5)}/10 • 
            Skill: {player.get('overall_skill', 5)}/10
        </div>
        """, unsafe_allow_html=True)
        
        if show_swap:
            if st.button(f"Swap {player['name']}", key=f"swap_{team_idx}_{player['name']}"):
                st.session_state.swap_player = player
                st.session_state.swap_from_team = team_idx

def render_balance_comparison(teams):
    """Render side-by-side team comparison"""
    st.subheader("⚖️ Team Balance Comparison")
    
    metrics_list = [calculate_team_metrics(team) for team in teams]
    
    # Get max values for normalization
    max_score = max(m['total_score'] for m in metrics_list)
    max_running = max(m['avg_running'] for m in metrics_list)
    max_goals = max(m['avg_goals'] for m in metrics_list)
    max_skill = max(m['avg_skill'] for m in metrics_list)
    
    comparison_df = pd.DataFrame([
        {
            'Team': f"Team {i+1}",
            'Total Score': m['total_score'],
            'Running': m['avg_running'],
            'Goals': m['avg_goals'],
            'Skill': m['avg_skill'],
            'Forwards': m['position_dist']['Forward'],
            'Midfielders': m['position_dist']['Midfielder'],
            'Defenders': m['position_dist']['Defender'],
            'Goalkeepers': m['position_dist']['Goalkeeper']
        }
        for i, m in enumerate(metrics_list)
    ])
    
    st.dataframe(comparison_df, use_container_width=True, hide_index=True)
    
    # Visual balance bars
    st.write("**Overall Balance:**")
    for i, m in enumerate(metrics_list):
        progress = m['total_score'] / max_score if max_score > 0 else 0
        st.markdown(f"""
        <div>
            <strong>Team {i+1}</strong>
            <div class="balance-bar">
                <div class="balance-fill" style="width: {progress*100}%"></div>
            </div>
            <small>{m['total_score']:.1f} points</small>
        </div>
        """, unsafe_allow_html=True)

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

# Sidebar navigation
with st.sidebar:
    st.title("⚽ Team Balancer Pro")
    st.markdown("---")
    
    if st.button("🏠 Home", use_container_width=True):
        st.session_state.page = 'home'
        st.rerun()
    
    if st.button("👥 Manage Players", use_container_width=True):
        st.session_state.page = 'players'
        st.rerun()
    
    if st.button("🎮 Create Game", use_container_width=True):
        st.session_state.page = 'game'
        st.rerun()
    
    if st.button("🤝 Partnerships & Conflicts", use_container_width=True):
        st.session_state.page = 'partnerships'
        st.rerun()
    
    if st.button("📊 Game History", use_container_width=True):
        st.session_state.page = 'history'
        st.rerun()
    
    st.markdown("---")
    st.caption("Advanced team balancing with AI-powered optimization")

# HOME PAGE
if st.session_state.page == 'home':
    st.title("⚽ Welcome to Team Balancer Pro")
    st.markdown("### Create perfectly balanced teams with advanced features")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3>👥</h3>
            <h4>Player Management</h4>
            <p>Maintain your player inventory with stats and positions</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h3>🎯</h3>
            <h4>Smart Balancing</h4>
            <p>AI-powered optimization with partnerships and conflicts</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h3>✨</h3>
            <h4>Manual Adjustments</h4>
            <p>Fine-tune teams with drag-and-drop swapping</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Quick stats
    players = load_players()
    games = load_games()
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Players", len(players))
    col2.metric("Games Played", len(games))
    
    if players:
        avg_skill = sum(p.get('overall_skill', 5) for p in players) / len(players)
        col3.metric("Avg Skill Level", f"{avg_skill:.1f}/10")
        
        positions_count = {}
        for p in players:
            pos = p.get('position', 'Midfielder')
            positions_count[pos] = positions_count.get(pos, 0) + 1
        most_common_pos = max(positions_count, key=positions_count.get) if positions_count else "N/A"
        col4.metric("Most Common Position", most_common_pos)
    
    st.markdown("---")
    st.info("👈 Use the sidebar to navigate to different sections")

# PLAYER MANAGEMENT PAGE
elif st.session_state.page == 'players':
    st.title("👥 Player Inventory Management")
    
    players = load_players()
    
    tab1, tab2, tab3 = st.tabs(["➕ Add Player", "📝 Edit Players", "📥 Import/Export"])
    
    with tab1:
        st.subheader("Add New Player")
        with st.form("add_player_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Player Name*")
                position = st.selectbox("Position*", POSITIONS)
                running_ability = st.slider("Running Ability", 1, 10, 5)
                goal_scoring = st.slider("Goal Scoring", 1, 10, 5)
            
            with col2:
                age = st.number_input("Age", 10, 60, 25)
                height = st.number_input("Height (cm)", 140, 220, 175)
                overall_skill = st.slider("Overall Skill", 1, 10, 5)
            
            submitted = st.form_submit_button("Add Player", use_container_width=True)
            
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
                    st.success(f"✅ Added {name} to inventory!")
                    st.rerun()
    
    with tab2:
        st.subheader("Edit Existing Players")
        
        if not players:
            st.info("No players in inventory. Add some players first!")
        else:
            # Display players in a nice format
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
                            st.success(f"Deleted player!")
                            st.rerun()
                    
                    col1, col2, col3 = st.columns(3)
                    player['running_ability'] = col1.slider("Running", 1, 10, player.get('running_ability', 5), key=f"run_{idx}")
                    player['goal_scoring'] = col2.slider("Goals", 1, 10, player.get('goal_scoring', 5), key=f"goal_{idx}")
                    player['overall_skill'] = col3.slider("Skill", 1, 10, player.get('overall_skill', 5), key=f"skill_{idx}")
            
            if st.button("💾 Save All Changes", type="primary", use_container_width=True):
                save_players(players)
                st.success("✅ All changes saved!")
                st.rerun()
    
    with tab3:
        st.subheader("Import/Export Players")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Export Current Players**")
            if players:
                df = pd.DataFrame(players)
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download as CSV",
                    data=csv,
                    file_name=f"players_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            else:
                st.info("No players to export")
        
        with col2:
            st.write("**Import Players from CSV**")
            uploaded_file = st.file_uploader("Choose CSV file", type=['csv'])
            
            if uploaded_file:
                if st.button("Import Players", use_container_width=True):
                    try:
                        df = pd.read_csv(uploaded_file)
                        required_cols = ['name', 'position']
                        
                        if not all(col in df.columns for col in required_cols):
                            st.error(f"CSV must contain columns: {required_cols}")
                        else:
                            # Clear existing and import
                            new_players = df.to_dict('records')
                            save_players(new_players)
                            st.success(f"✅ Imported {len(new_players)} players!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error importing: {e}")

# PARTNERSHIPS & CONFLICTS PAGE
elif st.session_state.page == 'partnerships':
    st.title("🤝 Player Partnerships & Conflicts")
    st.markdown("Define player relationships to improve team balancing")
    
    players = load_players()
    partnerships = load_partnerships()
    conflicts = load_conflicts()
    
    if not players:
        st.warning("⚠️ Add players first before managing partnerships!")
    else:
        tab1, tab2 = st.tabs(["🤝 Partnerships", "⚠️ Conflicts"])
        
        with tab1:
            st.subheader("Player Partnerships")
            st.info("Partners will be encouraged to play on the same team")
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.write("**Add New Partnership**")
                player1 = st.selectbox("Player 1", [p['name'] for p in players], key="partner1")
                remaining_players = [p['name'] for p in players if p['name'] != player1]
                
                if remaining_players:
                    player2 = st.selectbox("Player 2", remaining_players, key="partner2")
                    
                    if st.button("Add Partnership", use_container_width=True):
                        if player1 not in partnerships:
                            partnerships[player1] = []
                        if player2 not in partnerships:
                            partnerships[player2] = []
                        
                        if player2 not in partnerships[player1]:
                            partnerships[player1].append(player2)
                        if player1 not in partnerships[player2]:
                            partnerships[player2].append(player1)
                        
                        save_partnerships(partnerships)
                        st.success(f"✅ Partnership created: {player1} ↔️ {player2}")
                        st.rerun()
            
            with col2:
                st.write("**Existing Partnerships**")
                if partnerships:
                    displayed_pairs = set()
                    for player, partners in partnerships.items():
                        for partner in partners:
                            pair = tuple(sorted([player, partner]))
                            if pair not in displayed_pairs:
                                displayed_pairs.add(pair)
                                st.markdown(f"- **{pair[0]}** ↔️ **{pair[1]}**")
                                if st.button(f"Remove", key=f"remove_partner_{pair[0]}_{pair[1]}"):
                                    if pair[1] in partnerships.get(pair[0], []):
                                        partnerships[pair[0]].remove(pair[1])
                                    if pair[0] in partnerships.get(pair[1], []):
                                        partnerships[pair[1]].remove(pair[0])
                                    
                                    # Clean up empty entries
                                    partnerships = {k: v for k, v in partnerships.items() if v}
                                    save_partnerships(partnerships)
                                    st.rerun()
                else:
                    st.info("No partnerships defined yet")
        
        with tab2:
            st.subheader("Player Conflicts")
            st.info("Conflicts will be separated into different teams")
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.write("**Add New Conflict**")
                player1 = st.selectbox("Player 1", [p['name'] for p in players], key="conflict1")
                remaining_players = [p['name'] for p in players if p['name'] != player1]
                
                if remaining_players:
                    player2 = st.selectbox("Player 2", remaining_players, key="conflict2")
                    
                    if st.button("Add Conflict", use_container_width=True):
                        if player1 not in conflicts:
                            conflicts[player1] = []
                        if player2 not in conflicts:
                            conflicts[player2] = []
                        
                        if player2 not in conflicts[player1]:
                            conflicts[player1].append(player2)
                        if player1 not in conflicts[player2]:
                            conflicts[player2].append(player1)
                        
                        save_conflicts(conflicts)
                        st.success(f"✅ Conflict added: {player1} ⚠️ {player2}")
                        st.rerun()
            
            with col2:
                st.write("**Existing Conflicts**")
                if conflicts:
                    displayed_pairs = set()
                    for player, conflict_list in conflicts.items():
                        for conflict in conflict_list:
                            pair = tuple(sorted([player, conflict]))
                            if pair not in displayed_pairs:
                                displayed_pairs.add(pair)
                                st.markdown(f"- **{pair[0]}** ⚠️ **{pair[1]}**")
                                if st.button(f"Remove", key=f"remove_conflict_{pair[0]}_{pair[1]}"):
                                    if pair[1] in conflicts.get(pair[0], []):
                                        conflicts[pair[0]].remove(pair[1])
                                    if pair[0] in conflicts.get(pair[1], []):
                                        conflicts[pair[1]].remove(pair[0])
                                    
                                    # Clean up empty entries
                                    conflicts = {k: v for k, v in conflicts.items() if v}
                                    save_conflicts(conflicts)
                                    st.rerun()
                else:
                    st.info("No conflicts defined yet")

# GAME CREATION PAGE
elif st.session_state.page == 'game':
    st.title("🎮 Create Balanced Teams")
    
    players = load_players()
    
    if not players:
        st.warning("⚠️ No players in inventory! Add players first.")
    else:
        # Game setup
        st.subheader("Game Setup")
        
        col1, col2 = st.columns(2)
        
        with col1:
            game_name = st.text_input("Game Name", f"Game {len(load_games()) + 1}")
            
            # Player selection
            st.write("**Select Players:**")
            selected_players = []
            
            # Quick select buttons
            col_a, col_b = st.columns(2)
            if col_a.button("Select All", use_container_width=True):
                st.session_state.selected_all = True
            if col_b.button("Clear All", use_container_width=True):
                st.session_state.selected_all = False
            
            for player in players:
                default_val = st.session_state.get('selected_all', True)
                if st.checkbox(
                    f"{player['name']} ({player.get('position', 'N/A')}) - Skill: {player.get('overall_skill', 5)}/10",
                    value=default_val,
                    key=f"select_{player['name']}"
                ):
                    selected_players.append(player)
        
        with col2:
            st.write(f"**{len(selected_players)} players selected**")
            
            if len(selected_players) >= 2:
                # Team configuration
                num_teams = st.number_input("Number of Teams", 2, min(len(selected_players), 10), 2)
                
                st.write("**Lock Players to Teams (Optional):**")
                st.caption("Assign specific players to teams before balancing")
                
                for i in range(num_teams):
                    with st.expander(f"Team {i+1} Locks"):
                        locked_to_this_team = st.multiselect(
                            f"Players for Team {i+1}",
                            [p['name'] for p in selected_players],
                            key=f"lock_team_{i}"
                        )
                        for player_name in locked_to_this_team:
                            st.session_state.locked_players[player_name] = i
        
        # Generate teams button
        if len(selected_players) >= num_teams * 2:
            if st.button("⚡ Generate Balanced Teams", type="primary", use_container_width=True):
                with st.spinner("Balancing teams with AI optimization..."):
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
                    st.success("✅ Teams generated successfully!")
                    st.rerun()
        else:
            st.warning(f"⚠️ Select at least {num_teams * 2} players to create {num_teams} teams")
        
        # Display generated teams
        if st.session_state.generated_teams:
            st.markdown("---")
            st.subheader("🏆 Generated Teams")
            
            # Action buttons
            col1, col2, col3 = st.columns(3)
            
            if col1.button("🔄 Regenerate Teams", use_container_width=True):
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
            
            if col2.button("💾 Save Game", use_container_width=True):
                game_data = {
                    'name': st.session_state.game_name,
                    'date': datetime.now().isoformat(),
                    'teams': st.session_state.generated_teams,
                    'num_teams': len(st.session_state.generated_teams),
                    'total_players': sum(len(team) for team in st.session_state.generated_teams)
                }
                save_game(game_data)
                st.success("✅ Game saved to history!")
            
            if col3.button("🔓 Clear Locks", use_container_width=True):
                st.session_state.locked_players = {}
                st.rerun()
            
            # Balance comparison
            render_balance_comparison(st.session_state.generated_teams)
            
            st.markdown("---")
            
            # Team cards with swap functionality
            st.subheader("Teams & Manual Adjustments")
            
            # Handle swaps
            if st.session_state.swap_player:
                st.info(f"🔄 Click on a player from a different team to swap with **{st.session_state.swap_player['name']}**")
                if st.button("❌ Cancel Swap"):
                    st.session_state.swap_player = None
                    st.session_state.swap_from_team = None
                    st.rerun()
            
            # Display teams in columns
            team_cols = st.columns(min(len(st.session_state.generated_teams), 3))
            
            for idx, team in enumerate(st.session_state.generated_teams):
                with team_cols[idx % len(team_cols)]:
                    render_team_card(f"Team {idx + 1}", team, idx, show_swap=True)
                    
                    # Handle swap target selection
                    if st.session_state.swap_player and st.session_state.swap_from_team != idx:
                        st.write("**Select player to swap with:**")
                        for player in team:
                            if st.button(f"↔️ Swap with {player['name']}", key=f"swaptarget_{idx}_{player['name']}"):
                                # Perform swap
                                from_team = st.session_state.swap_from_team
                                swap_player = st.session_state.swap_player
                                
                                # Find and swap
                                from_team_list = st.session_state.generated_teams[from_team]
                                to_team_list = st.session_state.generated_teams[idx]
                                
                                from_team_list.remove(swap_player)
                                to_team_list.remove(player)
                                
                                from_team_list.append(player)
                                to_team_list.append(swap_player)
                                
                                st.session_state.swap_player = None
                                st.session_state.swap_from_team = None
                                st.success(f"✅ Swapped {swap_player['name']} ↔️ {player['name']}")
                                st.rerun()
            
            # Export options
            st.markdown("---")
            st.subheader("📤 Export Teams")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Create formatted text for sharing
                export_text = f"⚽ {st.session_state.game_name}\n"
                export_text += f"📅 {datetime.now().strftime('%Y-%m-%d')}\n\n"
                
                for idx, team in enumerate(st.session_state.generated_teams):
                    export_text += f"🏆 TEAM {idx + 1}\n"
                    export_text += "=" * 30 + "\n"
                    for player in team:
                        export_text += f"• {player['name']} ({player.get('position', 'N/A')})\n"
                    export_text += "\n"
                
                st.text_area("Copy & Share", export_text, height=300)
            
            with col2:
                # Create CSV export
                export_data = []
                for idx, team in enumerate(st.session_state.generated_teams):
                    for player in team:
                        export_data.append({
                            'Team': f"Team {idx + 1}",
                            'Player': player['name'],
                            'Position': player.get('position', 'N/A'),
                            'Skill': player.get('overall_skill', 5),
                            'Running': player.get('running_ability', 5),
                            'Goals': player.get('goal_scoring', 5)
                        })
                
                df = pd.DataFrame(export_data)
                csv = df.to_csv(index=False)
                
                st.download_button(
                    label="📥 Download as CSV",
                    data=csv,
                    file_name=f"{st.session_state.game_name.replace(' ', '_')}_teams.csv",
                    mime="text/csv",
                    use_container_width=True
                )

# GAME HISTORY PAGE
elif st.session_state.page == 'history':
    st.title("📊 Game History")
    
    games = load_games()
    
    if not games:
        st.info("No games played yet. Create your first game!")
    else:
        st.write(f"**Total Games: {len(games)}**")
        
        # Reverse to show newest first
        for idx, game in enumerate(reversed(games)):
            with st.expander(f"🎮 {game['name']} - {game['date'][:10]}", expanded=(idx == 0)):
                st.write(f"**Date:** {game['date'][:16]}")
                st.write(f"**Teams:** {game['num_teams']}")
                st.write(f"**Total Players:** {game['total_players']}")
                
                # Show teams
                for team_idx, team in enumerate(game['teams']):
                    st.markdown(f"**Team {team_idx + 1}:** {', '.join(p['name'] for p in team)}")
                
                if st.button(f"🗑️ Delete Game", key=f"delete_game_{idx}"):
                    games.remove(game)
                    save_json(GAMES_FILE, games)
                    st.success("Game deleted!")
                    st.rerun()
