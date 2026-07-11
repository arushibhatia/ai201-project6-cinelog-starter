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
**My position:**
**Reasoning:**
**Engagement with reviewer's point:**

## Comment 6 — Rebase
**What conflicted:**
**How I resolved it:**
**How I verified no conflict remains:**

## PR Description
<!-- Written at the end — feature overview, design decisions, manual testing steps -->