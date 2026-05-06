import requests
import csv
import time

API_KEY  = "3a7bea432386c9c51eb03cccfe4ed094"
BASE_URL = "https://api.themoviedb.org/3"

OUTPUT_FILE = "raw_cast_data_v2.csv"
PAGES = 15   # 20 titles per page
MAX_CAST = 20   # billing cutoff per title
COUNTRY = "US" # US productions only


# Search for titles
def get_popular_titles(media_type, pages=PAGES):
    """
    Pull the titles from the TMDB popular page, taking only US productions.
    Returns a list of TMDB IDs.
    """
    ids = []
    for page in range(1, pages + 1):
        url = f"{BASE_URL}/discover/{media_type}"
        params = {
            "api_key":              API_KEY,
            "sort_by":              "popularity.desc",
            "with_origin_country":  COUNTRY,
            "page":                 page
        }
        response = requests.get(url, params=params)
        results = response.json().get("results", [])
        ids.extend([r["id"] for r in results])
        time.sleep(0.25)

    print(f"Found {len(ids)} {media_type} titles")
    return ids


# pull metadata for IDs
def get_metadata(tmdb_id, media_type):
    url = f"{BASE_URL}/{media_type}/{tmdb_id}"
    params = {"api_key": API_KEY}
    response = requests.get(url, params=params)
    data = response.json()

    title = data.get("title") if media_type == "movie" else data.get("name")

    if media_type == "movie":
        start_year = data.get("release_date", "")[:4]
        end_year = start_year
    else:
        start_year = data.get("first_air_date", "")[:4]
        end_year = data.get("last_air_date",  "")[:4]

    genres = [g["name"] for g in data.get("genres", [])]

    # filter out potential non-US results
    origin_countries = data.get("origin_country", [])
    is_us = COUNTRY in origin_countries

    return title, start_year, end_year, genres, is_us


# get credits
def get_credits(tmdb_id, media_type):
    url = f"{BASE_URL}/{media_type}/{tmdb_id}/credits"
    params = {"api_key": API_KEY}
    response = requests.get(url, params=params)
    return response.json().get("cast", [])


# write CSV

def write_csv(movie_ids, tv_ids):
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            # Title-level
            "title", "start_year", "end_year", "genres", "tmdb_id", "media_type",

            # Actor-level
            "actor_name", "actor_tmdb_id", "actor_gender_code",
            "actor_ethnicity", # OpenAI annotation
            "actor_age_at_release", # manual

            # Character-level
            "character_name",
            "character_gender", # manual
            "character_ethnicity", # manual

            # Mismatch flags
            "gender_mismatch",
            "ethnicity_mismatch",

            # Role data
            "billing_order",
            "role_type",
            "prominence_score", # derived in parser

            # Qualitative (Week 7)
            "sympathy_coding",
            "arc_quality",
        ])

        all_titles = [("movie", mid) for mid in movie_ids] + \
                     [("tv", tid) for tid in tv_ids]

        skipped = 0
        for media_type, tmdb_id in all_titles:
            try:
                title, start_year, end_year, genres, is_us = get_metadata(tmdb_id, media_type)

                if not is_us: # skip is non US
                    skipped += 1
                    continue

                if not title: # skip if no title
                    skipped += 1
                    continue

                cast = get_credits(tmdb_id, media_type)
                time.sleep(0.25)

                written = 0
                for member in cast:
                    raw_order = member.get("order", 0)

                    # cast cutoff
                    if raw_order >= MAX_CAST:
                        continue

                    billing_order = raw_order + 1

                    if billing_order <= 3:
                        role_type = "lead"
                    elif billing_order <= 10:
                        role_type = "supporting"
                    else:
                        role_type = "minor"

                    writer.writerow([
                        # title-level
                        title, start_year, end_year,
                        "|".join(genres), tmdb_id, media_type,

                        # actor-level
                        member.get("name"),
                        member.get("id"),
                        member.get("gender"),
                        "", "",  # ethnicity , age

                        # character-level
                        member.get("character"),
                        "", "",  # character demographics

                        # mismatch flags
                        "", "",

                        # Role data
                        billing_order,
                        role_type,
                        "",  # prominence score derived in parser

                        # qualitative
                        "", "",
                    ])
                    written += 1

                print(f"{title} ({start_year}) — {written} cast members")

            except Exception as e:
                print(f"Error on {media_type} ID {tmdb_id}: {e}")
                skipped += 1
                continue

        print(f"\nDone. Skipped {skipped} titles (non-US or missing data)")



if __name__ == "__main__":
    print("Fetching movies...")
    movie_ids = get_popular_titles("movie", pages=PAGES)

    print("\nFetching TV shows...")
    tv_ids = get_popular_titles("tv", pages=PAGES)

    print(f"\nWriting file for {len(movie_ids)} movies, {len(tv_ids)} TV shows...")
    write_csv(movie_ids, tv_ids)

    print(f"\nOutput saved to {OUTPUT_FILE}")