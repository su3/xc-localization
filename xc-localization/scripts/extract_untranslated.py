#!/usr/bin/env python3
"""
extract_untranslated.py – Extract untranslated entries from .xcstrings files

Usage:
    python3 extract_untranslated.py Localizable.xcstrings ja [hint_lang ...]

Arguments:
    file_path   – Path to the .xcstrings file
    target      – Target language code (e.g., "ja", "zh-Hans", "ko")
    hint_langs  – Optional already-translated languages for context

Output:
    Compact JSON to stdout – feed this to Claude for translation
    Count written to stderr

Example:
    # Without hint languages
    python3 extract_untranslated.py path/to/Localizable.xcstrings ja > todo.json

    # With existing translation as context
    python3 extract_untranslated.py path/to/Localizable.xcstrings ja zh-Hans > todo.json
"""

import json
import sys


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 extract_untranslated.py <file> <target_lang> [hint_lang ...]", file=sys.stderr)
        sys.exit(1)

    file_path = sys.argv[1]
    target = sys.argv[2]
    hint_langs = sys.argv[3:]

    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)

    source_lang = data.get("sourceLanguage", "en")
    todo = {}

    for key, entry in data["strings"].items():
        # Skip stale keys — source string was changed/removed by developer
        if entry.get("extractionState") == "stale":
            continue

        # Skip keys marked as not translatable
        if entry.get("shouldTranslate") is False:
            continue

        locs = entry.get("localizations", {})
        tgt = locs.get(target, {})
        unit = tgt.get("stringUnit", {})

        # Skip if already translated
        if unit.get("state") == "translated":
            continue

        # Determine the reference (source) text
        src_unit = locs.get(source_lang, {}).get("stringUnit", {})
        ref_value = src_unit.get("value") or key

        record = {
            "source": ref_value,
            "current_state": unit.get("state", "missing"),
        }

        # Include existing translations from hint languages as context
        for lang in hint_langs:
            hint_unit = locs.get(lang, {}).get("stringUnit", {})
            hint_val = hint_unit.get("value", "")
            if hint_val:
                record[f"ref_{lang}"] = hint_val

        todo[key] = record

    print(json.dumps(todo, ensure_ascii=False, indent=2))
    print(f"Total keys to translate: {len(todo)}", file=sys.stderr)


if __name__ == "__main__":
    main()
