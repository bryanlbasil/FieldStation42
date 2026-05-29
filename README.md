# Guide Movie Metadata Experimental Branch
This branch is for testing purposes only and might not be actively maintained.

This is an experimental FieldStation42 branch that adds movie metadata to the web guide. 

It can detect configured movie tags in your regular catalog, color movie blocks red in the guide, and show TMDB metadata such as rating, year, cast, and description. MPAA rating icons are included in the branch. If an icon is missing or removed, the guide will fall back to text when possible.

This is intended for the **web guide**, not the classic guide.

This branch also adds continuation arrows to the web guide.

---

## Install

From your FieldStation42 folder:

```bash
cd ~/FieldStation42
git fetch https://github.com/bryanlbasil/FieldStation42.git feature/guide-movie-metadata
git checkout -b feature/guide-movie-metadata FETCH_HEAD
```

---

## Configure `main_config.json`

This branch requires a TMDB API key in `confs/main_config.json`:

```json
"tmdb_api_key": "YOUR_TMDB_API_KEY_HERE"
```

You also need to tell the guide which tags should be treated as movies:

```json
"guide_metadata": {
  "movie_tags": {
    "*": ["movie", "movies"],
    "CINE": ["movie", "movies", "action", "comedy", "drama", "thriller", "horror", "romance", "scifi"],
    "DISN": ["dcom"],
    "VH1": ["moviesthatrock"]
  }
}
```

The `*` entry applies to all stations. Station-specific entries only apply to that station.

For example, this means any station using `movie` or `movies` will be detected:

```json
"*": ["movie", "movies"]
```

And this means Cinemax/CINE can treat genre folders as movies:

```json
"CINE": ["movie", "movies", "action", "comedy", "drama", "thriller", "horror", "romance", "scifi"]
```

After editing, validate your JSON:

```bash
python3 -m json.tool confs/main_config.json >/dev/null && echo "main_config JSON is valid"
```

---

## How movie detection works

Movie detection is tag-based.

If a scheduled item has a tag listed in `guide_metadata.movie_tags`, the web guide treats it as a movie.

For example:

```text
catalog/CINE/action/Die Hard.mp4
```

can be treated as a movie if `action` is listed under `CINE`.

Cleaner file names will usually produce better TMDB matches.

Good:

```text
The Fifth Element.mp4
Greedy.mp4
127 Hours.mp4
```

Messier release-style names may work, but are more likely to produce bad matches.

---

## Rebuild and test

After configuring `main_config.json`, restart FieldStation42.

If needed, rebuild the affected station:

```bash
python3 station_42.py --rebuild_catalog CINE
python3 station_42.py --add_month CINE
```

Replace `CINE` with your station name.

You can check whether movie metadata is appearing through the schedule API:

```bash
curl -s "http://localhost:4242/schedules/CINE" \
  | python3 -m json.tool \
  | grep -A20 -B5 '"guide_nfo"'
```

If working, movie blocks should include fields like:

```json
"is_movie": true,
"guide_nfo": {
  "title": "The Fifth Element",
  "year": "1997",
  "rating": "PG-13",
  "cast": ["Bruce Willis", "Milla Jovovich"],
  "description": "...",
  "source": "tmdb"
}
```

Then open the web guide and check the result visually.

---
## Continuation arrows

If a program started before the visible guide window, the guide shows a left arrow. If a program continues past the visible guide window, the guide shows a right arrow.

```text
◀ Program Title
Program Title ▶
◀ Program Title ▶
```

These arrows are part of this branch and are rendered with Unicode arrow characters.

Note: You may have seen photos of my local setup. Those photos show additional experimental PNG arrow styling, including Prevue-style single/double arrow images, and support for inline closed captions icons, but those experiments are not included in this public branch.

---
## Revert and go back to normal FieldStation42

To return to the normal main branch:
If you cloned the main FieldStation42 repository normally, Shane's repo is probably your `origin` remote. 

```bash
cd ~/FieldStation42
git checkout main
git fetch origin
git pull origin main
```

If Git says the branch already exists or your remotes are set up differently, check:

```bash
git remote -v
```

Use whichever remote points to:

```text
https://github.com/shane-mason/FieldStation42.git
```

For example, if Shane's repo is called `upstream` on your system:

```bash
git checkout main
git fetch upstream
git pull upstream main
```

---

## Notes

This is experimental.

It currently focuses on movies in the web guide. TMDB metadata depends on title matching, so incorrect matches are possible. The visual styling may also need small CSS adjustments depending on your guide theme and display.

You may have seen photos of my local setup. Those photos show additional experimental text wrapping, dynamic block resizing, PNG arrow styling, and support for inline closed captions icons, but those experiments are not included in this public branch.
