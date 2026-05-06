import pandas as pd
import numpy as np
from scipy import stats
from statsmodels.stats.multitest import multipletests

df = pd.read_csv("parsed_data_with_ethnicity_v2.csv", dtype=str)

df["billing_order"] = pd.to_numeric(df["billing_order"], errors="coerce")
df["prominence_score"] = pd.to_numeric(df["prominence_score"], errors="coerce")
df["start_year"] = pd.to_numeric(df["start_year"], errors="coerce")

named = df[df["is_named_character"] == "True"].copy()
named["decade"] = (named["start_year"] // 10 * 10).astype("Int64").astype(str) + "s"
named["ethnicity_simple"] = named["actor_ethnicity"].apply(
    lambda x: "White" if x == "White" else ("Unknown" if x == "Unknown" else "Non-white")
)
named["genre_primary"] = named["genres"].str.split("|").str[0]

leads = named[named["role_type"] == "lead"]
ROLE_ORDER = ["lead", "supporting", "minor"]

print("Week 7 checkpoint analysis")
print(f"Rows: {len(named)} named characters across {named['title'].nunique()} titles")


print("\n 1. Gender trends over time")
print("=" * 65)

print("\n% female roles over time:")
print(named.groupby("decade").apply(lambda x: (x["actor_gender"] == "female").mean() * 100).round(1).to_string())

print("\n% female leads over time:")
print(leads.groupby("decade").apply(lambda x: (x["actor_gender"] == "female").mean() * 100).round(1).to_string())

print("\nAverage female prominence score over time:")
print(named[named["actor_gender"] == "female"].groupby("decade")["prominence_score"].mean().round(4).to_string())


print("\n 2. Ethnicity trends over time")
print("=" * 65)

print("\n% White by decade (all roles):")
print(named.groupby("decade").apply(lambda x: (x["actor_ethnicity"] == "White").mean() * 100).round(1).to_string())

print("\n% White leads by decade:")
print(leads.groupby("decade").apply(lambda x: (x["actor_ethnicity"] == "White").mean() * 100).round(1).to_string())

print("\nNon-white representation by decade (% of all roles):")
print(named.groupby("decade").apply(lambda x: (x["actor_ethnicity"] != "White").mean() * 100).round(1).to_string())


print("\n 3. Lead vs Supporting: Gender & Ethnicity")
print("=" * 65)

print("\nGender distribution by role type (%):")
gender_role = named.groupby("role_type")["actor_gender"].value_counts(normalize=True).mul(100).round(1).unstack(fill_value=0)
print(gender_role.reindex(ROLE_ORDER).to_string())

print("\nEthnicity distribution by role type (%):")
eth_role = named.groupby("role_type")["actor_ethnicity"].value_counts(normalize=True).mul(100).round(1).unstack(fill_value=0)
print(eth_role.reindex(ROLE_ORDER).to_string())

print("\nAverage prominence score by gender and role type:")
print(named.groupby(["role_type", "actor_gender"])["prominence_score"].mean().round(4).unstack().reindex(ROLE_ORDER).to_string())

print("\nAverage prominence score by ethnicity and role type:")
print(named.groupby(["role_type", "actor_ethnicity"])["prominence_score"].mean().round(4).unstack().reindex(ROLE_ORDER).to_string())


print("\n 4. Intersectionality: Gender and Ethnicity")
print("=" * 65)

print("\nLead roles — gender × ethnicity (counts):")
print(leads.groupby(["actor_gender", "actor_ethnicity"]).size().unstack(fill_value=0).to_string())

print("\nAll roles — gender × ethnicity simplified (%):")
intersect_all = named.groupby(["actor_gender", "ethnicity_simple"]).size().unstack(fill_value=0)
print(intersect_all.div(intersect_all.sum().sum()).mul(100).round(1).to_string())

print("\nAverage prominence: gender × ethnicity (simplified):")
print(named.groupby(["actor_gender", "ethnicity_simple"])["prominence_score"].mean().round(4).unstack().to_string())


print("\n 5. Gender & Ethnicity by Media Type")
print("=" * 65)

for mtype in ["movie", "tv"]:
    sub = named[named["media_type"] == mtype]
    pct_female = (sub["actor_gender"] == "female").mean() * 100
    pct_nonwhite = (sub["actor_ethnicity"] != "White").mean() * 100
    print(f"\n{mtype.upper()} — {sub['title'].nunique()} titles, {len(sub)} cast rows")
    print(f"% female:    {pct_female:.1f}%")
    print(f"% non-white: {pct_nonwhite:.1f}%")

print("\nGender by media type and role tier (% female):")
print(named.groupby(["media_type", "role_type"]).apply(
    lambda x: (x["actor_gender"] == "female").mean() * 100
).round(1).unstack().to_string())


print("\n 6. Genre breakdown")
print("=" * 65)

print("\n% female by primary genre:")
genre_gender = named.groupby("genre_primary").apply(
    lambda x: (x["actor_gender"] == "female").mean() * 100 if len(x) >= 10 else None
).dropna().round(1).sort_values(ascending=False)
print(genre_gender.to_string())

print("\n% non-white by primary genre:")
genre_eth = named.groupby("genre_primary").apply(
    lambda x: (x["actor_ethnicity"] != "White").mean() * 100 if len(x) >= 10 else None
).dropna().round(1).sort_values(ascending=False)
print(genre_eth.to_string())


print("\n 7. Statistical Tests (Benjamini-Hochberg corrected)")
print("=" * 65)

tests = []

def add_test(name, a, b, tests, test_type="ttest"):
    if test_type == "ttest":
        _, p = stats.ttest_ind(a, b)
        d = abs(cohens_d(a, b))
        comparison = f"{a.mean()*100:.1f}% vs {b.mean()*100:.1f}%" if a.max() <= 1 else f"{a.mean():.4f} vs {b.mean():.4f}"
    else:
        _, p = stats.f_oneway(*a)
        d, comparison = None, "ANOVA — see genre chart"
    tests.append((name, p, d, comparison))

tests = []

add_test("Female representation: leads vs non-leads",
    (named[named["role_type"] == "lead"]["actor_gender"] == "female").astype(float),
    (named[named["role_type"] != "lead"]["actor_gender"] == "female").astype(float), tests)

add_test("Non-white representation: leads vs non-leads",
    (named[named["role_type"] == "lead"]["actor_ethnicity"] != "White").astype(float),
    (named[named["role_type"] != "lead"]["actor_ethnicity"] != "White").astype(float), tests)

add_test("Prominence score: male vs female",
    named[named["actor_gender"] == "male"]["prominence_score"].dropna(),
    named[named["actor_gender"] == "female"]["prominence_score"].dropna(), tests)

add_test("Prominence score: White vs non-white",
    named[named["actor_ethnicity"] == "White"]["prominence_score"].dropna(),
    named[named["actor_ethnicity"] != "White"]["prominence_score"].dropna(), tests)

leads_80s = leads[leads["decade"] == "1980s"]
leads_10s = leads[leads["decade"] == "2010s"]
if len(leads_80s) > 0 and len(leads_10s) > 0:
    add_test("Female leads: 1980s vs 2010s",
        (leads_80s["actor_gender"] == "female").astype(float),
        (leads_10s["actor_gender"] == "female").astype(float), tests)

early_leads  = named[named["decade"].isin(["1980s", "1990s"]) & (named["role_type"] == "lead")]
recent_leads = named[named["decade"].isin(["2010s", "2020s"]) & (named["role_type"] == "lead")]
if len(early_leads) > 0 and len(recent_leads) > 0:
    add_test("Non-white leads: early vs recent decades",
        (early_leads["actor_ethnicity"] != "White").astype(float),
        (recent_leads["actor_ethnicity"] != "White").astype(float), tests)

w_f  = named[(named["actor_gender"] == "female") & (named["actor_ethnicity"] == "White")]["prominence_score"].dropna()
nw_f = named[(named["actor_gender"] == "female") & (named["actor_ethnicity"] != "White")]["prominence_score"].dropna()
w_m  = named[(named["actor_gender"] == "male")   & (named["actor_ethnicity"] == "White")]["prominence_score"].dropna()
nw_m = named[(named["actor_gender"] == "male")   & (named["actor_ethnicity"] != "White")]["prominence_score"].dropna()

add_test("Prominence: white female vs non-white female", w_f, nw_f, tests)
add_test("Prominence: white male vs non-white male",     w_m, nw_m, tests)
print(f"Ethnicity prominence penalty — female: {(w_f.mean()-nw_f.mean()):.4f}, male: {(w_m.mean()-nw_m.mean()):.4f}")

add_test("Female representation: TV vs film",
    (named[named["media_type"] == "tv"]["actor_gender"] == "female").astype(float),
    (named[named["media_type"] == "movie"]["actor_gender"] == "female").astype(float), tests)

add_test("Non-white representation: TV vs film",
    (named[named["media_type"] == "tv"]["actor_ethnicity"] != "White").astype(float),
    (named[named["media_type"] == "movie"]["actor_ethnicity"] != "White").astype(float), tests)

genre_groups_g = [(named[named["genre_primary"] == g]["actor_gender"] == "female").astype(float)
    for g in named["genre_primary"].dropna().unique() if len(named[named["genre_primary"] == g]) >= 10]
if len(genre_groups_g) >= 2:
    add_test("Gender representation differs across genres", genre_groups_g, None, tests, test_type="anova")

genre_groups_e = [(named[named["genre_primary"] == g]["actor_ethnicity"] != "White").astype(float)
    for g in named["genre_primary"].dropna().unique() if len(named[named["genre_primary"] == g]) >= 10]
if len(genre_groups_e) >= 2:
    add_test("Ethnicity representation differs across genres", genre_groups_e, None, tests, test_type="anova")

test_names = [t[0] for t in tests]
p_values   = [t[1] for t in tests]
reject, p_corrected, _, _ = multipletests(p_values, method="fdr_bh")
def fmt_p(p):
    if p < 0.0001:
        return f"{p:.2e}"
    return f"{p:.4f}"

print(f"\n{'Test':<50} {'p-raw':>10} {'p-corr':>10} {'Sig':>6}")
print("-" * 80)
for name, p_raw, p_corr, sig in zip(test_names, p_values, p_corrected, reject):
    flag = "YES" if sig else "no"
    print(f"{name:<50} {fmt_p(p_raw):>10} {fmt_p(p_corr):>10} {flag:>6}")

print("\nNote: Benjamini-Hochberg correction at FDR = 0.05")




"""

 1. Gender trends over time
=================================================================

% female roles over time:
decade
1910s    14.3
1920s    20.0
1930s    29.4
1950s    12.5
1960s    25.0
1970s    26.4
1980s    25.9
1990s    34.7
2000s    28.4
2010s    36.1
2020s    34.2

% female leads over time:
decade
1910s    33.3
1920s    33.3
1930s    33.3
1950s    15.4
1960s    17.2
1970s    26.3
1980s    22.8
1990s    39.3
2000s    34.7
2010s    31.7
2020s    42.0

Average female prominence score over time:
decade
1910s    0.1928
1920s    0.1840
1930s    0.0832
1950s    0.0797
1960s    0.1554
1970s    0.0889
1980s    0.1065
1990s    0.1005
2000s    0.0973
2010s    0.0753
2020s    0.0654

 2. Ethnicity trends over time
=================================================================

% White by decade (all roles):
decade
1910s    100.0
1920s    100.0
1930s     94.1
1950s     97.9
1960s     88.3
1970s     93.7
1980s     82.1
1990s     84.1
2000s     81.0
2010s     73.8
2020s     61.1

% White leads by decade:
decade
1910s    100.0
1920s    100.0
1930s     66.7
1950s    100.0
1960s     93.1
1970s     94.7
1980s     86.0
1990s     92.4
2000s     87.2
2010s     82.5
2020s     66.5

Non-white representation by decade (% of all roles):
decade
1910s     0.0
1920s     0.0
1930s     5.9
1950s     2.1
1960s    11.7
1970s     6.3
1980s    17.9
1990s    15.9
2000s    19.0
2010s    26.2
2020s    38.9

 3. Lead vs Supporting: Gender & Ethnicity
=================================================================

Gender distribution by role type (%):
actor_gender  female  male  unspecified
role_type                              
lead            35.9  62.8          1.4
supporting      34.1  62.3          3.6
minor           30.5  59.6         10.0

Ethnicity distribution by role type (%):
actor_ethnicity  Black  East Asian  Hispanic/Latino  Middle Eastern  Mixed/Multiracial  South Asian  Unknown  White
role_type                                                                                                          
lead               8.3         2.7              3.9             0.5                4.2          0.3      0.8   79.2
supporting        11.3         3.5              5.9             1.5                5.1          1.2      1.5   70.0
minor             10.9         2.9              6.2             1.2                4.1          1.0      4.7   68.9

Average prominence score by gender and role type:
actor_gender  female    male  unspecified
role_type                                
lead          0.2088  0.2422       0.2048
supporting    0.0578  0.0545       0.0459
minor         0.0212  0.0207       0.0182

Average prominence score by ethnicity and role type:
actor_ethnicity   Black  East Asian  Hispanic/Latino  Middle Eastern  Mixed/Multiracial  South Asian  Unknown   White
role_type                                                                                                            
lead             0.2016      0.1896           0.2062          0.1973             0.1893       0.1799   0.1905  0.2381
supporting       0.0542      0.0443           0.0628          0.0515             0.0519       0.0512   0.0470  0.0560
minor            0.0207      0.0187           0.0206          0.0205             0.0204       0.0207   0.0180  0.0208

 4. Intersectionality: Gender and Ethnicity
=================================================================

Lead roles — gender × ethnicity (counts):
actor_ethnicity  Black  East Asian  Hispanic/Latino  Middle Eastern  Mixed/Multiracial  South Asian  Unknown  White
actor_gender                                                                                                       
female              29          21               21               2                 38            0        6    433
male                97          20               39               6                 26            4        2    768
unspecified          2           0                0               0                  1            0        5     13

All roles — gender × ethnicity simplified (%):
ethnicity_simple  Non-white  Unknown  White
actor_gender                               
female                  9.6      1.0   22.4
male                   14.9      1.0   45.4
unspecified             1.4      0.6    3.6

Average prominence: gender × ethnicity (simplified):
ethnicity_simple  Non-white  Unknown   White
actor_gender                                
female               0.0643   0.0369  0.0857
male                 0.0659   0.0297  0.0868
unspecified          0.0274   0.0443  0.0355

 5. Gender & Ethnicity by Media Type
=================================================================

MOVIE — 295 titles, 5570 cast rows
% female:    31.0%
% non-white: 29.4%

TV — 286 titles, 1925 cast rows
% female:    38.7%
% non-white: 26.1%

Gender by media type and role tier (% female):
role_type   lead  minor  supporting
media_type                         
movie       36.2   29.0        31.3
tv          35.5   40.8        40.1

 6. Genre breakdown
=================================================================

% female by primary genre:
genre_primary
Mystery               46.9
Documentary           43.9
Fantasy               43.1
Romance               40.8
Soap                  40.0
Comedy                39.6
Sci-Fi & Fantasy      37.7
Drama                 37.0
Reality               35.7
Horror                35.2
Family                34.7
Talk                  33.3
Crime                 32.0
Science Fiction       31.9
Animation             31.3
Western               31.2
Music                 27.5
Adventure             27.2
Action                26.8
Action & Adventure    25.9
Thriller              23.1
War                   20.0
History               13.9

% non-white by primary genre:
genre_primary
Music                 45.0
Fantasy               42.5
History               38.9
Family                37.0
Action                36.9
Reality               35.7
Action & Adventure    34.7
Science Fiction       33.5
Romance               33.0
Thriller              30.8
Crime                 30.2
Documentary           29.3
Talk                  29.2
Sci-Fi & Fantasy      29.0
Horror                27.9
Mystery               26.2
Soap                  25.0
Animation             23.7
Adventure             22.5
Drama                 22.4
Comedy                20.0
Western               12.5
War                    0.0

 7. Statistical Tests (Benjamini-Hochberg corrected)
=================================================================

Ethnicity prominence penalty — female: 0.0240, male: 0.0232

Test                                                  p-raw   p-corr    Sig
----------------------------------------------------------------------------
Female representation: leads vs non-leads            0.0074   0.0089    YES
Non-white representation: leads vs non-leads         0.0000   0.0000    YES
Prominence score: male vs female                     0.3071   0.3071     no
Prominence score: White vs non-white                 0.0000   0.0000    YES
Female leads: 1980s vs 2010s                         0.1744   0.1903     no
Non-white leads: early vs recent decades             0.0000   0.0000    YES
Prominence: white female vs non-white female         0.0000   0.0000    YES
Prominence: white male vs non-white male             0.0000   0.0000    YES
Female representation: TV vs film                    0.0000   0.0000    YES
Non-white representation: TV vs film                 0.0053   0.0071    YES
Gender representation differs across genres (ANOVA)   0.0000   0.0000    YES
Ethnicity representation differs across genres (ANOVA)   0.0000   0.0000    YES

Note: Benjamini-Hochberg correction at FDR = 0.05

"""