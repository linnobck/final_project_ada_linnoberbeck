import requests
import csv

API_KEY = "3a7bea432386c9c51eb03cccfe4ed094"
BASE_URL = "https://api.themoviedb.org/3"

# Search for a title and get its TMDB ID
def search_title(title, media_type="movie"):
    url = f"{BASE_URL}/search/{media_type}"
    params = {"api_key": API_KEY, "query": title}
    response = requests.get(url, params=params)
    results = response.json().get("results", [])
    if results:
        return results[0]["id"]  # returns the top match
    return None


# pull credits for ID 
def get_credits(tmdb_id, media_type="movie"):
    url = f"{BASE_URL}/{media_type}/{tmdb_id}/credits"
    params = {"api_key": API_KEY}
    response = requests.get(url, params=params)
    return response.json().get("cast", [])


# pull metadata for ID
def get_metadata(tmdb_id, media_type="movie"):
    url = f"{BASE_URL}/{media_type}/{tmdb_id}"
    params = {"api_key": API_KEY}
    response = requests.get(url, params=params)
    data = response.json()
    
    if media_type == "movie":
        start_year = data.get("release_date", "")[:4] # year
        end_year = start_year  # movies start and end same year
    else:
        start_year = data.get("first_air_date", "")[:4]
        end_year = data.get("last_air_date", "")[:4]  # TV gets an end date
    
    genres = [g["name"] for g in data.get("genres", [])]
    return start_year, end_year, genres

# Might just use tv series depending on how the output looks
# Might just use the top # from TMBD
# Movies might be too alpha male cliche type
# Most movies that include gay characters are marketed as explicitly gay movies
# Should I only include US productions?
# Movies have a way larger cast
TITLES = [
    ("Succession", "tv"),
    ("Teen Wolf", "tv"),
    ("Bob's Burgers", "tv"),
    ("Gossip Girl", "tv"),
    ("The Boys", "tv"),
    ("Grey's Anatomy", "tv"),
    ("Peaky Blinders", "tv"),
    ("Game of Thrones", "tv"),
    ("NCIS", "tv"),
    ("Shameless", "tv"),
    ("Breaking Bad ", "tv"),
    ("Modern Family", "tv"),
    ("Friends", "tv"),
    ("The Walking Dead", "tv"),
    ("American Dad!", "tv"),
    ("Euphoria", "tv"),
    ("Supernatural", "tv"),
    ("Rick and Morty", "tv"),
    ("The Last Of Us", "tv"),
    ("Bridgerton", "tv"),
    ("American Horror Story", "tv"),
    ("South Park", "tv"),
    ("Orange Is The New Black", "tv"),
    ("How I Met Your Mother", "tv"),
    ("Brooklyn Nine-Nine", "tv"),
    ("The Dark Knight", "movie"),
    ("Parasite", "movie"),
    ("Pulp Fiction", "movie"),
    ("Forrest Gump", "movie"),
    ("Spider-Man: Into the Spider-Verse", "movie"),
    ("Inception", "movie"),
    ("Back To The Future", "movie"),
    ("The Wild Robot", "movie"),
    ("Avengers: Endgame", "movie"),
    ("Avengers: Infinity War", "movie"),
    ("Inglourious Basterds", "movie"),
    ("Whiplash", "movie"),
    ("Puss in Boots", "movie"),
    ("Coco", "movie"),
    ("La Haine", "movie"),
    ("Oppenheimer", "movie"),
    ("The Grand Budapest Hotel", "movie"),
    ("The Wolf of Wall Street", "movie"),
    ("Jojo Rabbit", "movie"),
    ("Kill Bill: Vol. 1", "movie"),
    ("Inside Out", "movie"),
    ("GOAT", "movie"),
    ("Coraline", "movie"),
    ("How to Train Your Dragon", "movie"),
    ("Knives Out", "movie")
]

with open("raw_cast_data.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow([
        # Title-level 
        "title", "start_year", "end_year", "genres", "tmdb_id", "media_type",

        # Actor-level
        "actor_name", "actor_tmdb_id", "actor_gender_code",
        "actor_ethnicity", # manual
        "actor_sexuality", # manual

        # Character-level
        "character_name",
        "character_gender", # manual
        "character_ethnicity", # manual
        "character_sexuality", # manual

        # Mismatch flags (derived in parser later)
        "gender_mismatch",
        "ethnicity_mismatch",
        "sexuality_mismatch",

        # Role data
        "billing_order",
        "role_type", # derived in parser (lead/supporting/minor)
        "prominence_score", # derived in parser

        # Qualitative (manual, Week 7)
        "sympathy_coding",
        "arc_quality",
    ])


    for title, media_type in TITLES:
        tmdb_id = search_title(title, media_type)
        if not tmdb_id:
            print(f"Not found: {title}")
            continue

        start_year, end_year, genres = get_metadata(tmdb_id, media_type)
        cast = get_credits(tmdb_id, media_type)

        for member in cast:
            raw_order = member.get("order", 0)
    
            # skip minor background roles
            if raw_order >= 20:
                continue
            
            # fix zero-indexing and derive role type
            billing_order = raw_order + 1
            if billing_order <= 3:
                role_type = "lead"
            elif billing_order <= 10:
                role_type = "supporting"
            else:
                role_type = "minor"
            writer.writerow([
                # Title-level
                title, start_year, end_year, "|".join(genres), tmdb_id, media_type,

                # Actor-level
                member.get("name"),
                member.get("id"),
                member.get("gender"),
                "", "", "",  # actor_ethnicity, actor_sexuality, actor_age_at_release

                # Character-level
                member.get("character"),
                "", "", "",  # character_gender, character_ethnicity, character_sexuality

                # Mismatch flags
                "", "", "",  # all empty until parser derives them

                # Role data
                billing_order,
                role_type,  # lead / supporting / minor
                "",  # prominence_score derived in parser

                # Qualitative
                "", "",  # sympathy_coding, arc_quality
            ])


        print(f"Done: {title} — {len(cast)} cast members")