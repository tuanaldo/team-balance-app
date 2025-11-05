import streamlit as st
import pandas as pd
from datetime import datetime
from pulp import LpProblem, LpVariable, LpMinimize, lpSum, LpBinary, value, PULP_CBC_CMD
from typing import Dict, List
from supabase import create_client, Client

# Page config
st.set_page_config(
    page_title="Team Balance",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize Supabase client
@st.cache_resource
def init_supabase() -> Client:
    """Initialize Supabase client with credentials from secrets"""
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

# Get Supabase client
try:
    supabase = init_supabase()
except Exception as e:
    st.error(f"""
    ⚠️ Supabase not configured!
    
    Please add your Supabase credentials:
    1. Go to Streamlit Cloud → App Settings → Secrets
    2. Add:
    ```
    [supabase]
    url = "YOUR_SUPABASE_URL"
    key = "YOUR_SUPABASE_KEY"
    ```
    
    Error: {str(e)}
    """)
    st.stop()

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
    
    .team-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 16px;
        padding: 24px;
        margin: 16px 0;
        color: white;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
    }
    
    .team-card-blue { background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); }
    .team-card-green { background: linear-gradient(135deg, #10b981 0%, #059669 100%); }
    .team-card-purple { background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%); }
    .team-card-orange { background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); }
    .team-card-red { background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); }
    
    .player-card {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 12px;
        padding: 16px;
        margin: 8px 0;
        color: #1a1a1a;
    }
    
    .badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        margin-right: 8px;
    }
    
    .badge-forward { background: #fee; color: #dc2626; }
    .badge-midfielder { background: #efe; color: #059669; }
    .badge-defender { background: #eef; color: #2563eb; }
    .badge-goalkeeper { background: #ffe; color: #d97706; }
    
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
    }
    
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
</style>
""", unsafe_allow_html=True)

POSITIONS = ["Forward", "Midfielder", "Defender", "Goalkeeper"]
TEAM_COLORS = ["blue", "green", "purple", "orange", "red"]

# Database functions
def load_players():
    """Load all players from Supabase"""
    try:
        response = supabase.table('players').select('*').order('created_at', desc=False).execute()
        return response.data
    except Exception as e:
        st.error(f"Error loading players: {e}")
        return []

def normalize_player_name(name):
    """Normalize player name to title case for consistency"""
    return name.strip().title() if name else ""

def safe_get_value(player, key, default, min_val, max_val):
    """Safely get a value from player dict and clamp it within range"""
    value = player.get(key, default)
    return max(min_val, min(max_val, value))

def add_player(player_data):
    """Add a new player to Supabase"""
    try:
        # Normalize name for consistency
        if 'name' in player_data:
            player_data['name'] = normalize_player_name(player_data['name'])
        
        # Validate and clamp values
        player_data['age'] = max(10, min(60, player_data.get('age', 25)))
        player_data['height'] = max(140, min(220, player_data.get('height', 175)))
        player_data['running_ability'] = max(1, min(10, player_data.get('running_ability', 5)))
        player_data['goal_scoring'] = max(1, min(10, player_data.get('goal_scoring', 5)))
        player_data['overall_skill'] = max(1, min(10, player_data.get('overall_skill', 5)))
        
        response = supabase.table('players').insert(player_data).execute()
        return True
    except Exception as e:
        st.error(f"Error adding player: {e}")
        return False

def update_player(player_id, updates):
    """Update a player in Supabase"""
    try:
        # Normalize name
        if 'name' in updates:
            updates['name'] = normalize_player_name(updates['name'])
        
        # Validate and clamp values
        if 'age' in updates:
            updates['age'] = max(10, min(60, updates['age']))
        if 'height' in updates:
            updates['height'] = max(140, min(220, updates['height']))
        if 'running_ability' in updates:
            updates['running_ability'] = max(1, min(10, updates['running_ability']))
        if 'goal_scoring' in updates:
            updates['goal_scoring'] = max(1, min(10, updates['goal_scoring']))
        if 'overall_skill' in updates:
            updates['overall_skill'] = max(1, min(10, updates['overall_skill']))
        
        response = supabase.table('players').update(updates).eq('id', player_id).execute()
        return True
    except Exception as e:
        st.error(f"Error updating player: {e}")
        return False

def delete_player(player_id):
    """Delete a player from Supabase"""
    try:
        response = supabase.table('players').delete().eq('id', player_id).execute()
        return True
    except Exception as e:
        st.error(f"Error deleting player: {e}")
        return False

def load_games():
    """Load all games from Supabase"""
    try:
        response = supabase.table('games').select('*').order('created_at', desc=True).execute()
        return response.data
    except Exception as e:
        st.error(f"Error loading games: {e}")
        return []

def save_game(game_data):
    """Save a game to Supabase"""
    try:
        response = supabase.table('games').insert(game_data).execute()
        return True
    except Exception as e:
        st.error(f"Error saving game: {e}")
        return False

def delete_game(game_id):
    """Delete a game from Supabase"""
    try:
        response = supabase.table('games').delete().eq('id', game_id).execute()
        return True
    except Exception as e:
        st.error(f"Error deleting game: {e}")
        return False

def load_partnerships():
    """Load partnerships from Supabase"""
    try:
        response = supabase.table('partnerships').select('*').execute()
        partnerships = {}
        for p in response.data:
            if p['player1'] not in partnerships:
                partnerships[p['player1']] = []
            partnerships[p['player1']].append(p['player2'])
        return partnerships
    except Exception as e:
        st.error(f"Error loading partnerships: {e}")
        return {}

def add_partnership(player1, player2):
    """Add a partnership to Supabase"""
    try:
        supabase.table('partnerships').insert({'player1': player1, 'player2': player2}).execute()
        return True
    except Exception as e:
        st.error(f"Error adding partnership: {e}")
        return False

def delete_partnership(player1, player2):
    """Delete a partnership from Supabase"""
    try:
        supabase.table('partnerships').delete().eq('player1', player1).eq('player2', player2).execute()
        supabase.table('partnerships').delete().eq('player1', player2).eq('player2', player1).execute()
        return True
    except Exception as e:
        return False

def load_conflicts():
    """Load conflicts from Supabase"""
    try:
        response = supabase.table('conflicts').select('*').execute()
        conflicts = {}
        for c in response.data:
            if c['player1'] not in conflicts:
                conflicts[c['player1']] = []
            conflicts[c['player1']].append(c['player2'])
        return conflicts
    except Exception as e:
        st.error(f"Error loading conflicts: {e}")
        return {}

def add_conflict(player1, player2):
    """Add a conflict to Supabase"""
    try:
        supabase.table('conflicts').insert({'player1': player1, 'player2': player2}).execute()
        return True
    except Exception as e:
        st.error(f"Error adding conflict: {e}")
        return False

def delete_conflict(player1, player2):
    """Delete a conflict from Supabase"""
    try:
        supabase.table('conflicts').delete().eq('player1', player1).eq('player2', player2).execute()
        supabase.table('conflicts').delete().eq('player1', player2).eq('player2', player1).execute()
        return True
    except Exception as e:
        return False

# Team balancing functions
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
    st.markdown('<div style="font-size: 24px; font-weight: 600; padding: 10px 0;">⚽ Team Balance</div>', unsafe_allow_html=True)

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
                else:
                    # Check for duplicates (case-insensitive)
                    normalized_name = normalize_player_name(name)
                    existing_names = [normalize_player_name(p['name']) for p in players]
                    
                    if normalized_name in existing_names:
                        st.error(f"Player '{normalized_name}' already exists (case-insensitive match)")
                    else:
                        player_data = {
                            'name': name,
                            'position': position,
                            'running_ability': running,
                            'goal_scoring': goals,
                            'age': age,
                            'height': height,
                            'overall_skill': skill
                        }
                        if add_player(player_data):
                            st.success(f"✅ Added {normalized_name}")
                            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab2:
        if not players:
            st.info("No players yet")
        else:
            st.info("💡 Edit player stats below and click Save Changes to update the database")
            
            for player in players:
                with st.expander(f"{player['name']} - {player.get('position', 'N/A')}"):
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    player_id = player['id']
                    
                    # Safely get clamped values
                    current_age = safe_get_value(player, 'age', 25, 10, 60)
                    current_height = safe_get_value(player, 'height', 175, 140, 220)
                    current_running = safe_get_value(player, 'running_ability', 5, 1, 10)
                    current_goals = safe_get_value(player, 'goal_scoring', 5, 1, 10)
                    current_skill = safe_get_value(player, 'overall_skill', 5, 1, 10)
                    
                    with col1:
                        new_name = st.text_input("Name", player['name'], key=f"n{player_id}")
                        new_position = st.selectbox("Position", POSITIONS, 
                                                    index=POSITIONS.index(player.get('position', 'Midfielder')),
                                                    key=f"p{player_id}")
                    
                    with col2:
                        new_age = st.number_input("Age", 10, 60, current_age, key=f"a{player_id}")
                        new_height = st.number_input("Height", 140, 220, current_height, key=f"h{player_id}")
                    
                    with col3:
                        if st.button("Delete", key=f"d{player_id}", type="secondary"):
                            if delete_player(player_id):
                                st.success("Deleted!")
                                st.rerun()
                    
                    col1, col2, col3 = st.columns(3)
                    new_running = col1.slider("Running", 1, 10, current_running, key=f"r{player_id}")
                    new_goals = col2.slider("Goals", 1, 10, current_goals, key=f"g{player_id}")
                    new_skill = col3.slider("Skill", 1, 10, current_skill, key=f"s{player_id}")
                    
                    if st.button("💾 Save Changes for This Player", key=f"save{player_id}", use_container_width=True):
                        updates = {
                            'name': new_name,
                            'position': new_position,
                            'age': new_age,
                            'height': new_height,
                            'running_ability': new_running,
                            'goal_scoring': new_goals,
                            'overall_skill': new_skill
                        }
                        if update_player(player_id, updates):
                            st.success("✅ Updated!")
                            st.rerun()
    
    with tab3:
        col1, col2 = st.columns(2)
        
        with col1:
            if players:
                # Convert to pandas and download
                df_data = []
                for p in players:
                    df_data.append({
                        'name': p['name'],
                        'position': p['position'],
                        'running_ability': p.get('running_ability', 5),
                        'goal_scoring': p.get('goal_scoring', 5),
                        'age': p.get('age', 25),
                        'height': p.get('height', 175),
                        'overall_skill': p.get('overall_skill', 5)
                    })
                csv = pd.DataFrame(df_data).to_csv(index=False)
                st.download_button("📥 Download CSV", csv, 
                                 f"players_{datetime.now().strftime('%Y%m%d')}.csv",
                                 mime="text/csv", use_container_width=True)
        
        with col2:
            uploaded = st.file_uploader("Import CSV", type=['csv'])
            if uploaded and st.button("Import", use_container_width=True):
                try:
                    df = pd.read_csv(uploaded)
                    
                    # Get existing player names (normalized for comparison)
                    existing_names = {normalize_player_name(p['name']): True for p in players}
                    
                    count = 0
                    skipped = 0
                    for _, row in df.iterrows():
                        player_data = row.to_dict()
                        
                        # Normalize the name
                        player_name = normalize_player_name(player_data.get('name', ''))
                        
                        # Skip if player already exists (case-insensitive)
                        if player_name in existing_names:
                            skipped += 1
                            continue
                        
                        # Ensure position is valid (case-insensitive)
                        if 'position' in player_data:
                            position_lower = str(player_data['position']).lower()
                            for pos in POSITIONS:
                                if pos.lower() == position_lower:
                                    player_data['position'] = pos
                                    break
                        
                        if add_player(player_data):
                            count += 1
                            existing_names[player_name] = True
                    
                    if count > 0:
                        st.success(f"✅ Imported {count} players")
                    if skipped > 0:
                        st.info(f"ℹ️ Skipped {skipped} duplicate players")
                    
                    if count > 0:
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
                        if add_partnership(p1, p2) and add_partnership(p2, p1):
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
                                    if delete_partnership(pair[0], pair[1]):
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
                        if add_conflict(c1, c2) and add_conflict(c2, c1):
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
                                    if delete_conflict(pair[0], pair[1]):
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
                game_data = {
                    'name': st.session_state.game_name,
                    'num_teams': len(st.session_state.generated_teams),
                    'total_players': sum(len(t) for t in st.session_state.generated_teams),
                    'teams': st.session_state.generated_teams
                }
                if save_game(game_data):
                    st.success("✅ Saved")
            
            if col3.button("Clear Locks", use_container_width=True):
                st.session_state.locked_players = {}
                st.rerun()
            
            for idx, team in enumerate(st.session_state.generated_teams):
                color = TEAM_COLORS[idx % len(TEAM_COLORS)]
                metrics = calculate_team_metrics(team)
                
                st.markdown(f"""
                <div class="team-card team-card-{color}">
                    <h3 style="margin: 0; font-size: 20px;">Team {idx + 1}</h3>
                    <div style="opacity: 0.9; margin-top: 8px; font-size: 14px;">
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
                        <div style="font-size: 15px; font-weight: 600; margin-bottom: 4px;">
                            <span class="badge badge-{pos}">{player.get('position', 'MID')[:3]}</span>
                            {player['name']}
                        </div>
                        <div style="font-size: 13px; color: #666;">
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
        for game in games:
            with st.expander(f"🎮 {game['name']} - {game.get('created_at', '')[:10] if game.get('created_at') else 'No date'}"):
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.write(f"**Teams:** {game['num_teams']}")
                st.write(f"**Players:** {game['total_players']}")
                
                for team_idx, team in enumerate(game.get('teams', [])):
                    st.markdown(f"**Team {team_idx + 1}:** {', '.join(p['name'] for p in team)}")
                
                if st.button("Delete", key=f"del{game['id']}", type="secondary"):
                    if delete_game(game['id']):
                        st.success("Deleted!")
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
