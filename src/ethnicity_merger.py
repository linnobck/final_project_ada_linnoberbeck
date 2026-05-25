import pandas as pd
import glob
 
INPUT_FILE = "parsed_cast_data_v2.csv"
OUTPUT_FILE = "parsed_data_with_ethnicity_v2.csv"
 
all_batch_files = sorted(glob.glob("actors_ethnicity_*.csv"))
print(f"Found {len(all_batch_files)} batch files: {all_batch_files}")
 
combined = pd.concat([pd.read_csv(f) for f in all_batch_files])
combined = combined.drop_duplicates(subset=["actor_tmdb_id"])
print(f"Combined {len(combined)} unique actors")
 
df = pd.read_csv(INPUT_FILE, dtype=str)
df = df.drop(columns=["actor_ethnicity"], errors="ignore")
df["actor_tmdb_id"] = df["actor_tmdb_id"].astype(str)
combined["actor_tmdb_id"] = combined["actor_tmdb_id"].astype(str)
df = df.merge(
    combined[["actor_tmdb_id", "actor_ethnicity", "confidence"]],
    on="actor_tmdb_id",
    how="left"
)
 
df.to_csv(OUTPUT_FILE, index=False)
print(f"Saved to {OUTPUT_FILE}")
print(f"Ethnicity filled: {df['actor_ethnicity'].notna().sum()} of {len(df)} rows")