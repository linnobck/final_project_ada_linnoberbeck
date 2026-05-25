import pandas as pd
from openai import OpenAI
import json
import time


INPUT_FILE  = "parsed_data_with_ethnicity_v2.csv"
OUTPUT_FILE = "parsed_data_with_ethnicity_sympathy_arc.csv"
CHARS_FILE  = "characters_sympathy_reasoning.csv"

SYMPATHY_CATEGORIES = [
    "protagonist", # audience roots for them throughout
    "antagonist", # audience is against them throughout
    "redeemed", # starts negative, earns sympathy
    "fallen", # starts sympathetic, loses it
    "antihero", # rooted for despite moral ambiguity
    "neutral", # no strong sympathy
]

ARC_PRESENCE_CATEGORIES = [
    "significant", # clear transformation
    "minor", # some development
    "flat", # no meaningful change
]

ARC_DIRECTION_CATEGORIES = [
    "positive", # grows or improves
    "negative", # deteriorates or falls
    "ambiguous", # changes but not clearly one way
    "none", # use when arc_presence is flat
]

client = OpenAI()

df = pd.read_csv(INPUT_FILE, dtype=str)

unique_chars = (
    df[["title", "character_name", "actor_name", "media_type"]]
    .drop_duplicates(subset=["title", "character_name"])
    .reset_index(drop=True)
)

# annotate each character
def annotate_character(title, character_name, actor_name, media_type):
    """
    Ask GPT to assess sympathy coding and arc quality for a character.
    Requires knowledge of the show/film — works best for major characters in well-known titles.
    """
    media_label = "TV show" if media_type == "tv" else "film"

    prompt = f"""You are helping with an academic research project on media representation.

For the character '{character_name}' played by {actor_name} in the {media_label} '{title}', provide:

1. SYMPATHY CODING — how is the audience meant to feel about this character?
Choose EXACTLY one:
- protagonist: a main character the audience roots for
- antagonist: a character who opposes the protagonist and creates conflict
- redeemed: starts as antagonist or unsympathetic, earns sympathy by the end
- fallen: starts sympathetic, becomes antagonistic or loses audience sympathy
- antihero: audience roots for them despite morally questionable behavior
- neutral: use ONLY for genuine side characters with minimal screen time and no clear relationship with the audience — do NOT use this as a default for supporting characters who have a clear role in the story

2. ARC PRESENCE — does this character meaningfully change over the story?
Choose EXACTLY one:
- significant: clear internal transformation — beliefs, values, relationships, or worldview change
- minor: some growth or change but fundamentally stays the same person
- flat: purely functional character, exists to serve the plot rather than develop as a person
- Use flat ONLY when you are confident the character has no development, not when you are uncertain

3. ARC DIRECTION — if the character changes, which way?
Choose EXACTLY one:
- positive: grows, improves, or resolves something
- negative: deteriorates, falls, or loses something
- ambiguous: changes meaningfully but not clearly in one direction
- none: use ONLY if arc_presence is flat

4. CONFIDENCE: high, medium, or low
- high: well-known character you have detailed knowledge of
- medium: some knowledge but not certain of all details  
- low: minor character, unfamiliar title, or insufficient knowledge to classify reliably — if low, still make your best guess but reflect uncertainty in your classifications by leaning toward simpler categories

5. REASONING: one short sentence explaining your assessment

Respond ONLY with valid JSON in this exact format, nothing else:
{{"sympathy_coding": "...", "arc_presence": "...", "arc_direction": "...", "confidence": "...", "reasoning": "..."}}"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=200,
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": "You are a precise research assistant with extensive knowledge of film and TV. Always respond with valid JSON only. For minor or unknown characters, use flat/neutral/none and low confidence."
                },
                {"role": "user", "content": prompt}
            ]
        )
        raw    = response.choices[0].message.content.strip()
        result = json.loads(raw)

        # validate categories
        if result.get("sympathy_coding") not in SYMPATHY_CATEGORIES:
            result["sympathy_coding"] = "neutral"
            result["confidence"]      = "low"

        if result.get("arc_presence") not in ARC_PRESENCE_CATEGORIES:
            result["arc_presence"] = "flat"
            result["confidence"]   = "low"

        if result.get("arc_direction") not in ARC_DIRECTION_CATEGORIES:
            result["arc_direction"] = "none"

        # flat arc should always have direction = none
        if result.get("arc_presence") == "flat":
            result["arc_direction"] = "none"

        return result

    except Exception as e:
        return {
            "sympathy_coding": "neutral",
            "arc_presence": "flat",
            "arc_direction": "none",
            "confidence": "low",
            "reasoning": f"API error: {str(e)}"
        }


# run annotation

results = []
for i, row in unique_chars.iterrows():
    title = row["title"]
    character_name = row["character_name"]
    actor_name = row["actor_name"]
    media_type = row["media_type"]

    print(f"[{i+1}/{len(unique_chars)}] {character_name} ({title})...", end=" ", flush=True)

    result = annotate_character(title, character_name, actor_name, media_type)
    results.append({
        "title": title,
        "character_name": character_name,
        "actor_name": actor_name,
        "sympathy_coding": result["sympathy_coding"],
        "arc_presence": result["arc_presence"],
        "arc_direction": result["arc_direction"],
        "confidence_arc": result["confidence"],
        "reasoning_arc": result["reasoning"],
    })
    print(f"{result['sympathy_coding']} | {result['arc_presence']} / {result['arc_direction']} ({result['confidence']})")
    time.sleep(0.25)


# save to file 
chars_df = pd.DataFrame(results)
chars_df.to_csv(CHARS_FILE, index=False)

print(f"\nSaved to {CHARS_FILE}")
print("\nSympathy coding breakdown")
print(chars_df["sympathy_coding"].value_counts().to_string())
print("\nArc presence breakdown")
print(chars_df["arc_presence"].value_counts().to_string())
print("\n")
print(chars_df["arc_direction"].value_counts().to_string())
print("\nConfidence breakdown")
print(chars_df["confidence_arc"].value_counts().to_string())

# show high confidence non-neutral, non-flat characters for review
interesting = chars_df[
    (chars_df["confidence_arc"] == "high") &
    (chars_df["sympathy_coding"] != "neutral") &
    (chars_df["arc_presence"] != "flat")
]
print(f"\n{len(interesting)} high-confidence characters with arc and sympathy")
print(interesting[["character_name", "title", "sympathy_coding", "arc_presence", "arc_direction"]].to_string())


# Merge into main dataset
# drop existing placeholder columns
cols_to_drop = [c for c in ["sympathy_coding", "arc_quality", "arc_presence",
                             "arc_direction", "confidence_arc"] if c in df.columns]
df = df.drop(columns=cols_to_drop)

df = df.merge(
    chars_df[["title", "character_name", "sympathy_coding",
              "arc_presence", "arc_direction", "confidence_arc"]],
    on=["title", "character_name"],
    how="left"
)

df.to_csv(OUTPUT_FILE, index=False)
print(f"\nFull annotated dataset saved to {OUTPUT_FILE}")


"""
Sympathy coding breakdown
sympathy_coding
neutral        4392
protagonist    1945
antagonist      526
antihero        211
fallen          127
redeemed         37

Arc presence breakdown
arc_presence
flat           4870
significant    1893
minor           475


arc_direction
none         4894
positive     1959
negative      307
ambiguous      78

Confidence breakdown
confidence_arc
low       3971
medium    1957
high      1310

1185 high-confidence characters with arc and sympathy
"""