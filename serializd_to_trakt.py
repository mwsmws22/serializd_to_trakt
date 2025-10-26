import argparse
import http.client
import json


def login_to_serializd(email: str, password: str) -> str:
    """Log in to Serializd and return the authentication token."""
    conn = http.client.HTTPSConnection("www.serializd.com")
    payload = json.dumps({"email": email, "password": password})
    headers = {
        "accept": "application/json",
        "x-requested-with": "serializd_vercel",
        "Content-Type": "text/plain",
    }
    conn.request("POST", "/api/login", payload, headers)
    res = conn.getresponse()
    data = json.loads(res.read().decode("utf-8"))
    return data["token"]


def fetch_shows(token: str) -> tuple:
    """
    Fetch the user's show lists (watched and watchlist) using the authentication token.
    """
    conn = http.client.HTTPSConnection("www.serializd.com")
    headers = {
        "accept": "application/json",
        "x-requested-with": "serializd_vercel",
        "Cookie": f"tvproject_credentials={token}",
    }
    conn.request("GET", "/api/user_information?shouldGetUserContext=true", "", headers)
    res = conn.getresponse()
    data = json.loads(res.read().decode("utf-8"))
    context = data.get("context", {})

    watched = set()
    watchlist = {}
    for lst, seasons in context.items():
        if lst in ["watched", "currentlyWatching", "droppedShows", "pausedShows"]:
            watched.update({season["showId"] for season in seasons})
        if lst == "watchlist":
            for season in seasons:
                if season["showId"] not in watchlist:
                    watchlist[season["showId"]] = set()
                watchlist[season["showId"]].add(season["dateAdded"])
            for show_id, dates in watchlist.items():
                if len(dates) > 1:
                    print(
                        f"Multiple dateAdded values for showId {show_id} in watchlist. "
                        f"Using the oldest date {min(dates)}."
                    )
                watchlist[show_id] = min(dates)
    return watched, watchlist


def fetch_show_seasons(show_id: int) -> tuple:
    """Fetch the seasons of a show using generic show endpoint."""
    conn = http.client.HTTPSConnection("www.serializd.com")
    headers = {
        "accept": "application/json",
        "x-requested-with": "serializd_vercel",
    }
    endpoint = f"/api/show/{show_id}"
    conn.request("GET", endpoint, "", headers)
    res = conn.getresponse()
    data = json.loads(res.read().decode("utf-8"))
    show_name = data.get("name")

    if not show_name:
        raise ValueError(f"Show name not found for show [id={show_id}]")

    show_seasons = data.get("seasons")

    if not show_seasons:
        raise ValueError(f"No seasons found for show [name={show_name}, id={show_id}]")

    return show_name, show_seasons


def fetch_episode_logs(show_id: int, season_id: int, token: str) -> list:
    """Fetch the episode logs for a specific show and season using the user's token."""
    conn = http.client.HTTPSConnection("www.serializd.com")
    headers = {
        "accept": "application/json",
        "x-requested-with": "serializd_vercel",
        "Cookie": f"tvproject_credentials={token}",
    }
    endpoint = f"/mobile/page/show/{show_id}/season_v2_part_3/0?season_id={season_id}"
    conn.request("GET", endpoint, "", headers)
    res = conn.getresponse()
    data = json.loads(res.read().decode("utf-8"))
    return data.get("episodeLogs", [])


def fetch_trakt_show_info(show_id: int, trakt_client_id: str) -> dict:
    """Fetch show information from Trakt API using TMDB ID."""
    endpoint = f"/search/tmdb/{show_id}?type=show"
    status, data = _make_trakt_request(endpoint, trakt_client_id)
    return {
        "slug": data[0]["show"]["ids"]["slug"],
        "id": data[0]["show"]["ids"]["trakt"],
    }


def _make_trakt_request(endpoint: str, trakt_client_id: str) -> tuple:
    """Helper function to make a request to the Trakt API."""
    conn = http.client.HTTPSConnection("api.trakt.tv")
    headers = {
        "trakt-api-key": trakt_client_id,
        "trakt-api-version": "2",
        "Content-Type": "application/json",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, "
            "like Gecko) Chrome/135.0.0.0 Safari/537.36"
        ),
    }
    conn.request("GET", endpoint, "", headers)
    res = conn.getresponse()

    if res.status == 200:
        data = json.loads(res.read().decode("utf-8"))
        return res.status, data

    return res.status, None


def fetch_season_info_trakt(show_slug: str, season_num: int, trakt_id: str) -> tuple:
    """Fetch season data from Trakt API using the provided slug."""
    endpoint = f"/shows/{show_slug}/seasons/{season_num}"
    return _make_trakt_request(endpoint, trakt_id)


def episode_num_to_trakt_id(
    season_num: int, trakt_id: str, show_name: str, show_slug: str
) -> dict:
    """Fetch episode IDs and metadata for a specific show and season from Trakt."""
    status, data = fetch_season_info_trakt(show_slug, season_num, trakt_id)
    if status != 200:
        print(
            f"Error fetching season [number={season_num}] for show "
            f"[name={show_name}, slug={show_slug}]: HTTP {status}"
        )
        return {}
    if not data:
        print(
            f"No episodes found for season [number={season_num}] of show "
            f"[name={show_name}]."
        )
        return {}
    return {
        episode["number"]: {
            "trakt_id": episode["ids"]["trakt"],
            "tvdb_id": episode["ids"]["tvdb"],
            "tmdb_id": episode["ids"]["tmdb"],
            "imdb_id": episode["ids"]["imdb"],
        }
        for episode in data
    }


def fetch_episodes(
    show_id: int,
    show_name: str,
    season: dict,
    token: str,
    trakt_id: str,
    show_slug: str,
) -> list:
    """Fetch all episodes for a specific show and season."""
    season_id = season["id"]
    season_name = season["name"]
    season_num = season["seasonNumber"]

    # Fetch episode logs and episode IDs from Trakt
    episode_logs = fetch_episode_logs(show_id, season_id, token)
    episode_ids = episode_num_to_trakt_id(season_num, trakt_id, show_name, show_slug)

    if not episode_ids:
        # If no IDs found, that could mean the season isn't released yet or an issue
        # with the Trakt API call. Regardless, should ignore in this case.
        return []

    enriched_episodes = []
    for episode in episode_logs:
        episode_number = episode["episodeNumber"]
        episode_id_data = episode_ids.get(episode_number)

        if not episode_id_data:
            print(
                f"Episode [number={episode_number}] not found for season "
                f"[name={season_name}, number={season_num}, id={season_id}] of "
                f"show [name={show_name}, id={show_id}]"
            )
        else:
            enriched_episodes.append(
                {
                    "showId": show_id,
                    "showName": show_name,
                    "seasonId": season_id,
                    "seasonName": season_name,
                    "seasonNumber": season_num,
                    "episodeNumber": episode_number,
                    "dateAdded": episode["dateAdded"],
                    **episode_id_data,
                }
            )
    return enriched_episodes


def fetch_all_episodes(show_ids: set, token: str, trakt_id: str) -> list:
    """Fetch all watched episodes (with metadata) for a set of show IDs."""
    all_episodes = []
    for show_id in show_ids:
        show_name, seasons = fetch_show_seasons(show_id)
        show_slug = fetch_trakt_show_info(show_id, trakt_id)["slug"]
        all_episodes += [
            episode
            for season in seasons
            for episode in fetch_episodes(
                show_id, show_name, season, token, trakt_id, show_slug
            )
        ]
    return all_episodes


def format_watched_for_trakt(watched_episodes: list) -> list:
    """Format watched episodes into Trakt-compatible JSON."""
    return [
        {
            "trakt_id": episode["trakt_id"],
            "watched_at": episode["dateAdded"],
            "type": "episode",
        }
        for episode in watched_episodes
    ]


def format_watchlist_for_trakt(watchlist: dict, trakt_client_id: str) -> list:
    """Format watchlisted shows into Trakt-compatible JSON."""
    return [
        {
            "trakt_id": fetch_trakt_show_info(show_id, trakt_client_id)["id"],
            "watchlisted_at": date_added,
            "type": "show",
        }
        for show_id, date_added in watchlist.items()
    ]


def main():
    """Main function to fetch and export TV show data from Serializd."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Fetch and enrich TV show data from Serializd."
    )
    parser.add_argument(
        "--serializd_email", required=True, help="Serializd account email"
    )
    parser.add_argument(
        "--serializd_password", required=True, help="Serializd account password"
    )
    parser.add_argument("--trakt_client_id", required=True, help="Trakt API client ID")
    args = parser.parse_args()

    # Step 1: Log in to Serializd
    token = login_to_serializd(args.serializd_email, args.serializd_password)

    # Step 2: Fetch account show lists
    watched, watchlist = fetch_shows(token)

    # Step 3: Enrich combined shows with season and episode-level details
    watched_episodes = fetch_all_episodes(watched, token, args.trakt_client_id)

    # Step 4: Format enriched data for Trakt
    watched_data = format_watched_for_trakt(watched_episodes)
    watchlist_data = format_watchlist_for_trakt(watchlist, args.trakt_client_id)

    # Step 5: Save Trakt-compatible JSON files
    with open("serializd_to_trakt_watched.json", mode="w", encoding="utf-8") as f:
        json.dump(watched_data, f, indent=4)

    with open("serializd_to_trakt_watchlist.json", mode="w", encoding="utf-8") as f:
        json.dump(watchlist_data, f, indent=4)

    print(
        f"{len(watched_episodes)} watched episodes from "
        f"{len({episode['showId'] for episode in watched_episodes})} shows "
        f"exported to serializd_to_trakt_watched.json"
    )
    print(
        f"{len(watchlist_data)} shows from watchlist exported to "
        f"serializd_to_trakt_watchlist.json"
    )


if __name__ == "__main__":
    main()
