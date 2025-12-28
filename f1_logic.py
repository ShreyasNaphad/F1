import pandas as pd
import numpy as np
import os


# --- 1. DATA LOADING & CONFIG ---
def load_data_dict():
    """Loads CSVs from data/ folder."""
    base_dir = os.getcwd()
    data_dir = os.path.join(base_dir, "data")
    files = ["results.csv", "races.csv", "drivers.csv", "constructors.csv"]
    dfs = {}

    if not os.path.exists(data_dir): return None

    for f in files:
        path = os.path.join(data_dir, f)
        if os.path.exists(path):
            dfs[f.split(".")[0]] = pd.read_csv(path)
    return dfs


STATUS_MAP = {
    1: "Finished", 2: "Disqualified", 3: "Accident", 4: "Collision", 5: "Engine",
    6: "Gearbox", 7: "Transmission", 8: "Clutch", 9: "Hydraulics", 10: "Electrical",
    11: "+1 Lap", 12: "+2 Laps", 13: "+3 Laps", 20: "Spun off", 22: "Suspension",
    31: "Retired", 104: "Fatal accident"
}

# --- 2. VECTOR ENGINE (DOPPELGÄNGER) ---
try:
    from sklearn.preprocessing import MinMaxScaler
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError:
    MinMaxScaler = None
    cosine_similarity = None


def get_similar_drivers(target_driver, driver_data):
    if cosine_similarity is None: return []
    df = pd.DataFrame(driver_data)
    if target_driver not in df['surname'].values: return []

    df['score_pace'] = 22 - df['avg_finish']
    df['score_consistency'] = 15 - df['finish_std']
    df['score_skill'] = df['delta_vs_team'] * -1
    df['score_exp'] = df['races']

    features = ['score_pace', 'score_consistency', 'score_skill', 'score_exp']
    df[features] = df[features].fillna(df[features].mean())

    scaler = MinMaxScaler()
    vectors = scaler.fit_transform(df[features])

    target_idx = df[df['surname'] == target_driver].index[0]
    sim_scores = cosine_similarity([vectors[target_idx]], vectors)[0]

    scores_with_indices = sorted(list(enumerate(sim_scores)), key=lambda x: x[1], reverse=True)

    top_matches = []
    for idx, score in scores_with_indices:
        if idx == target_idx: continue
        match_driver = df.iloc[idx].to_dict()
        match_driver['similarity_score'] = score
        top_matches.append(match_driver)
        if len(top_matches) >= 3: break

    return top_matches


# --- 3. ARCHIVE ENGINE (FIXED) ---
def get_years():
    dfs = load_data_dict()
    if not dfs: return []
    return sorted(dfs['races']['year'].unique(), reverse=True)


def get_races_for_year(year):
    dfs = load_data_dict()
    if not dfs: return pd.DataFrame()
    return dfs['races'][dfs['races']['year'] == year].sort_values('round')


def get_drivers_in_race(race_id):
    """
    Returns FULL NAMES (Forename + Surname) to avoid duplicates like Verstappen/Schumacher.
    """
    dfs = load_data_dict()
    if not dfs: return []

    res = dfs['results'][dfs['results']['raceId'] == race_id]
    merged = pd.merge(res, dfs['drivers'], on='driverId')

    # Create Full Name column
    merged['full_name'] = merged['forename'] + " " + merged['surname']
    return sorted(merged['full_name'].unique())


def get_race_story_stats(race_id, driver_fullname):
    """
    Look up by FULL NAME to prevent 'IndexError' on ambiguous surnames.
    """
    dfs = load_data_dict()
    if not dfs: return None

    try:
        # 1. Split name safely
        # We search specifically in the results of THIS race to find the correct ID
        race_results = dfs['results'][dfs['results']['raceId'] == race_id]
        merged = pd.merge(race_results, dfs['drivers'], on='driverId')
        merged['full_name'] = merged['forename'] + " " + merged['surname']

        # 2. Filter for the specific driver
        target_row = merged[merged['full_name'] == driver_fullname]

        if target_row.empty:
            return None  # Driver didn't race here

        res = target_row.iloc[0]

        # 3. Get Constructor Name
        cons = dfs['constructors'][dfs['constructors']['constructorId'] == res['constructorId']].iloc[0]

        # 4. Logic
        status_text = STATUS_MAP.get(res['statusId'], "Technical Issue")
        grid = int(res['grid'])
        pos = int(res['positionOrder'])
        calc_grid = 20 if grid == 0 else grid
        delta = calc_grid - pos

        return {
            "year": int(dfs['races'][dfs['races']['raceId'] == race_id].iloc[0]['year']),
            "gp_name": dfs['races'][dfs['races']['raceId'] == race_id].iloc[0]['name'],
            "date": dfs['races'][dfs['races']['raceId'] == race_id].iloc[0]['date'],
            "driver": driver_fullname,
            "team": cons['name'],
            "grid": grid,
            "finish": pos,
            "status": status_text,
            "delta": delta
        }
    except Exception as e:
        print(f"Error getting stats: {e}")
        return None