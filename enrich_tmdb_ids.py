"""
Enriches logos.json with TMDB production company IDs.

Modes:
  Local backfill (default):
      python enrich_tmdb_ids.py
      - Processes all entries with a null/missing TMDB ID
      - Saves progress every 100 entries
      - Writes tmdb_confidence_report.csv
      - Auto commits and pushes logos.json when done

  Workflow mode (called by GitHub Actions):
      python enrich_tmdb_ids.py --files added_files.txt
      - Only processes the filenames listed in added_files.txt
      - No git push (the workflow handles committing)
"""

import argparse
import csv
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from difflib import SequenceMatcher

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# --- Args ---
parser = argparse.ArgumentParser()
parser.add_argument("--files", help="File containing newline-separated filenames to process (workflow mode)")
args = parser.parse_args()

workflow_mode = args.files is not None

# --- Load .env (ignored in workflow mode — key comes from env secret) ---
if os.path.exists(".env"):
    with open(".env") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

TMDB_API_KEY = os.environ.get("TMDB_API_KEY", "")
if not TMDB_API_KEY:
    print("ERROR: TMDB_API_KEY not set. Add it to a .env file:\n  TMDB_API_KEY=your_key_here")
    sys.exit(1)

INDEX_FILE = "logos.json"
CONFIDENCE_REPORT = "tmdb_confidence_report.csv"
SAVE_EVERY = 100
RATE_LIMIT_DELAY = 0.27  # ~37 req/10s, safely under TMDB's 40/10s limit
MIN_SCORE = 0.6           # Below this threshold the match is rejected (id stays null)


def similarity(a, b):
    a_clean = a.lower().strip()
    b_clean = b.lower().strip()

    full_ratio = SequenceMatcher(None, a_clean, b_clean).ratio()

    # Boost when the query is a clean prefix of the result (e.g. "2929" → "2929 Productions")
    shorter, longer = (a_clean, b_clean) if len(a_clean) <= len(b_clean) else (b_clean, a_clean)
    if longer.startswith(shorter) and (len(longer) == len(shorter) or longer[len(shorter)] == " "):
        return max(full_ratio, 0.85)

    return full_ratio


def search_company(name):
    query = urllib.parse.quote(name)
    url = f"https://api.themoviedb.org/3/search/company?api_key={TMDB_API_KEY}&query={query}"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())
            results = data.get("results", [])
            if results:
                return results[0]
    except urllib.error.HTTPError as e:
        if e.code == 429:
            print("  Rate limited — waiting 10s...")
            time.sleep(10)
            return search_company(name)  # retry once
        print(f"  HTTP {e.code} for '{name}'")
    except Exception as e:
        print(f"  ERROR for '{name}': {e}")
    return None


# --- Load index ---
with open(INDEX_FILE, encoding="utf-8") as f:
    entries = json.load(f)

# Build a lookup by filename for fast access
entry_by_name = {e["name"]: e for e in entries}

# --- Determine which entries to process ---
if workflow_mode:
    with open(args.files, encoding="utf-8") as f:
        new_filenames = {line.strip() for line in f if line.strip()}
    to_process = [e for e in entries if e["name"] in new_filenames]
    print(f"Workflow mode: {len(to_process)} newly added file(s) to enrich")
else:
    to_process = [e for e in entries if "tmdb_production_company_id" not in e or e["tmdb_production_company_id"] is None]
    print(f"Backfill mode")
    print(f"Total entries : {len(entries)}")
    print(f"To process    : {len(to_process)}")
    print(f"Already filled: {len(entries) - len(to_process)}")

print()

if not to_process:
    print("Nothing to do.")
    sys.exit(0)

# --- Enrich ---
confidence_log = []
processed = 0

for entry in to_process:
    name = os.path.splitext(entry["name"])[0]  # strip extension
    result = search_company(name)

    if result:
        score = similarity(name, result["name"])
        accepted = score >= MIN_SCORE
        entry["tmdb_production_company_id"] = result["id"] if accepted else None
        confidence_log.append({
            "score": round(score, 4),
            "accepted": accepted,
            "file_name": entry["name"],
            "query": name,
            "tmdb_name": result["name"],
            "tmdb_id": result["id"] if accepted else None,
        })
        status = "✓" if accepted else f"✗ below {MIN_SCORE}"
        print(f"  [{processed + 1}/{len(to_process)}] {name} → {result['name']}  (id={result['id']}, score={score:.2f}) {status}")
    else:
        entry["tmdb_production_company_id"] = None
        confidence_log.append({
            "score": 0.0,
            "accepted": False,
            "file_name": entry["name"],
            "query": name,
            "tmdb_name": "",
            "tmdb_id": None,
        })
        print(f"  [{processed + 1}/{len(to_process)}] {name} → no match")

    processed += 1

    if not workflow_mode and processed % SAVE_EVERY == 0:
        with open(INDEX_FILE, "w", encoding="utf-8") as f:
            json.dump(entries, f, indent=2, ensure_ascii=False)
        print(f"  [checkpoint] {processed}/{len(to_process)} saved\n")

    time.sleep(RATE_LIMIT_DELAY)

# --- Final save ---
with open(INDEX_FILE, "w", encoding="utf-8") as f:
    json.dump(entries, f, indent=2, ensure_ascii=False)
print(f"\nSaved {INDEX_FILE}")

# --- Confidence report (local mode only, sorted least confident first) ---
if not workflow_mode:
    confidence_log.sort(key=lambda x: x["score"])
    with open(CONFIDENCE_REPORT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["score", "accepted", "file_name", "query", "tmdb_name", "tmdb_id"])
        writer.writeheader()
        writer.writerows(confidence_log)
    print(f"Saved {CONFIDENCE_REPORT}")

    # --- Git commit and push (local mode only) ---
    print("\nPushing updated index to GitHub...")
    try:
        subprocess.run(["git", "add", INDEX_FILE], check=True)
        subprocess.run(["git", "commit", "-m", f"Enrich logos.json with TMDB IDs ({processed} entries)"], check=True)
        subprocess.run(["git", "push"], check=True)
        print("Pushed.")
    except subprocess.CalledProcessError as e:
        print(f"Git error: {e}\nYou may need to push manually.")

print(f"\nDone. {processed} entries processed.")
