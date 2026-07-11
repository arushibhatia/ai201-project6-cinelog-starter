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
**What I did:**
**How I verified:**

## Comment 3 — Missing test
**What I did:**
**How I verified:**

## Comment 4 — Default visibility
**My position:**
**Reasoning:**
**Tradeoff acknowledged:**

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