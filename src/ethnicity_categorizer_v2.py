import pandas as pd
from openai import OpenAI
import json
import time
 
START_FROM = 5000
BATCH_SIZE = 1000
 
INPUT_FILE = "parsed_cast_data_v2.csv"
 
VALID_CATEGORIES = [
    "White", "Black", "Hispanic/Latino", "East Asian",
    "South Asian", "Middle Eastern", "Mixed/Multiracial", "Unknown"
]
 
client = OpenAI()
 
df = pd.read_csv(INPUT_FILE, dtype=str)
unique_actors = (
    df[["actor_name", "actor_tmdb_id"]]
    .drop_duplicates()
    .reset_index(drop=True)
)
print(f"Found {len(unique_actors)} unique actors total")
 
batch = unique_actors.iloc[START_FROM : START_FROM + BATCH_SIZE]
print(f"Processing rows {START_FROM} to {START_FROM + len(batch) - 1}")
 
ACTORS_FILE = f"actors_ethnicity_{START_FROM}_{START_FROM + BATCH_SIZE}.csv"
 
def annotate_actor(actor_name: str) -> dict:
    prompt = f"""You are helping with an academic research project on media representation.
 
For the actor '{actor_name}', provide:
1. Their ethnicity from EXACTLY one of these categories:
   White, Black, Hispanic/Latino, East Asian, South Asian, Middle Eastern, Mixed/Multiracial, Unknown
   If you would say Unknown but have a low or medium confidence but then think they look White, classify as White.
 
2. Your confidence level: high, medium, or low
   - high: this actor is well-known and their ethnicity is publicly documented
   - medium: reasonable inference but not certain
   - low: limited public information, significant uncertainty
 
3. A single short sentence explaining your reasoning
 
Respond ONLY with valid JSON in this exact format, nothing else:
{{"ethnicity": "...", "confidence": "...", "reasoning": "..."}}"""
 
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=150,
            temperature=0,
            messages=[
                {"role": "system", "content": "You are a precise research assistant. Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ]
        )
        raw = response.choices[0].message.content.strip()
        result = json.loads(raw)
 
        if result.get("ethnicity") not in VALID_CATEGORIES:
            result["ethnicity"] = "Unknown"
            result["confidence"] = "low"
            result["reasoning"] = "Returned unexpected category, defaulted to Unknown"
 
        return result
 
    except Exception as e:
        return {"ethnicity": "Unknown", "confidence": "low", "reasoning": f"API error: {str(e)}"}
 
 
results = []
for i, row in batch.iterrows():
    actor_name = row["actor_name"]
    print(f"[{i+1}/{len(unique_actors)}] {actor_name}...", end=" ", flush=True)
 
    result = annotate_actor(actor_name)
    results.append({
        "actor_name": actor_name,
        "actor_tmdb_id": row["actor_tmdb_id"],
        "actor_ethnicity": result["ethnicity"],
        "confidence": result["confidence"],
        "reasoning": result["reasoning"],
    })
    print(f"{result['ethnicity']} ({result['confidence']})")
    time.sleep(0.2)
 
actors_df = pd.DataFrame(results)
actors_df.to_csv(ACTORS_FILE, index=False)
print(f"\nBatch saved to {ACTORS_FILE}")
print(f"Next batch: set START_FROM = {START_FROM + BATCH_SIZE}")