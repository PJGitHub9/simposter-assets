"""
Scans folders listed in asset-list.txt and creates/updates per-folder JSON indexes.

Each folder gets its own <folder>.json file, e.g. logos -> logos.json.

Schema:
[
  {
    "name": "filename.png",
    "url": "https://raw.githubusercontent.com/...",
    "date_added": "YYYY-MM-DD"
  },
  ...
]

New entries are appended. Updated entries (passed via --updated) have their date_added refreshed.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

# Ensure stdout handles unicode (matters on Windows)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

parser = argparse.ArgumentParser()
parser.add_argument("--updated",      help="Newline-separated filenames that were overwritten upstream")
parser.add_argument("--placeholders", help="Newline-separated filenames that are placeholder images")
args = parser.parse_args()

def load_fileset(path):
    if path and os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return {line.strip() for line in f if line.strip()}
    return set()

updated_filenames     = load_fileset(args.updated)
placeholder_filenames = load_fileset(args.placeholders)

REPO = "PJGitHub9/simposter-assets"
BRANCH = "main"
RAW_BASE = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}"

ASSET_LIST = "asset-list.txt"

# --- Load folder list ---
folders = []
with open(ASSET_LIST) as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#"):
            folders.append(line)

# --- Process each folder independently ---
today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
total_new = 0
total_updated = 0

for folder in folders:
    if not os.path.isdir(folder):
        print(f"WARNING: folder '{folder}' not found, skipping.")
        continue

    index_file = f"{folder}.json"

    # Load existing index for this folder
    if os.path.exists(index_file):
        with open(index_file, encoding="utf-8") as f:
            existing = json.load(f)
    else:
        existing = []

    existing_names = {entry["name"] for entry in existing}
    changed = False

    # Refresh updated files — also fill URL if it was previously a placeholder
    for entry in existing:
        if entry["name"] in updated_filenames:
            entry["date_added"] = today
            if not entry.get("url"):
                entry["url"] = f"{RAW_BASE}/{folder}/{entry['name']}"
                print(f"  [{folder}] ^ {entry['name']} (placeholder → real logo, url filled)")
            else:
                print(f"  [{folder}] ~ {entry['name']} (updated)")
            total_updated += 1
            changed = True

    # Append new files
    new_entries = []
    for filename in sorted(os.listdir(folder)):
        if not os.path.isfile(os.path.join(folder, filename)):
            continue
        if filename in existing_names:
            continue
        is_placeholder = filename in placeholder_filenames
        new_entries.append({
            "name": filename,
            "url": None if is_placeholder else f"{RAW_BASE}/{folder}/{filename}",
            "date_added": today
        })
        label = "(placeholder)" if is_placeholder else ""
        print(f"  [{folder}] + {filename} {label}".strip())
        total_new += 1
        changed = True

    if changed:
        final = existing + new_entries
        with open(index_file, "w", encoding="utf-8") as f:
            json.dump(final, f, indent=2, ensure_ascii=False)
        print(f"  {index_file}: +{len(new_entries)} added, ~{sum(1 for e in existing if e['name'] in updated_filenames)} updated, {len(final)} total")
    else:
        print(f"  {index_file}: up to date ({len(existing)} entries)")

print(f"\nDone. {total_new} new, {total_updated} updated across all indexes.")
