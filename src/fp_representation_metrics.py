import pandas as pd
import numpy as np
  
df = pd.read_csv("/Users/linnoberbeck/Documents/UChicagoMasters/ADA/final_project_ada/parsed_data_annotated.csv", dtype=str)
 
# Cast numeric columns
df["billing_order"] = pd.to_numeric(df["billing_order"], errors="coerce")
df["prominence_score"] = pd.to_numeric(df["prominence_score"], errors="coerce")
df["start_year"] = pd.to_numeric(df["start_year"], errors="coerce")
 
# Named characters only
named = df[df["is_named_character"] == "True"].copy()
 
ROLE_ORDER = ["lead", "supporting", "minor"]
 
print("Representation metrics")
print(f"Total cast rows:      {len(df)}")
print(f"Named characters:     {len(named)}")
print(f"Titles:               {df['title'].nunique()}")
print(f"TV shows:             {df[df['media_type']=='tv']['title'].nunique()}")
print(f"Movies:               {df[df['media_type']=='movie']['title'].nunique()}")
 

# Gender 
print("Gender:")
 
# Overall counts and proportions
gender_counts = named["actor_gender"].value_counts()
gender_pct = (named["actor_gender"].value_counts(normalize=True) * 100).round(1)
gender_summary = pd.DataFrame({"count": gender_counts, "percent": gender_pct})
print("\nOverall:")
print(gender_summary.to_string())
 
print("\nBy role type:")
gender_role = named.groupby(["role_type", "actor_gender"]).size().unstack(fill_value=0)
gender_role = gender_role.reindex(ROLE_ORDER)
gender_role_pct = gender_role.div(gender_role.sum(axis=1), axis=0).mul(100).round(1)
print(gender_role.to_string())
print("\nAs percentages:")
print(gender_role_pct.to_string())
 
print("\nAverage prominence score by gender:")
print(named.groupby("actor_gender")["prominence_score"].mean().round(4).to_string())
 
 
# Ethnicity
 
print("Ethnicity:")
 
eth_counts = named["actor_ethnicity"].value_counts()
eth_pct = (named["actor_ethnicity"].value_counts(normalize=True) * 100).round(1)
eth_summary = pd.DataFrame({"count": eth_counts, "percent": eth_pct})
print("\nOverall:")
print(eth_summary.to_string())
 
print("\nBy role type:")
eth_role = named.groupby(["role_type", "actor_ethnicity"]).size().unstack(fill_value=0)
eth_role = eth_role.reindex(ROLE_ORDER)
eth_role_pct = eth_role.div(eth_role.sum(axis=1), axis=0).mul(100).round(1)
print(eth_role_pct.to_string())
 
print("\nAverage prominence score by ethnicity:")
print(named.groupby("actor_ethnicity")["prominence_score"].mean().round(4).sort_values(ascending=False).to_string())
 
# White vs non-White summary
named["is_white"] = named["actor_ethnicity"] == "White"
print(f"\nWhite actors:     {named['is_white'].sum()} ({named['is_white'].mean()*100:.1f}%)")
print(f"Non-white actors: {(~named['is_white']).sum()} ({(~named['is_white']).mean()*100:.1f}%)")
 
print("\nWhite vs non-White by role type (% White):")
for role in ROLE_ORDER:
    sub = named[named["role_type"] == role]
    pct = sub["is_white"].mean() * 100
    print(f"  {role}: {pct:.1f}% White")
 
 
# Sexuality 

print("Sexuality (disclosed only):")
 
# Disclosed actors only
disclosed = named[named["actor_sexuality"] != "Unknown"]
print(f"\nActors with disclosed sexuality: {len(disclosed)} of {len(named)} ({len(disclosed)/len(named)*100:.1f}%)")
 
sex_counts = disclosed["actor_sexuality"].value_counts()
sex_pct = (disclosed["actor_sexuality"].value_counts(normalize=True) * 100).round(1)
print("\nAmong disclosed actors:")
print(pd.DataFrame({"count": sex_counts, "percent": sex_pct}).to_string())
 
# Non-straight by role type
non_straight = named[named["actor_sexuality"].isin(["Gay/Lesbian", "Bisexual", "Queer"])]
print(f"\nNon-straight actors (disclosed): {len(non_straight)}")
if len(non_straight) > 0:
    print("\nNon-straight actors by role type:")
    print(non_straight["role_type"].value_counts().to_string())
    print("\nNon-straight actors by gender:")
    print(non_straight["actor_gender"].value_counts().to_string())
 

# Intersectionality 
 
print("Intersectionality: Gender × Ethnicity")
 
# Leads only
leads = named[named["role_type"] == "lead"]
print(f"\nLead roles only ({len(leads)} total):")
intersect = leads.groupby(["actor_gender", "actor_ethnicity"]).size().unstack(fill_value=0)
print(intersect.to_string())
 
print("\nAverage prominence score by gender × ethnicity:")
pivot = named.groupby(["actor_gender", "actor_ethnicity"])["prominence_score"].mean().round(4).unstack()
print(pivot.to_string())
 
 
# Trends over time
#  
print("Trends over time:")
 
# Decade bins
named["decade"] = (named["start_year"] // 10 * 10).astype("Int64").astype(str) + "s"
 
print("\n'%' Female by decade:")
decade_gender = named.groupby("decade").apply(
    lambda x: (x["actor_gender"] == "female").mean() * 100
).round(1)
print(decade_gender.to_string())
 
print("\n'%' White by decade:")
decade_eth = named.groupby("decade").apply(
    lambda x: (x["actor_ethnicity"] == "White").mean() * 100
).round(1)
print(decade_eth.to_string())
 
print("\nLead role gender split by decade ('%' female leads):")
leads_decade = named[named["role_type"] == "lead"].groupby("decade").apply(
    lambda x: (x["actor_gender"] == "female").mean() * 100
).round(1)
print(leads_decade.to_string())
 
 