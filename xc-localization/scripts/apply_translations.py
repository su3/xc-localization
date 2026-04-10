#!/usr/bin/env python3
"""
apply_translations.py – Write translations back into .xcstrings files

Usage:
    python3 apply_translations.py <file> <target_lang> <translations.json>

Arguments:
    file_path     – Path to the .xcstrings file to update
    target        – Target language code (e.g., "ja", "zh-Hans", "ko")
    trans_path    – Path to translations.json produced by translation step

Output:
    Backup file created (preserves original)
    Count of applied/skipped translations written to stderr

Example:
    python3 apply_translations.py path/to/Localizable.xcstrings ja translations.json
"""

import json
import sys
import shutil
from datetime import datetime


def main():
    if len(sys.argv) < 4:
        print("Usage: python3 apply_translations.py <file> <target_lang> <translations.json>", file=sys.stderr)
        sys.exit(1)

    file_path = sys.argv[1]
    target = sys.argv[2]
    trans_path = sys.argv[3]

    # Safety: backup the original
    backup = file_path + ".bak." + datetime.now().strftime("%Y%m%d%H%M%S")
    shutil.copy2(file_path, backup)
    print(f"Backup: {backup}", file=sys.stderr)

    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)

    with open(trans_path, encoding="utf-8") as f:
        translations = json.load(f)

    applied = 0
    skipped = []

    for key, value in translations.items():
        if key not in data["strings"]:
            skipped.append(key)
            continue
        entry = data["strings"][key]
        locs = entry.setdefault("localizations", {})
        locs.setdefault(target, {})
        locs[target]["stringUnit"] = {
            "state": "translated",
            "value": value
        }
        applied += 1

    # Write back with same formatting style as Xcode (2-space indent, no BOM)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"Applied: {applied}, Skipped: {len(skipped)}", file=sys.stderr)
    if skipped:
        print(f"Skipped keys not found in file: {skipped}", file=sys.stderr)


if __name__ == "__main__":
    main()
