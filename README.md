# Serializd to Trakt Exporter

The `serializd_to_trakt.py` script allows you to export your watched episodes data
from [Serializd](https://www.serializd.com) and format it into a JSON file compatible with [Trakt](https://trakt.tv/).

## Features

- Log in to your Serializd account using your email and password.
- Fetch your watched episodes and watchlist from Serializd.
- Enrich the data with season and episode-level details.
- Format the data into a Trakt-compatible JSON file.
- Save the exported data locally for easy import into Trakt.

## Usage

Run the script using the following command:

```bash
python serializd_to_trakt.py --serializd_email <your_email> --serializd_password <your_password> --trakt_client_id <your_trakt_client_id>
```

### Arguments

- `--serializd_email`: Your Serializd account email address.
- `--serializd_password`: Your Serializd account password.
- `--trakt_client_id`: Your Trakt API client ID. You can obtain this from
  your [Trakt API settings](https://trakt.tv/oauth/applications).

### Example

```bash
python serializd_to_trakt.py --serializd_email user@example.com --serializd_password mypassword123 --trakt_client_id 4aa6e37d-0a34-4a5d-9018-1342d070f994
```

After running the script, a file named `serializd_watched_data.json` will be created in the current directory. This file
contains your watched episodes in a format compatible with Trakt.

## Output

The output JSON file will look like this:

```json
[
  {
    "tvdb_id": 12345,
    "watched_at": "2023-01-01T12:00:00Z"
  },
  {
    "tvdb_id": 67890,
    "watched_at": "2023-01-02T15:30:00Z"
  }
]
```

To upload this JSON file to Trakt, log into your account and [run the importer](https://trakt.tv/settings/data#import).
Choose JSON as your import option and upload the file produced by this cript.

## Limitation of Trakt JSON Importer

### TODO - Finish this section

- The script currently does **not** support exporting watchlist data to Trakt because Trakt does not allow importing
  watchlist items by show, only by episode.
    - If this ever changes, the script is ready to go, you just need to enable the line in `format_for_trakt`
    - Frankly, I can't understand why anyone would want to add a show to their watchlist on an episode-by-episode basis.
      This makes sense for history, but not in the context of one's watchlist.

## Notes

- There are some descrepencies between Serializd APIs. Sometimes there are episodes that are logged but aren't in the
  actual episode data. For example, for me Archer Season 14 had episodes 10 and 11 as logged, but there are only 9
  episodes in that season. This is because the finale was split into three parts. At the time I recorded it a few years
  ago, likely it was reflected that way in Serializd. Since then, TMDB probably combined the finale into a single
  episode (S14E09). So these previously logged episdoes 10 and 11 are no longer found and ingored. In this case the
  script will warn:
  ```plaintext
  Episode [number=10] not found for show [name=Archer, id=10283] and season [name=Season 14, number=14, id=341010]
  ```
- There are some seasons without episodes. This is typically when a season is announced, but no there is no info on how
  many episodes there will be. In this case the script will warn:
  ```plaintext
  No episodes found for season [number=8] of show [name=Rick and Morty, id=60625]
  ```
- If a season is not found (HTTP 404), the script will warn:
  ```plaintext
  Season [number=1] not found for show [name=Giri/Haji, id=94659]. Check show_name_slug 'Giri/Haji'
  ```
  This typically due to the formatting of the show name in the API endpoint (refered to as the 'slug'). Requires
  substituting certain special characters like `space` with `-` dash (e.g., `Breaking-Bad`). In the example above,
  the issue with the `/` which needs to be replaced with `%2F`.
- Unfortunately, Serializd only associates a show with your account if 1) you've marked at least one season as watched
  or 2) you've marked the show as dropped or paused. Albeit an outlier case, but if you mark only one or two episode
  as watched, but do not mark the show as dropped or paused, then that show will not appear in your Serializd account
  data, and so this script will not be able to capture those episodes.
- This script does not support ratings. I don't rate my shows, so this feature wasn't applicable to me. If anyone wants
  to add it, you're more than welcome to submit a PR.

## Contributing

Contributions are welcome! Feel free to open an issue or submit a pull request if you have suggestions or improvements.

## License

This project is licensed under the MIT License. See the [LICENSE](../LICENSE) file for details.

## Disclaimer

This script is not affiliated with or endorsed by Serializd or Trakt. Use it at your own risk.
