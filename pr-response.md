# PR Response Doc — CineLog Watchlist Feature

## AI Usage
<!-- Fill in at the end — how you used AI tools during this project -->

## Comment 1 — Rename
**What I did:** I used VSCode's search to find uses of `save_to_watchlist`. I updated usages and corresponding imports. I also looked for usages of just `save` to ensure I didn't leave anything behind, and in that I identified the documentation using `save`-language which I changed to `add`-langauge.

**How I verified:** I invoked the add endpoint from the watchlist routes using:

``` 
curl -X POST http://localhost:5000/watchlist/1/add   -H "Content-Type: application/json"   -d '{"film_id": 1}'
```

And checked that it worked E2E.

## Comment 2 — Deduplication
**What I did:** Before implementing this, I looked at how `services/collection_service.py` already handles the same problem for collections: `add_to_collection()` checks for an existing `(user_id, film_id)` pair and raises `AlreadyInCollectionError`, which `routes/collection.py`'s `add_film` route catches and turns into a `409`. I mirrored that exact pattern for the watchlist: `add_to_watchlist()` in `services/watchlist_service.py` queries `WatchlistEntry.query.filter_by(user_id=user_id, film_id=film_id).first()` before creating a new entry, and if a match already exists, raises a new `AlreadyInWatchlistError` instead of silently creating a duplicate row. `routes/watchlist/watchlist.py`'s `add_film` route then catches `AlreadyInWatchlistError` the same way collection's route catches `AlreadyInCollectionError`, returning `409` with `{"error": "Film '<film_id>' is already in this user's watchlist"}`.

**How I verified:** I ran the same curl (adding the same `film_id` for the same `user_id`) twice — the first call returns `201` with the new entry, the second returns `409` with the error message above instead of a second row being created.

## Comment 3 — Missing test
**What I did:** I used Claude to mirror `test_add_to_collection_nonexistent_film_raises` from `tests/test_collection.py`, reusing the same `app`/`sample_user` fixture structure (in-memory SQLite, isolated per test), in a new file `tests/test_watchlist.py`. The new test, `test_add_to_watchlist_nonexistent_film_raises`, calls `add_to_watchlist()` with a fake UUID that doesn't correspond to any row in the `Film` table, and asserts that it raises `FilmNotFoundError` — the same edge case the collection test targets (a nonexistent `film_id`, not e.g. a missing `user_id` or a malformed UUID), just for the watchlist service instead of the collection service.

**How I verified:** I validated the test logic against the fixture pattern, then ran it with `pytest tests/test_watchlist.py -v` and confirmed it passed.

## Comment 4 — Default visibility
**My position:** I'm keeping `public=True` as the default for watchlist entries.

**Reasoning:** A watchlist is fundamentally different from a collection (films already watched) — it's a list of intent, and intent-to-watch is the kind of data that's valuable when it's visible to others. The behavior I'm optimizing for is social discovery: friends browsing each other's watchlists for "what should I watch next" recommendations, and the light social pressure of a visible watchlist nudging someone to actually watch what they said they wanted to. That only works if lists are public by default — if we default to private, the watchlist feature launches as a personal to-do list with zero network effect on day one, and visibility becomes an opt-in action almost nobody takes (defaults are sticky; the vast majority of users never change a boolean toggle buried in a settings screen). Given this app's collection feature already treats logged/watched films as shareable activity, a private-by-default watchlist would also be an inconsistent, surprising exception within the product rather than a deliberate privacy boundary.

**Tradeoff acknowledged:** The real cost of `public=True` is that it favors the platform's growth/engagement goals over the individual user's privacy-by-default expectation. A user adding films to their watchlist for embarrassing, sensitive, or simply personal reasons (a guilty-pleasure genre, films tied to a breakup, screening picks for a therapist-recommended list, etc.) is opted into visibility before they've made any affirmative choice, and most people don't audit privacy settings after signup. If we ever see evidence that users are surprised or upset that their watchlist was visible, that's a strong signal to flip the default — but absent that signal, I think the discovery/engagement upside for a nascent social feature outweighs the downside, given the field exists precisely so any individual user can flip it to private with one write.

## Comment 5 — Sort order
**My position:** I'm switching `get_watchlist()` from alphabetical (`Film.title.asc()`) to date-added, newest-first (`WatchlistEntry.date_added.desc()`), matching the maintainer's preference.

**Engagement with reviewer's point:** I agree, and I don't think this is a close call once I looked at it next to the collection feature. `get_collection()` already sorts newest-first by `date_added` (see `test_get_collection_returns_newest_first` in test_collection.py), precisely because a "recently logged" list is more useful sorted by recency than by title. A watchlist is even more recency-sensitive than a collection: it's a list of current intent, and the entries a user is most likely to act on *right now* are the ones they just added — whatever movie prompted them to open the app and add something is the one they're most likely to actually watch next. Alphabetical order actively works against that: a film added five minutes ago named "Zootopia" gets buried at the bottom, even though it's the freshest and most actionable entry. Alphabetical sort is a reasonable default for *browsing/searching* a large catalog (which is what `Film.query` in routes/films.py optimizes for), but it's the wrong default for a personal, intent-ordered list — and my original choice of `Film.title.asc()` was just inherited from copy-pasting the query shape rather than a deliberate call, which is exactly the kind of default the maintainer was right to push on.

The one place I'd flag as a real tradeoff: newest-first means a watchlist a user hasn't touched in months will have their oldest (possibly most-intended, "I've been meaning to watch this for a year") entries scrolled past everything recent. If that becomes a real pain point, a secondary user-facing sort toggle (recency vs. alphabetical vs. by-genre) would be a reasonable follow-up, but I don't think it should block this default.

**Bug found and fixed along the way:** Implementing/testing this surfaced a separate pre-existing bug — `get_watchlist()` calls `entry.film.to_dict()`, but unlike `Film.collection_entries = db.relationship("CollectionEntry", backref="film", ...)`, there was no equivalent `watchlist_entries` relationship on `Film` giving `WatchlistEntry` a `.film` backref. This meant `GET /watchlist/<user_id>` crashed with `AttributeError: 'WatchlistEntry' object has no attribute 'film'` on every call — sort order was unreachable code. I added `watchlist_entries = db.relationship("WatchlistEntry", backref="film", lazy=True)` to `Film` in models.py, mirroring the existing collection relationship exactly.

**How I verified:** Added `test_get_watchlist_returns_newest_first` to tests/test_watchlist.py, mirroring `test_get_collection_returns_newest_first`'s fixture/assertion structure — two films added to the watchlist out of alphabetical order relative to their `date_added` timestamps, asserting the more-recently-added one comes first. Ran the full suite (`pytest tests/ -v`): all 6 tests pass, including this new one and the pre-existing collection tests (confirming the `Film` model change didn't regress collection behavior).

**Stretch — second test:** This is a second test beyond the one required for Comment 3 (`test_add_to_watchlist_nonexistent_film_raises`), committed separately as `test: add test for watchlist newest-first ordering`. I deliberately chose "Alien" (1979) and "Blade Runner" (1982) as the two films specifically because their titles sort in the *opposite* order from their `date_added` timestamps — "Alien" added most recently, "Blade Runner" added five days earlier, but "Alien" alphabetically precedes "Blade Runner." That's the only kind of case that can actually distinguish the two sort orders: if a test used films whose title order and date order happened to agree, the assertion would pass under both the old (wrong) alphabetical code and the new (correct) date-based code, and wouldn't prove the fix does anything. Picking titles that disagree with recency order is what makes the test meaningful.

## Comment 6 — Rebase
**What conflicted:**
**How I resolved it:**
**How I verified no conflict remains:**

## PR Description
<!-- Written at the end — feature overview, design decisions, manual testing steps -->