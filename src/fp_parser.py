import pandas as pd
import re

df = pd.read_csv("/Users/linnoberbeck/Documents/UChicagoMasters/ADA/final_project_ada/src/raw_cast_data_v2.csv", dtype=str)

print(f"Loaded {len(df)} rows across {df['title'].nunique()} titles")


# Replace empty strings with NaN
df.replace("", pd.NA, inplace=True)


# Strip leading/trailing whitespace from all string columns
str_cols = ["title", "actor_name", "character_name", "genres", "media_type", "role_type"]
for col in str_cols:
    df[col] = df[col].str.strip()

# Normalize title whitespace
df["title"] = df["title"].str.replace(r"\s+", " ", regex=True)


# To numeric
df["billing_order"] = pd.to_numeric(df["billing_order"], errors="coerce")
df["actor_gender_code"] = pd.to_numeric(df["actor_gender_code"], errors="coerce")
df["start_year"] = pd.to_numeric(df["start_year"], errors="coerce").astype("Int64")
df["end_year"] = pd.to_numeric(df["end_year"], errors="coerce").astype("Int64")


# Code to gender
gender_map = {2: "male", 1: "female", 0: "unspecified"}
df["actor_gender"] = df["actor_gender_code"].map(gender_map).fillna("unspecified")


# Score 
df["prominence_score_raw"] = 1 / df["billing_order"]

# Normalize per title so scores are comparable across titles with different cast sizes
df["prominence_score"] = df.groupby("title")["prominence_score_raw"].transform(
    lambda x: x / x.sum()
).round(4)

df.drop(columns=["prominence_score_raw"], inplace=True)


# Flag characters like "Cop", "Mover", "Pedestrian (uncredited)"
generic_patterns = [
    r"\(uncredited\)",
    r"^(?:cop|guard|man|woman|soldier|pedestrian|worker|officer|extra|background)$",
]
combined_pattern = "|".join(generic_patterns)

df["is_named_character"] = ~df["character_name"].str.lower().str.contains(
    combined_pattern, flags=re.IGNORECASE, na=False
)


# Production time (always 1 for movies)
df["production_span"] = (df["end_year"] - df["start_year"] + 1).clip(lower=1)



column_order = [
    # Title-level
    "title", "start_year", "end_year", "production_span", "genres", "tmdb_id", "media_type",

    # Actor-level
    "actor_name", "actor_tmdb_id", "actor_gender_code", "actor_gender",
    "actor_ethnicity",        # OpenAI annotation
    "actor_age_at_release",   # manual

    # Character-level
    "character_name", "is_named_character",
    "character_gender",       # manual
    "character_ethnicity",    # manual

    # Mismatch flags
    "gender_mismatch",
    "ethnicity_mismatch",

    # Role data
    "billing_order", "role_type", "prominence_score",

    # Qualitative (Week 7)
    "sympathy_coding", "arc_quality",
]

df = df[column_order]


output_path = "parsed_cast_data_v2.csv"
df.to_csv(output_path, index=False)


# Overview summary
print("\nDataset overview")
print(f"Titles:       {df['title'].nunique()}")
print(f"Cast rows:    {len(df)}")
print(f"Named chars:  {df['is_named_character'].sum()} ({df['is_named_character'].mean()*100:.1f}%)")

print("\nGender breakdown (actor)")
print(df["actor_gender"].value_counts().to_string())

print("\nRole type breakdown")
print(df["role_type"].value_counts().to_string())

print("\nGender × role type")
print(df.groupby(["role_type", "actor_gender"]).size().unstack(fill_value=0).to_string())

print("\nTitles in dataset")
for title, group in df.groupby("title"):
    start = group['start_year'].iloc[0]
    end = group['end_year'].iloc[0]
    start_str = str(int(start)) if pd.notna(start) else "?"
    end_str = str(int(end)) if pd.notna(end) else "2026"
    years = f"{start_str}–{end_str}"    
    print(f"  {title} ({years}) — {len(group)} cast members")
