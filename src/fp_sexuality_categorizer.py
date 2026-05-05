import pandas as pd
from openai import OpenAI
import json
import time
  
INPUT_FILE  = "parsed_data_annotated.csv" # output from ethnicity script
ACTORS_FILE = "actors_sexuality_annotated.csv"
OUTPUT_FILE = "parsed_data_annotated.csv" # overwrite with new column added
 
# Deliberately broad categories
S_CATEGORIES = [
    "Straight",
    "Gay/Lesbian",
    "Bisexual",
    "Queer", # self-identified queer without further specification
    "Unknown" # not publicly disclosed or insufficient information
]
 
client = OpenAI() 
 
# unique actor list 
df = pd.read_csv(INPUT_FILE, dtype=str)
unique_actors = (
    df[["actor_name", "actor_tmdb_id"]]
    .drop_duplicates()
    .reset_index(drop=True)
)
print(f"Found {len(unique_actors)} unique actors to annotate")
 

 
def annotate_sexuality(actor_name: str) -> dict:
    """
    Ask GPT to infer sexuality based on publicly available information.
    I used this prompt: 'Use "Straight" if the actor is married to the opposite sex.' 
    To deflate the 'Unknown' category. Will discuss if usefull
    """
    prompt = f"""You are helping with an academic research project on media representation.
 
For the actor '{actor_name}', provide their publicly known or disclosed sexuality.
 
Important guidelines:
- Only use information the actor has publicly disclosed themselves, or shown themselves
- Use "Straight" if the actor is married to the opposite sex. 
- If the actor has never publicly discussed their sexuality, but is in a opposite-sex relationship/marriage, without ever publicly been in a same-sex relationship, use "Straight"
- If the actor is married to the opposite sex, use "Straight" unless they have publicly said otherwise
- If the actor has never publicly discussed their sexuality, but has been in a public same-sex and opposite-sex relationships, use "Bisexual"
- If the actor has publicly identified as "Queer" without further specification, use "Queer"
- Do NOT infer from roles they have played
- Do NOT infer from appearance, mannerisms, or rumors
- If an actor has given ambiguous or evolving statements, use your best judgment 
  and note this in reasoning, but lean toward "Unknown" if genuinely unclear
- If you were to say "Unknown" with a low confidence, chose your best guess instead
 
Choose EXACTLY one category:
  Straight, Gay/Lesbian, Bisexual, Queer, Unknown
 
Confidence levels:
- high: actor has explicitly and clearly stated their sexuality publicly
- medium: actor has made statements that implies a category but haven't used a specific label
- low: very limited or ambiguous public information
 
Respond ONLY with valid JSON in this exact format, nothing else:
{{"sexuality": "...", "confidence": "...", "reasoning": "..."}}"""
 
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=150,
            temperature=0,
            messages=[
                {"role": "system", "content": "You are a precise research assistant. Always respond with valid JSON only. Follow the specified prompt guidelines."},
                {"role": "user", "content": prompt}
            ]
        )
        raw = response.choices[0].message.content.strip()
        result = json.loads(raw)
 
        if result.get("sexuality") not in S_CATEGORIES:
            result["sexuality"] = "Unknown"
            result["confidence"] = "low"
            result["reasoning"] = "Returned unexpected category, defaulted to Unknown"
 
        return result
 
    except Exception as e:
        return {"sexuality": "Unknown", "confidence": "low", "reasoning": f"API error: {str(e)}"}
 
  
results = []
for i, row in unique_actors.iterrows():
    actor_name = row["actor_name"]
    print(f"[{i+1}/{len(unique_actors)}] {actor_name}...", end=" ", flush=True)
 
    result = annotate_sexuality(actor_name)
    results.append({
        "actor_name": actor_name,
        "actor_tmdb_id": row["actor_tmdb_id"],
        "actor_sexuality": result["sexuality"],
        "confidence_sexuality": result["confidence"],
        "reasoning_sexuality": result["reasoning"],
    })
    print(f"{result['sexuality']} ({result['confidence']})")
    time.sleep(0.2)
 
 
# Save in file 
actors_df = pd.DataFrame(results)
actors_df.to_csv(ACTORS_FILE, index=False)
 
print(f"\nSaved to {ACTORS_FILE}")
print("\nConfidence breakdown:")
print(actors_df["confidence_sexuality"].value_counts().to_string())
print("\nSexuality breakdown:")
print(actors_df["actor_sexuality"].value_counts().to_string())
 
# Show who is not unknown
disclosed = actors_df[actors_df["actor_sexuality"] != "Unknown"]
print(f"\n{len(disclosed)} actors with disclosed sexuality:")
print(disclosed[["actor_name", "actor_sexuality", "confidence_sexuality", "reasoning_sexuality"]].to_string())
 
 
# ── STEP 5: MERGE BACK INTO FULL DATASET ─────────────────────────────────────
 
# Drop existing empty sexuality column and confidence column if present
cols_to_drop = [c for c in ["actor_sexuality", "confidence_sexuality"] if c in df.columns]
df = df.drop(columns=cols_to_drop)
 
df = df.merge(
    actors_df[["actor_tmdb_id", "actor_sexuality", "confidence_sexuality"]],
    on="actor_tmdb_id",
    how="left"
)
 
df.to_csv(OUTPUT_FILE, index=False)
print(f"\nFull annotated dataset saved to {OUTPUT_FILE}")
print("Note: most actors will be Unknown — this is expected, not a failure.")