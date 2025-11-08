import os
import re
from datetime import datetime

# 🔧 List your target folders here
target_folders = [
    r"C:\-   Ω\Ω1\1.          L1",
]

# 🕒 Generate timestamped log filename
timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
log_dir = r"A:\Logs"
log_file_path = os.path.join(log_dir, f"nfo_cleanup_log_{timestamp}.txt")

# 📄 Path to swap file
swap_file_path = r"A:\swap.txt"

# 🔁 Load genre swaps from swap.txt
def load_genre_swaps():
    swaps = {}
    if os.path.exists(swap_file_path):
        with open(swap_file_path, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split(",", 1)
                if len(parts) == 2:
                    x = parts[0].strip()
                    y = parts[1].strip()
                    swaps[x] = y  # y may be empty (null)
    return swaps

def initialize_log():
    os.makedirs(log_dir, exist_ok=True)
    with open(log_file_path, "w", encoding="utf-8") as log:
        log.write("NFO Cleanup Log\n" + "="*20 + f"\nStarted: {timestamp}\n")

def clean_nfo_content(content, genre_swaps):
    changes = []
    original_content = content

    # Step 1: Replace or remove <genre>x</genre>
    for x, y in genre_swaps.items():
        pattern = f"<genre>{re.escape(x)}</genre>"
        if re.search(pattern, content):
            if y:
                replacement = f"<genre>{y}</genre>"
                content = re.sub(pattern, replacement, content)
                changes.append(f"Swapped genre: '{x}' → '{y}'")
            else:
                content = re.sub(pattern, "", content)
                changes.append(f"Removed genre: '{x}'")

    # Step 2: Remove <tag>...</tag> blocks
    tag_pattern = re.compile(r"<tag>.*?</tag>", re.DOTALL)
    tag_matches = tag_pattern.findall(content)
    if tag_matches:
        content = tag_pattern.sub("", content)
        changes.append(f"Removed {len(tag_matches)} <tag> block(s)")

    # Step 3: Remove blank lines
    lines = content.splitlines()
    cleaned_lines = [line for line in lines if line.strip()]
    removed_blank_lines = len(lines) - len(cleaned_lines)
    if removed_blank_lines > 0:
        changes.append(f"Removed {removed_blank_lines} blank line(s)")

    return "\n".join(cleaned_lines), changes, original_content

def log_changes(file_path, changes, original_content, cleaned_content):
    with open(log_file_path, "a", encoding="utf-8") as log:
        timestamp_entry = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log.write(f"\n[{timestamp_entry}] Processed: {file_path}\n")
        if changes:
            for change in changes:
                log.write(f"  - {change}\n")
            log.write("  --- Original Content Preview ---\n")
            log.write("\n".join(original_content.splitlines()[:10]) + "\n")
            log.write("  --- Cleaned Content Preview ---\n")
            log.write("\n".join(cleaned_content.splitlines()[:10]) + "\n")
        else:
            log.write("  - No changes made\n")

def process_nfo_files(folder_list):
    initialize_log()
    genre_swaps = load_genre_swaps()
    for root_folder in folder_list:
        for dirpath, _, filenames in os.walk(root_folder):
            for filename in filenames:
                if filename.lower().endswith(".nfo"):
                    full_path = os.path.join(dirpath, filename)
                    try:
                        with open(full_path, "r", encoding="utf-8", errors="ignore") as file:
                            original_content = file.read()
                        cleaned_content, changes, original_snapshot = clean_nfo_content(original_content, genre_swaps)
                        if changes:
                            with open(full_path, "w", encoding="utf-8") as file:
                                file.write(cleaned_content)
                        log_changes(full_path, changes, original_snapshot, cleaned_content)
                        print(f"Processed: {full_path}")
                    except Exception as e:
                        print(f"Error processing {full_path}: {e}")

process_nfo_files(target_folders)