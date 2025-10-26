# Serializd to Trakt Exporter

The `serializd_to_trakt.py` script allows you to export your watched episodes data
from [Serializd](https://www.serializd.com) and format it into a JSON file compatible with [Trakt](https://trakt.tv/).

## Features

- Log in to your Serializd account using your email and password.
- Fetch your watched episodes and watchlist from Serializd.
- Map shows and episodes to their corresponding Trakt IDs.
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

## Output

After running the script, two JSON files will be created in the current directory:

### 1) `serializd_to_trakt_watched.json`

Contains all watched episodes, including dropped and paused shows. Each episode is one entry.

```json
[
  {
    "trakt_id": 342400,
    "watched_at": "2023-10-01T03:41:43Z",
    "type": "episode"
  },
  {
    "trakt_id": 342401,
    "watched_at": "2023-10-01T03:41:43Z",
    "type": "episode"
  }
]
```

### 2) `serializd_to_trakt_watchlist.json`

Contains all shows in your watchlist. Each show is one entry.

```json
[
  {
    "trakt_id": 1267,
    "watchlisted_at": "2024-05-20T03:59:01Z",
    "type": "show"
  },
  {
    "trakt_id": 170649,
    "watchlisted_at": "2024-05-20T23:37:11Z",
    "type": "show"
  }
]
```

To import the above JSON files to Trakt, log into your account and [run the importer](https://trakt.tv/settings/data#import).
Choose JSON as your import option and drag and drop one of the files. Note that Trakt only supports one JSON file at a time.

## Notes

### Discrepancies Between Serializd and Trakt Episode Data

There are some discrepancies between Serializd API data and Trakt. Sometimes there are episodes that are logged but aren't
in the actual episode data. For example, for me Archer Season 14 had episodes 10 and 11 as logged, but there are only 9
episodes in that season. This is because the finale was split into three parts. At the time I recorded it a few years
ago, likely it was reflected that way in Serializd. Since then, TMDB probably combined the finale into a single
episode (S14E09). So these previously logged episodes 10 and 11 are no longer found and ignored. In this case the
script will warn:

```plaintext
Episode [number=10] not found for season [name=Season 14, number=14, id=341010] of show [name=Archer, id=10283]
Episode [number=11] not found for season [name=Season 14, number=14, id=341010] of show [name=Archer, id=10283]
```

### Seasons Without Episodes

There are some seasons without episodes. This is typically when a season is announced, but there is no info on how
many episodes there will be. In this case the script will warn:

```plaintext
No episodes found for season [number=2] of show [name=Sweetpea]
```

### Missing Shows in Serializd Account

Unfortunately, Serializd only associates a show if...

1) You've marked at least one season as watched **OR**
2) You've marked the show as dropped or paused

Albeit an outlier case, but if you only mark individual episodes as watched (no seasons), and do not mark the show as dropped or paused, 
then that show will not appear in your Serializd account data, and so this script will not be able to capture those episodes.

### Ratings Support

This script does not support ratings. I don't rate my shows, so this feature wasn't applicable to me. If anyone wants
to add it, you're more than welcome to submit a PR.

## Contributing

Contributions are welcome! Feel free to open an issue or submit a pull request if you have suggestions or improvements.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Disclaimer

This script is not affiliated with or endorsed by Serializd or Trakt. Use it at your own risk.
