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

New entries are appended. Existing entries are never modified (preserves date_added).
"""

import json
import os
import sys
from datetime import datetime, timezone

# Ensure stdout handles unicode (matters on Windows)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

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

    # Find new files
    new_entries = []
    for filename in sorted(os.listdir(folder)):
        if not os.path.isfile(os.path.join(folder, filename)):
            continue
        if filename in existing_names:
            continue
        new_entries.append({
            "name": filename,
            "url": f"{RAW_BASE}/{folder}/{filename}",
            "date_added": today
        })
        print(f"  [{folder}] + {filename}")

    if new_entries:
        updated = existing + new_entries
        with open(index_file, "w", encoding="utf-8") as f:
            json.dump(updated, f, indent=2, ensure_ascii=False)
        print(f"  {index_file}: added {len(new_entries)}, total {len(updated)}")
        total_new += len(new_entries)
    else:
        print(f"  {index_file}: up to date ({len(existing)} entries)")

print(f"\nDone. {total_new} new entries across all indexes.")
