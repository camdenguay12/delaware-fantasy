# Delaware Fantasy

Public 2026 fantasy football dashboard for ESPN league 562354279.

## Deployment
1. Open Settings → Pages and choose Deploy from a branch, main, root.
2. Open Actions → ESPN Data Sync → Run workflow to attempt an initial data import.
3. ESPN scores are refreshed by a scheduled job approximately every 15 minutes (not guaranteed to-the-second live).
4. Commissioner rankings remain empty until their Google Doc is available; `data/rankings.json` accepts objects with `rank`, `teamName`, `previousRank`, `writeup`.

Projection history begins on the first successful sync; no historical values or win probabilities are fabricated. ESPN API is unofficial and may change.
