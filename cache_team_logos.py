"""Cache ESPN custom fantasy team logos locally so browser restrictions cannot hide them."""
import json
import pathlib
import urllib.request
import urllib.error

ROOT = pathlib.Path(__file__).resolve().parent
DATA = ROOT / "data" / "league.json"
OUT = ROOT / "assets" / "team-logos"
OUT.mkdir(parents=True, exist_ok=True)

def main():
    league = json.loads(DATA.read_text(encoding="utf-8"))
    count = 0
    for team in league.get("teams", []):
        url = team.get("logo", "")
        if "mystique-api.fantasy.espn.com/" not in url:
            continue
        target = OUT / ("team-" + str(team["id"]) + ".png")
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (compatible; DelawareFantasy/1.0)",
                "Accept": "image/avif,image/webp,image/png,image/jpeg,image/*;q=0.8",
                "Referer": "https://fantasy.espn.com/",
            })
            with urllib.request.urlopen(req, timeout=20) as resp:
                blob = resp.read(5_000_001)
                typ = resp.headers.get("Content-Type", "").lower()
            if len(blob) > 5_000_000 or len(blob) < 100 or not typ.startswith("image/"):
                raise ValueError("Unexpected image response: " + typ)
            if blob.startswith(b"\x89PNG\\r\\n\\x1a\\n"):
                ext = ".png"
            elif blob.startswith(b"\xff\\xd8\\xff"):
                ext = ".jpg"
            elif blob.startswith(b"RIFF") and blob[8:12] == b"WEBP":
                ext = ".webp"
            else:
                raise ValueError("Unsupported image format")
            target = target.with_suffix(ext)
            target.write_bytes(blob)
            team["logo"] = "assets/team-logos/" + target.name
            count += 1
        except (OSError, ValueError, urllib.error.URLError) as exc:
            print("Custom logo download failed for", team["name"], ":", exc)
            for ext in (".png", ".jpg", ".webp"):
                existing = target.with_suffix(ext)
                if existing.exists() and existing.stat().st_size > 100:
                    team["logo"] = "assets/team-logos/" + existing.name
                    print("Using previously cached image for", team["name"])
                    break
    DATA.write_text(json.dumps(league, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Cached", count, "custom team logos")

if __name__ == "__main__":
    main()
