import pandas as pd
import numpy as np

try:
    from sklearn.preprocessing import MinMaxScaler
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError:
    # Fallback if sklearn is not installed
    MinMaxScaler = None
    cosine_similarity = None


def get_similar_drivers(target_driver, driver_data):
    """
    Vectorizes driver stats and uses Cosine Similarity to find the Top 3 matches.
    """
    if cosine_similarity is None:
        return []

    # 1. Convert JSON list to DataFrame
    df = pd.DataFrame(driver_data)

    # Check if target exists
    if target_driver not in df['surname'].values:
        return []

    # 2. Feature Engineering (The "DNA" Strategy)
    # We invert 'avg_finish' & 'std' so Higher Numbers = Better Performance
    # This helps Cosine Similarity align "Good" drivers with "Good" drivers.

    # Logic: 22 - Finish Position (1st place becomes 21, 20th place becomes 2)
    df['score_pace'] = 22 - df['avg_finish']

    # Logic: 15 - Std Dev (Low deviation becomes high consistency score)
    df['score_consistency'] = 15 - df['finish_std']

    # Logic: Invert delta (Negative delta means beating team, so we negate it)
    df['score_skill'] = df['delta_vs_team'] * -1

    # Logic: Races (Experience) - needs no inversion, just scaling later
    df['score_exp'] = df['races']

    # 3. Select Features
    features = ['score_pace', 'score_consistency', 'score_skill', 'score_exp']

    # Fill NaNs if any (Mid-season drivers might have missing data)
    df[features] = df[features].fillna(df[features].mean())

    # 4. Normalize (Scale everything between 0 and 1)
    # This ensures "Races" (e.g., 300) doesn't overpower "Skill" (e.g., 0.5)
    scaler = MinMaxScaler()
    vectors = scaler.fit_transform(df[features])

    # 5. Compute Cosine Similarity
    target_idx = df[df['surname'] == target_driver].index[0]

    # Compare Target Vector vs All Vectors
    # Returns an array of scores (0.0 to 1.0)
    sim_scores = cosine_similarity([vectors[target_idx]], vectors)[0]

    # 6. Rank Results
    # Pair scores with index: [(0, 0.2), (1, 0.9)...]
    scores_with_indices = list(enumerate(sim_scores))

    # Sort descending
    scores_with_indices = sorted(scores_with_indices, key=lambda x: x[1], reverse=True)

    # 7. Extract Top 3 (excluding self)
    top_matches = []
    for idx, score in scores_with_indices:
        if idx == target_idx: continue  # Skip the driver themselves

        match_driver = df.iloc[idx].to_dict()
        match_driver['similarity_score'] = score
        top_matches.append(match_driver)

        if len(top_matches) >= 3:
            break

    return top_matches