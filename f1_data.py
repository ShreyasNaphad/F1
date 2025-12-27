import pandas as pd
import os


def load_and_merge_data():
    """
    Loads raw Kaggle CSVs from the 'data/' folder and creates a Master DataFrame.
    """
    # 1. Define the Data Directory
    # We look for a folder named 'data' in the same directory as this script
    base_dir = os.getcwd()
    data_dir = os.path.join(base_dir, "data")

    files = {
        "results": "results.csv",
        "drivers": "drivers.csv",
        "races": "races.csv",
        "constructors": "constructors.csv"
    }

    # 2. Check if files exist and load them
    dataframes = {}

    print(f"📂 Scanning directory: {data_dir}")

    if not os.path.exists(data_dir):
        print(f"❌ ERROR: The folder '{data_dir}' does not exist.")
        return None

    for name, filename in files.items():
        # Construct path: current_folder/data/filename.csv
        path = os.path.join(data_dir, filename)

        if not os.path.exists(path):
            print(f"⚠️ CRITICAL ERROR: Could not find '{filename}' inside 'data' folder.")
            return None

        try:
            dataframes[name] = pd.read_csv(path)
            # print(f"✅ Loaded {filename}") # Uncomment to debug
        except Exception as e:
            print(f"❌ Error reading {filename}: {e}")
            return None

    # Unpack
    df_results = dataframes["results"]
    df_drivers = dataframes["drivers"]
    df_races = dataframes["races"]
    df_constructors = dataframes["constructors"]

    # 3. MERGE LOGIC (Connect the dots)
    # Results + Drivers
    merged = pd.merge(df_results, df_drivers[['driverId', 'forename', 'surname', 'code', 'nationality']], on='driverId',
                      how='left')

    # + Races
    merged = pd.merge(merged, df_races[['raceId', 'year', 'name', 'date']], on='raceId', how='left')
    merged.rename(columns={'name': 'race_name'}, inplace=True)

    # + Constructors
    merged = pd.merge(merged, df_constructors[['constructorId', 'name']], on='constructorId', how='left')
    merged.rename(columns={'name': 'team_name'}, inplace=True)

    # 4. CLEANUP
    merged['full_name'] = merged['forename'] + ' ' + merged['surname']

    final_df = merged[[
        'year', 'race_name', 'date',
        'full_name', 'surname', 'code', 'nationality',
        'team_name',
        'grid', 'positionOrder', 'points', 'laps', 'statusId'
    ]]

    final_df['positionOrder'] = pd.to_numeric(final_df['positionOrder'], errors='coerce')

    print(f"🎉 SUCCESS: Loaded {len(final_df)} rows from 'data/' folder.")
    return final_df


if __name__ == "__main__":
    load_and_merge_data()