import streamlit as st
import json
from datetime import datetime
import random
from pulp import *
import pandas as pd
from io import StringIO
import os

# Supabase setup (if using cloud version)
# Try Streamlit secrets first (for Streamlit Cloud), then fall back to environment variables
# Support both formats: with [supabase] section and without
try:
    # Try with [supabase] section first
    if "supabase" in st.secrets:
        SUPABASE_URL = st.secrets["supabase"].get("SUPABASE_URL", "")
        SUPABASE_KEY = st.secrets["supabase"].get("SUPABASE_KEY", "")
    else:
        # Try without section (root level)
        SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
        SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")
    
    # Fall back to environment variables if not in secrets
    if not SUPABASE_URL:
        SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    if not SUPABASE_KEY:
        SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
except:
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

USE_SUPABASE = bool(SUPABASE_URL and SUPABASE_KEY)

if USE_SUPABASE:
    try:
        from supabase import create_client
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        # Test connection
        supabase.table('players').select("count", count='exact').limit(1).execute()
        st.session_state.supabase_connected = True
    except Exception as e:
        st.session_state.supabase_connected = False
        USE_SUPABASE = False
        print(f"Supabase connection failed: {e}")
else:
    st.session_state.supabase_connected = False

# Constants
POSITIONS = ["Forward", "Midfielder", "Defender", "Goalkeeper"]
LOCAL_PLAYERS_FILE = "players.json"
LOCAL_GAMES_FILE = "games.json"

# Page config MUST be first Streamlit command
st.set_page_config(
    page_title="Team Balance Pro",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS - Mobile-First & Modern Black/White Design
st.markdown("""
<style>
    /* Import font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }
    
    /* Hide Streamlit branding */
    #MainMenu, footer, header {visibility: hidden;}
    
    /* Main container */
    .main .block-container {
        padding: 1rem 1rem 3rem 1rem;
        max-width: 100%;
        background: #fafafa;
    }
    
    /* Mobile responsive adjustments */
    @media (min-width: 768px) {
        .main .block-container {
            padding: 2rem 3rem 4rem 3rem;
        }
    }
    
    /* Cards - with dark mode support */
    .card {
        background: white;
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        border: 1px solid #e5e5e5;
        transition: all 0.3s ease;
        color: #000000 !important;
    }
    
    .card:hover {
        border-color: #000000;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    
    /* Dark mode support - force text visibility */
    .card *, .card p, .card span, .card div {
        color: #000000 !important;
    }
    
    .card h1, .card h2, .card h3, .card h4, .card h5, .card h6 {
        color: #000000 !important;
    }
    
    /* Header card */
    .header-card {
        display: flex;
        align-items: center;
        gap: 1.5rem;
        background: white;
        border-radius: 16px;
        padding: 2rem;
        margin-bottom: 3rem;
        border: 1px solid #e5e5e5;
        flex-wrap: wrap;
    }
    
    .header-card * {
        color: #000000 !important;
    }
    
    .logo-box {
        width: 80px;
        height: 80px;
        background: #000000;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 2.5rem;
        flex-shrink: 0;
    }
    
    .app-title {
        font-size: 2.5rem;
        font-weight: 700;
        color: #000000 !important;
        margin: 0;
        letter-spacing: -0.02em;
    }
    
    @media (max-width: 768px) {
        .header-card {
            flex-direction: column;
            text-align: center;
            padding: 1.5rem;
        }
        
        .app-title {
            font-size: 2rem;
        }
        
        .logo-box {
            width: 64px;
            height: 64px;
            font-size: 2rem;
        }
    }
    
    /* Stat cards */
    .stat-card {
        background: white;
        border-radius: 16px;
        padding: 2rem 1.5rem;
        text-align: center;
        border: 1px solid #e5e5e5;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    
    .stat-card:hover {
        transform: translateY(-4px);
        border-color: #000000;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    
    .stat-card * {
        color: #000000 !important;
    }
    
    .stat-value {
        font-size: 3rem;
        font-weight: 700;
        color: #000000 !important;
        letter-spacing: -0.02em;
        margin-bottom: 0.5rem;
    }
    
    .stat-label {
        font-size: 0.95rem;
        color: #737373 !important;
        font-weight: 500;
    }
    
    @media (max-width: 768px) {
        .stat-card {
            padding: 1.5rem 1rem;
        }
        
        .stat-value {
            font-size: 2.25rem;
        }
        
        .stat-label {
            font-size: 0.85rem;
        }
    }
    
    /* Buttons */
    .stButton > button {
        border-radius: 12px;
        font-weight: 600;
        padding: 0.75rem 2rem;
        transition: all 0.3s ease;
        border: 1px solid #e5e5e5;
        background: white;
        color: #000000 !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        border-color: #000000;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    
    .stButton > button[kind="primary"] {
        background: #ffffff !important;
        color: #ffffff !important;
        border: none !important;
    }
    
    .stButton > button[kind="primary"]:hover {
        background: #1a1a1a;
        color: #ffffff;
        box-shadow: 0 8px 20px rgba(0,0,0,0.15);
    }
    
    /* Form inputs - ensure text is visible */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > div,
    .stTextArea textarea {
        border-radius: 10px;
        border: 1px solid #e5e5e5;
        padding: 0.75rem;
        font-size: 1rem;
        background: white !important;
        color: #000000 !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stSelectbox > div > div > div:focus,
    .stTextArea textarea:focus {
        border-color: #000000;
        box-shadow: 0 0 0 2px rgba(0, 0, 0, 0.1);
    }
    
    /* Sliders */
    .stSlider > div > div > div > div {
        background: #000000;
    }
    
    /* Success/Error messages - ensure visibility */
    .stSuccess, .stError, .stWarning, .stInfo {
        border-radius: 12px;
        padding: 1rem;
        margin: 1rem 0;
        background: white !important;
        border: 1px solid #e5e5e5;
    }
    
    .stSuccess *, .stError *, .stWarning *, .stInfo * {
        color: #000000 !important;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: #fafafa;
    }
    
    [data-testid="stSidebar"] * {
        color: #000000 !important;
    }
    
    [data-testid="stSidebar"] .stButton > button {
        width: 100%;
        margin-bottom: 0.5rem;
        background: white;
        color: #000000 !important;
        border: 1px solid #e5e5e5;
    }
    
    [data-testid="stSidebar"] .stButton > button:hover {
        border-color: #000000;
        background: white;
    }
    
    /* Team cards - dark mode safe */
    .team-card {
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        background: white;
        border: 2px solid #000000;
        color: #000000 !important;
    }
    
    .team-card * {
        color: #000000 !important;
    }
    
    .team-card h3 {
        font-size: 1.5rem;
        font-weight: 700;
        margin-bottom: 1rem;
    }
    
    .player-item {
        background: #fafafa;
        padding: 0.75rem;
        border-radius: 10px;
        margin-bottom: 0.5rem;
        border: 1px solid #e5e5e5;
    }
    
    .player-item * {
        color: #000000 !important;
    }
    
    .player-name {
        font-weight: 600;
        font-size: 1rem;
    }
    
    .player-stats {
        font-size: 0.85rem;
        color: #525252 !important;
        margin-top: 0.25rem;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px 10px 0 0;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        background: white;
        border: 1px solid #e5e5e5;
        color: #000000 !important;
    }
    
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: #000000;
        color: white !important;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        font-weight: 600;
        font-size: 1.05rem;
        background: white;
        border: 1px solid #e5e5e5;
        border-radius: 10px;
        padding: 0.75rem 1rem;
        color: #000000 !important;
    }
    
    .streamlit-expanderHeader * {
        color: #000000 !important;
    }
    
    /* History cards */
    .history-card {
        background: white;
        border: 1px solid #e5e5e5;
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }
    
    .history-card:hover {
        border-color: #000000;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    
    .history-card * {
        color: #000000 !important;
    }
    
    .game-date {
        font-size: 0.9rem;
        color: #737373 !important;
        font-weight: 500;
    }
    
    .game-title {
        font-size: 1.2rem;
        font-weight: 700;
        color: #000000 !important;
        margin: 0.5rem 0;
    }
    
    /* Checkbox labels - ensure visibility */
    .stCheckbox label {
        color: #000000 !important;
    }
    
    /* All text elements - force black in light areas */
    p, span, div, label {
        color: #000000 !important;
    }
    
    /* Markdown text */
    .stMarkdown {
        color: #000000 !important;
    }
</style>
""", unsafe_allow_html=True)

# Database functions
def load_players():
    """Load players from Supabase or local JSON"""
    if USE_SUPABASE and st.session_state.get('supabase_connected', False):
        try:
            response = supabase.table('players').select('*').execute()
            # Convert UUID to string for consistency
            players = response.data
            for player in players:
                if 'id' in player:
                    player['id'] = str(player['id'])
            return players
        except Exception as e:
            st.error(f"Error loading players from Supabase: {e}")
            return []
    
    # Fallback to local
    if os.path.exists(LOCAL_PLAYERS_FILE):
        with open(LOCAL_PLAYERS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_players(players):
    """Save players to Supabase or local JSON"""
    if USE_SUPABASE and st.session_state.get('supabase_connected', False):
        try:
            # For each player, either insert or update
            for player in players:
                player_data = {
                    'name': player['name'],
                    'position': player.get('position', 'Midfielder'),
                    'running_ability': player.get('running_ability', 5),
                    'goal_scoring': player.get('goal_scoring', 5),
                    'age': player.get('age', 25),
                    'height': player.get('height', 175),
                    'overall_skill': player.get('overall_skill', 5)
                }
                
                if 'id' in player and player['id']:
                    # Update existing player
                    supabase.table('players').update(player_data).eq('id', player['id']).execute()
                else:
                    # Insert new player and get the ID back
                    result = supabase.table('players').insert(player_data).execute()
                    if result.data:
                        player['id'] = str(result.data[0]['id'])
            return
        except Exception as e:
            st.error(f"Error saving players to Supabase: {e}")
            # Fall through to local save
    
    # Fallback to local
    with open(LOCAL_PLAYERS_FILE, 'w') as f:
        json.dump(players, f, indent=2)

def load_games():
    """Load game history from Supabase or local JSON"""
    if USE_SUPABASE and st.session_state.get('supabase_connected', False):
        try:
            response = supabase.table('games').select('*').order('created_at', desc=True).execute()
            # Convert to format expected by the app and handle UUIDs
            games = []
            for game in response.data:
                games.append({
                    'id': str(game['id']),
                    'created_at': game['created_at'],
                    'num_teams': game['num_teams'],
                    'num_players': game['total_players'],  # Map total_players to num_players
                    'teams': game['teams']
                })
            return games
        except Exception as e:
            st.error(f"Error loading games from Supabase: {e}")
            return []
    
    # Fallback to local
    if os.path.exists(LOCAL_GAMES_FILE):
        with open(LOCAL_GAMES_FILE, 'r') as f:
            return json.load(f)
    return []

def save_game(game_data):
    """Save a game to history"""
    if USE_SUPABASE and st.session_state.get('supabase_connected', False):
        try:
            # Format data to match Supabase schema
            supabase_game = {
                'name': game_data.get('name', f"Game {datetime.now().strftime('%Y-%m-%d %H:%M')}"),
                'num_teams': game_data['num_teams'],
                'total_players': game_data['num_players'],
                'teams': game_data['teams']
            }
            supabase.table('games').insert(supabase_game).execute()
            return
        except Exception as e:
            st.error(f"Error saving game to Supabase: {e}")
            # Fall through to local save
    
    # Fallback to local
    games = load_games()
    games.insert(0, game_data)
    with open(LOCAL_GAMES_FILE, 'w') as f:
        json.dump(games, f, indent=2)

def delete_player(player_id):
    """Delete a player from Supabase or local JSON"""
    if USE_SUPABASE and st.session_state.get('supabase_connected', False):
        try:
            supabase.table('players').delete().eq('id', player_id).execute()
            return True
        except Exception as e:
            st.error(f"Error deleting player from Supabase: {e}")
            return False
    return True  # For local, handled by save_players

# Team generation algorithm
def generate_balanced_teams(players, num_teams):
    """Generate balanced teams using optimization"""
    n_players = len(players)
    
    if n_players < num_teams:
        return None
    
    # Create optimization problem
    prob = LpProblem("Team_Balance", LpMinimize)
    
    # Decision variables: player i assigned to team j
    x = {}
    for i in range(n_players):
        for j in range(num_teams):
            x[i, j] = LpVariable(f"x_{i}_{j}", cat='Binary')
    
    # Each player assigned to exactly one team
    for i in range(n_players):
        prob += lpSum(x[i, j] for j in range(num_teams)) == 1
    
    # Team size constraints (as equal as possible)
    min_size = n_players // num_teams
    max_size = min_size + (1 if n_players % num_teams > 0 else 0)
    
    for j in range(num_teams):
        prob += lpSum(x[i, j] for i in range(n_players)) >= min_size
        prob += lpSum(x[i, j] for i in range(n_players)) <= max_size
    
    # Objective: minimize variance in total skill across teams
    team_skills = []
    for j in range(num_teams):
        team_skill = lpSum(
            x[i, j] * (
                players[i].get('running_ability', 5) +
                players[i].get('goal_scoring', 5) +
                players[i].get('overall_skill', 5)
            ) / 3.0
            for i in range(n_players)
        )
        team_skills.append(team_skill)
    
    # Minimize maximum deviation from average
    avg_skill = sum(
        (p.get('running_ability', 5) + p.get('goal_scoring', 5) + p.get('overall_skill', 5)) / 3.0
        for p in players
    ) / num_teams
    
    deviation = LpVariable("max_deviation")
    for team_skill in team_skills:
        prob += deviation >= team_skill - avg_skill * min_size
        prob += deviation >= avg_skill * min_size - team_skill
    
    prob += deviation
    
    # Solve
    prob.solve(PULP_CBC_CMD(msg=0))
    
    if prob.status != 1:
        # Fallback to random assignment
        teams = [[] for _ in range(num_teams)]
        shuffled = players.copy()
        random.shuffle(shuffled)
        for i, player in enumerate(shuffled):
            teams[i % num_teams].append(player)
        return teams
    
    # Extract solution
    teams = [[] for _ in range(num_teams)]
    for i in range(n_players):
        for j in range(num_teams):
            if x[i, j].varValue > 0.5:
                teams[j].append(players[i])
    
    return teams

# Initialize session state
if 'page' not in st.session_state:
    st.session_state.page = 'home'
if 'generated_teams' not in st.session_state:
    st.session_state.generated_teams = None
if 'last_generation_timestamp' not in st.session_state:
    st.session_state.last_generation_timestamp = None

# Sidebar navigation
with st.sidebar:
    st.markdown("### ⚽ Navigation")
    
    if st.button("🏠 Home", use_container_width=True):
        st.session_state.page = 'home'
        st.rerun()
    
    if st.button("👥 Manage Players", use_container_width=True):
        st.session_state.page = 'players'
        st.rerun()
    
    if st.button("🎯 Create Teams", use_container_width=True):
        st.session_state.page = 'game'
        st.rerun()
    
    if st.button("📊 Game History", use_container_width=True):
        st.session_state.page = 'history'
        st.rerun()
    
    st.markdown("---")
    
    # Connection status with details
    if USE_SUPABASE and st.session_state.get('supabase_connected', False):
        st.success("☁️ Cloud Connected")
        # Debug info
        players = load_players()
        games = load_games()
        st.caption(f"📊 {len(players)} players, {len(games)} games")
    else:
        st.info("💾 Using Local Storage")
        if USE_SUPABASE:
            st.caption("⚠️ Supabase configured but not connected")
    
    st.markdown("---")
    st.markdown("**Team Balance Pro**")
    st.markdown("v2.0")

# Page routing
if st.session_state.page == 'home':
    # Header with Logo and Title
    st.markdown("""
    <div class="header-card">
        <div class="logo-box">⚽</div>
        <h1 class="app-title">Team Balancer Pro</h1>
    </div>
    """, unsafe_allow_html=True)
    
    # Debug section (shows if not connected)
    if not (USE_SUPABASE and st.session_state.get('supabase_connected', False)):
        with st.expander("🔍 Connection Debug Info", expanded=False):
            st.warning("⚠️ Not connected to Supabase - using local storage")
            
            st.write("**Configuration Check:**")
            has_url = bool(SUPABASE_URL)
            has_key = bool(SUPABASE_KEY)
            
            col1, col2 = st.columns(2)
            with col1:
                if has_url:
                    st.success(f"✅ URL found: {SUPABASE_URL[:30]}...")
                else:
                    st.error("❌ URL missing")
            
            with col2:
                if has_key:
                    st.success(f"✅ Key found: {SUPABASE_KEY[:20]}...")
                else:
                    st.error("❌ Key missing")
            
            if has_url and has_key:
                st.info("Both credentials found but connection failed. Checking...")
                
                if st.button("🔄 Test Connection Now"):
                    try:
                        from supabase import create_client
                        test_client = create_client(SUPABASE_URL, SUPABASE_KEY)
                        result = test_client.table('players').select('*').limit(1).execute()
                        st.success(f"✅ Connection works! Found {len(result.data)} players")
                        st.info("Connection is working. Click 'Reboot app' in Streamlit settings to reconnect.")
                    except Exception as e:
                        st.error(f"❌ Connection failed: {str(e)}")
                        st.write("**Common fixes:**")
                        st.write("- Make sure tables are created in Supabase")
                        st.write("- Check RLS policies allow access")
                        st.write("- Verify you're using the anon public key")
            else:
                st.write("**To fix:**")
                st.write("1. Go to Streamlit Cloud → Settings → Secrets")
                st.write("2. Add your credentials (see guides)")
                st.write("3. Click Save")
                st.write("4. App will restart automatically")
    
    # Stats Grid
    players = load_players()
    games = load_games()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{len(players)}</div>
            <div class="stat-label">Total Players</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{len(games)}</div>
            <div class="stat-label">Games Played</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        avg_skill = sum(p.get('overall_skill', 5) for p in players) / len(players) if players else 0
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{avg_skill:.1f}</div>
            <div class="stat-label">Avg Skill</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        positions_count = {}
        for p in players:
            pos = p.get('position', 'Midfielder')
            positions_count[pos] = positions_count.get(pos, 0) + 1
        most_common = max(positions_count, key=positions_count.get)[:3] if positions_count else "N/A"
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{most_common}</div>
            <div class="stat-label">Top Position</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)
    
    # CTA Button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🎯 Create New Game", use_container_width=True, type="primary"):
            st.session_state.page = 'game'
            st.rerun()
    
    # Version
    st.markdown("<div style='text-align: center; margin-top: 2rem; color: #a3a3a3; font-size: 0.9rem;'>v2.0</div>", unsafe_allow_html=True)

elif st.session_state.page == 'players':
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<h1>👥 Player Management</h1>', unsafe_allow_html=True)
    st.markdown('<p style="font-size: 1.1rem; color: #718096;">Manage your permanent player roster</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    players = load_players()
    
    tab1, tab2, tab3 = st.tabs(["➕ Add Player", "✏️ Edit Players", "📥 Import/Export"])
    
    with tab1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Add New Player")
        
        with st.form("add_player_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Player Name*", key="new_player_name")
                position = st.selectbox("Position*", POSITIONS, key="new_player_position")
                running = st.slider("Running Ability", 1, 10, 5, key="new_player_running")
                goals = st.slider("Goal Scoring", 1, 10, 5, key="new_player_goals")
            
            with col2:
                age = st.number_input("Age", 10, 100, 25, key="new_player_age")
                height = st.number_input("Height (cm)", 140, 220, 175, key="new_player_height")
                skill = st.slider("Overall Skill", 1, 10, 5, key="new_player_skill")
            
            submitted = st.form_submit_button("✅ Add Player", use_container_width=True, type="primary")
            
            if submitted:
                if not name or not name.strip():
                    st.error("❌ Player name is required!")
                elif any(p['name'].lower() == name.strip().lower() for p in players):
                    st.error(f"❌ Player '{name}' already exists!")
                else:
                    new_player = {
                        'name': name.strip().title(),
                        'position': position,
                        'running_ability': running,
                        'goal_scoring': goals,
                        'age': age,
                        'height': height,
                        'overall_skill': skill,
                        'created_at': datetime.now().isoformat()
                    }
                    players.append(new_player)
                    save_players(players)
                    st.success(f"✅ Successfully added {name}!")
                    st.balloons()
                    st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        
        if not players:
            st.info("📭 No players yet. Add some players to get started!")
        else:
            st.subheader(f"All Players ({len(players)})")
            
            for idx, player in enumerate(players):
                with st.expander(f"⚽ {player['name']} - {player.get('position', 'N/A')}", expanded=False):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        # Edit form
                        with st.form(f"edit_player_{idx}"):
                            c1, c2 = st.columns(2)
                            
                            with c1:
                                new_running = st.slider("Running", 1, 10, player.get('running_ability', 5), key=f"edit_run_{idx}")
                                new_goals = st.slider("Goals", 1, 10, player.get('goal_scoring', 5), key=f"edit_goal_{idx}")
                            
                            with c2:
                                new_age = st.number_input("Age", 10, 100, player.get('age', 25), key=f"edit_age_{idx}")
                                new_skill = st.slider("Skill", 1, 10, player.get('overall_skill', 5), key=f"edit_skill_{idx}")
                            
                            col_update, col_delete = st.columns(2)
                            
                            with col_update:
                                if st.form_submit_button("💾 Update Stats", use_container_width=True):
                                    players[idx].update({
                                        'running_ability': new_running,
                                        'goal_scoring': new_goals,
                                        'age': new_age,
                                        'overall_skill': new_skill,
                                        'updated_at': datetime.now().isoformat()
                                    })
                                    save_players(players)
                                    st.success(f"✅ Updated {player['name']}!")
                                    st.rerun()
                    
                    with col2:
                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.button(f"🗑️ Delete", key=f"delete_{idx}", use_container_width=True):
                            player_id = player.get('id')
                            player_name = player['name']
                            
                            # Delete from Supabase if connected
                            if player_id and delete_player(player_id):
                                # Also remove from local list
                                players.pop(idx)
                                if not USE_SUPABASE:
                                    save_players(players)  # Save locally if not using Supabase
                                st.success(f"Deleted {player_name}")
                                st.rerun()
                            elif not player_id:
                                # No ID means local only
                                players.pop(idx)
                                save_players(players)
                                st.success(f"Deleted {player_name}")
                                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab3:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        
        # Export
        st.subheader("📤 Export Players")
        if players:
            df = pd.DataFrame(players)
            csv = df.to_csv(index=False)
            st.download_button(
                label="⬇️ Download CSV",
                data=csv,
                file_name=f"players_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.info("No players to export")
        
        st.markdown("---")
        
        # Import
        st.subheader("📥 Import Players")
        uploaded_file = st.file_uploader("Upload CSV file", type=['csv'])
        
        if uploaded_file:
            try:
                df = pd.read_csv(uploaded_file)
                
                st.write("Preview:")
                st.dataframe(df.head())
                
                if st.button("✅ Import Players", type="primary", use_container_width=True):
                    imported = 0
                    skipped = 0
                    
                    for _, row in df.iterrows():
                        name = str(row.get('name', '')).strip().title()
                        if not name or any(p['name'].lower() == name.lower() for p in players):
                            skipped += 1
                            continue
                        
                        players.append({
                            'name': name,
                            'position': row.get('position', 'Midfielder'),
                            'running_ability': max(1, min(10, int(row.get('running_ability', 5)))),
                            'goal_scoring': max(1, min(10, int(row.get('goal_scoring', 5)))),
                            'age': max(10, min(100, int(row.get('age', 25)))),
                            'height': max(140, min(220, int(row.get('height', 175)))),
                            'overall_skill': max(1, min(10, int(row.get('overall_skill', 5)))),
                            'created_at': datetime.now().isoformat()
                        })
                        imported += 1
                    
                    save_players(players)
                    st.success(f"✅ Imported {imported} players! (Skipped {skipped} duplicates)")
                    st.balloons()
                    st.rerun()
                    
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
        
        st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.page == 'game':
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<h1>🎯 Create Balanced Teams</h1>', unsafe_allow_html=True)
    st.markdown('<p style="font-size: 1.1rem; color: #718096;">Select players and generate perfectly balanced teams</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    players = load_players()
    
    if not players:
        st.warning("📭 No players available. Please add players first!")
        if st.button("➕ Go to Player Management"):
            st.session_state.page = 'players'
            st.rerun()
    else:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        
        # Player selection
        st.subheader("1️⃣ Select Players for This Game")
        
        col1, col2 = st.columns([4, 1])
        with col1:
            if 'selected_players' not in st.session_state:
                st.session_state.selected_players = set()
        
        with col2:
            if st.button("Select All", use_container_width=True):
                st.session_state.selected_players = set(range(len(players)))
                st.rerun()
            if st.button("Clear All", use_container_width=True):
                st.session_state.selected_players = set()
                st.rerun()
        
        # Display players in a grid
        cols_per_row = 3
        for i in range(0, len(players), cols_per_row):
            cols = st.columns(cols_per_row)
            for j, col in enumerate(cols):
                if i + j < len(players):
                    idx = i + j
                    player = players[idx]
                    with col:
                        is_selected = idx in st.session_state.selected_players
                        if st.checkbox(
                            f"⚽ **{player['name']}** ({player.get('position', 'N/A')})\n"
                            f"Skill: {player.get('overall_skill', 5)}/10",
                            value=is_selected,
                            key=f"player_select_{idx}"
                        ):
                            st.session_state.selected_players.add(idx)
                        else:
                            st.session_state.selected_players.discard(idx)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Team generation
        selected_count = len(st.session_state.selected_players)
        
        if selected_count > 0:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("2️⃣ Set Number of Teams")
            
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                st.info(f"✅ {selected_count} players selected")
            
            with col2:
                max_teams = min(10, selected_count)
                num_teams = st.number_input(
                    "Number of teams",
                    min_value=2,
                    max_value=max_teams,
                    value=min(3, max_teams),
                    step=1
                )
            
            with col3:
                st.info(f"~{selected_count // num_teams} per team")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("⚡ Generate Teams", type="primary", use_container_width=True):
                    selected_players_list = [players[i] for i in sorted(st.session_state.selected_players)]
                    
                    with st.spinner("🔄 Generating balanced teams..."):
                        teams = generate_balanced_teams(selected_players_list, num_teams)
                        
                        if teams:
                            st.session_state.generated_teams = teams
                            st.session_state.last_generation_timestamp = datetime.now()
                            st.success("✅ Teams generated successfully!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to generate teams. Try different settings.")
            
            with col2:
                if st.session_state.generated_teams:
                    if st.button("🔄 Regenerate Different Teams", use_container_width=True):
                        selected_players_list = [players[i] for i in sorted(st.session_state.selected_players)]
                        
                        with st.spinner("🔄 Regenerating..."):
                            # Force new random seed
                            random.seed(datetime.now().timestamp())
                            teams = generate_balanced_teams(selected_players_list, num_teams)
                            
                            if teams:
                                st.session_state.generated_teams = teams
                                st.session_state.last_generation_timestamp = datetime.now()
                                st.success("✅ New teams generated!")
                                st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Display generated teams
        if st.session_state.generated_teams:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("3️⃣ Your Balanced Teams")
            
            teams = st.session_state.generated_teams
            
            for idx, team in enumerate(teams):
                team_num = idx + 1
                
                # Calculate team stats
                avg_skill = sum(p.get('overall_skill', 5) for p in team) / len(team)
                avg_running = sum(p.get('running_ability', 5) for p in team) / len(team)
                avg_goals = sum(p.get('goal_scoring', 5) for p in team) / len(team)
                
                st.markdown(f"""
                <div class="team-card">
                    <h3>Team {team_num} ({len(team)} players)</h3>
                    <div style="display: flex; gap: 1rem; margin-bottom: 1rem; flex-wrap: wrap; color: #000000;">
                        <span>⭐ Avg Skill: {avg_skill:.1f}</span>
                        <span>🏃 Running: {avg_running:.1f}</span>
                        <span>⚽ Goals: {avg_goals:.1f}</span>
                    </div>
                """, unsafe_allow_html=True)
                
                for player in team:
                    st.markdown(f"""
                    <div class="player-item">
                        <div class="player-name">{player['name']}</div>
                        <div class="player-stats">
                            {player.get('position', 'N/A')} | 
                            Skill: {player.get('overall_skill', 5)}/10 | 
                            Run: {player.get('running_ability', 5)}/10 | 
                            Goals: {player.get('goal_scoring', 5)}/10
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Copyable text format
            st.markdown("---")
            st.subheader("📋 Copy Teams")
            
            teams_text = ""
            for idx, team in enumerate(teams):
                team_num = idx + 1
                teams_text += f"TEAM {team_num}\n"
                teams_text += "=" * 40 + "\n"
                for player in team:
                    teams_text += f"⚽ {player['name']}\n"
                teams_text += "\n"
            
            st.text_area(
                "Copy and share your teams:",
                value=teams_text,
                height=300,
                key="teams_copy_text"
            )
            
            
            # Save game button
            if st.button("💾 Save This Game to History", type="primary", use_container_width=True):
                game_data = {
                    'created_at': datetime.now().isoformat(),
                    'num_teams': len(teams),
                    'num_players': sum(len(team) for team in teams),
                    'teams': [
                        {
                            'team_number': i + 1,
                            'players': [p['name'] for p in team],
                            'avg_skill': sum(p.get('overall_skill', 5) for p in team) / len(team)
                        }
                        for i, team in enumerate(teams)
                    ]
                }
                save_game(game_data)
                st.success("✅ Game saved to history!")
                st.balloons()
            
            st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.page == 'history':
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<h1>📊 Game History</h1>', unsafe_allow_html=True)
    st.markdown('<p style="font-size: 1.1rem; color: #718096;">Review all your past games and team compositions</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    games = load_games()
    
    if not games:
        st.info("📭 No games played yet. Create your first game to see history here!")
        if st.button("🎯 Create New Game", type="primary"):
            st.session_state.page = 'game'
            st.rerun()
    else:
        st.markdown(f"**Total Games: {len(games)}**")
        
        for idx, game in enumerate(games):
            game_date = datetime.fromisoformat(game['created_at']).strftime("%B %d, %Y at %I:%M %p")
            
            st.markdown(f"""
            <div class="history-card">
                <div class="game-date">🗓️ {game_date}</div>
                <div class="game-title">Game #{len(games) - idx}</div>
                <p style="color: #718096; margin: 0.5rem 0;">
                    {game['num_teams']} teams • {game['num_players']} players
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander("View Team Details"):
                for idx, team in enumerate(game['teams']):
                    # Handle both old and new data formats
                    team_num = team.get('team_number', idx + 1)
                    avg_skill = team.get('avg_skill', 0)
                    players_list = team.get('players', [])
                    
                    st.markdown(f"### Team {team_num}")
                    if avg_skill > 0:
                        st.markdown(f"**Average Skill:** {avg_skill:.1f}/10")
                    st.markdown("**Players:**")
                    for player_name in players_list:
                        st.markdown(f"- ⚽ {player_name}")
                    st.markdown("---")
