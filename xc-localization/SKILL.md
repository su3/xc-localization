---
name: xc-localization
description: "Use this skill whenever working with Xcode localization and .xcstrings files. This includes: adding new languages to a project, translating missing strings, updating stale translations, auditing localization coverage, or handling any .xcstrings file (Localizable.xcstrings, InfoPlist.xcstrings, etc.). The skill uses bundled scripts for token-efficient workflows — never read full .xcstrings files into context. Trigger on any mention of localization, translation, .xcstrings, adding languages, or Internationalization (i18n) in Xcode projects."
---

# Xcode Localization Skill

## Overview

This skill handles Xcode project localization using `.xcstrings` files. The core principle is **token efficiency**: never read full `.xcstrings` files into context. Instead, use the bundled scripts to extract only untranslated entries, translate them, and write back surgically.

## Bundled Scripts

The skill includes two Python scripts in the `scripts/` directory:

| Script                    | Purpose                                                                 |
| ------------------------- | ----------------------------------------------------------------------- |
| `extract_untranslated.py` | Extracts only keys needing translation (skips `stale` and `translated`) |
| `apply_translations.py`   | Writes translations back, setting `state: "translated"`                 |

Always use these scripts — they are 5–20× more token-efficient than reading raw files.

---

## Workflow

### Step 1 — Extract untranslated entries

**Always run this first.** The script outputs a compact JSON work list.

```bash
# Basic usage
python3 scripts/extract_untranslated.py <path/to/file.xcstrings> <target_lang>

# With hint language for context (e.g., zh-Hans already translated)
python3 scripts/extract_untranslated.py <path/to/file.xcstrings> ja zh-Hans

# Save to file
python3 scripts/extract_untranslated.py Localizable.xcstrings ja > todo.json
```

**Output format** (`todo.json`):

```json
{
  "Save changes?": {
    "source": "Save changes?",
    "current_state": "needs_review",
    "ref_zh-Hans": "保存更改？"
  },
  "New feature title": {
    "source": "New feature title",
    "current_state": "missing"
  }
}
```

- `current_state: "missing"` → No localization block exists yet (insert from scratch)
- `current_state: "needs_review"` or `"new"` → Block exists, needs translation
- `ref_<lang>` → Existing translation for context (when hint languages provided)

---

### Step 2 — Translate

Read `todo.json` and translate each `source` value to the target language.

**Translation rules:**

- Use `source` as the authoritative text to translate
- Use `ref_<lang>` fields as tonal/contextual reference (not as translation source)
- Preserve format specifiers exactly: `%@`, `%d`, `%1$@`, `\n`
- Keep proper nouns, brand names, URLs as-is
- Output flat JSON: `{ "key": "translated value", ... }`

**Example output** (`translations.json`):

```json
{
  "Cancel": "キャンセル",
  "Save changes?": "変更を保存しますか？",
  "Hello, %@!": "こんにちは、%@！"
}
```

---

### Step 3 — Write translations back

```bash
python3 scripts/apply_translations.py <path/to/file.xcstrings> <target_lang> translations.json
```

The script:

- Creates a timestamped backup automatically (e.g., `Localizable.xcstrings.bak.20260702143800`)
- Inserts/updates `localizations.<target>.stringUnit` with `state: "translated"`
- Preserves Xcode's 2-space JSON formatting

> **⚠️ Clean up backup files** — After all languages are applied, remove `.bak` files:
>
> ```bash
> rm -v <path/to/*.xcstrings.bak.*>
> ```
>
> Each `apply_translations.py` call creates one backup. Multiple runs produce multiple `.bak` files. They are safe to delete once you've verified the main `.xcstrings` file is correct.

---

### Step 4 — Verify

Run extraction again to confirm zero remaining keys:

```bash
python3 scripts/extract_untranslated.py <path/to/file.xcstrings> <target_lang>
# Expected output: {}
```

---

## Multiple Languages / Multiple Files

**Multiple target languages:** Repeat Steps 1–4 for each language.

**Multiple `.xcstrings` files:** Process each file independently:

```bash
for f in path/to/*.xcstrings; do
    python3 scripts/extract_untranslated.py "$f" ja > "todo_$(basename $f .xcstrings).json"
done
```

---

## Adding a New Language (Large Files)

When adding a language with no existing translations (all keys are "missing"), batch for large files:

```bash
# Extract and split into batches of ~100 keys
python3 scripts/extract_untranslated.py Localizable.xcstrings ko | \
  python3 -c "
import json,sys
d=json.load(sys.stdin)
items=list(d.items())
size=100
for i in range(0,len(items),size):
    batch=dict(items[i:i+size])
    with open(f'batch_{i//size}.json','w') as f:
        json.dump(batch,f,ensure_ascii=False,indent=2)
print(f'Created {-(-len(items)//size)} batch files')
"
```

---

## Reference: .xcstrings Structure

```jsonc
{
  "sourceLanguage": "en",
  "strings": {
    // Normal key
    "Some key": {
      "localizations": {
        "en": { "stringUnit": { "state": "translated", "value": "Some key" } },
        "ja": { "stringUnit": { "state": "needs_review", "value": "" } }
      }
    },
    // New key — no localizations yet (key itself is source)
    "New feature title": {},
    // Stale key — SKIP (developer handles in Xcode)
    "Old string": {
      "extractionState": "stale",
      "localizations": { ... }
    },
    // Non-translatable key — SKIP entirely
    "AudioKit:": {
      "shouldTranslate": false
    }
  },
  "version": "1.0"
}
```

**Top-level key fields:**
| Field | Action |
|-------|--------|
| `shouldTranslate: false` | ⛔ Skip entirely — app-internal key, not for translation |
| `extractionState: "stale"` | ⛔ Skip entirely — source changed, developer resolves |
| `extractionState: "manual"` | Process normally — manually added key |
| _(neither present)_ | Process normally |

**`stringUnit.state` values:**
| Value | Action |
|-------|--------|
| `translated` | ✅ Skip — already done |
| `needs_review` | ⚠️ Translate |
| `new` | 🆕 Translate |
| _(language absent)_ | ❌ Insert from scratch |

---

## Common Language Codes

| Language            | Code      |
| ------------------- | --------- |
| Japanese            | `ja`      |
| Korean              | `ko`      |
| Simplified Chinese  | `zh-Hans` |
| Traditional Chinese | `zh-Hant` |
| French              | `fr`      |
| German              | `de`      |
| Spanish             | `es`      |
| Portuguese (Brazil) | `pt-BR`   |
| Arabic              | `ar`      |
| Russian             | `ru`      |

---

## Token Budget Guidelines

| File Size     | Strategy                               |
| ------------- | -------------------------------------- |
| < 500 keys    | Extract → translate all in one pass    |
| 500–2000 keys | Extract → translate in batches of ~150 |
| 2000+ keys    | Extract → batch by 100, file-by-file   |

**Never read raw `.xcstrings` into context.** The extraction script output is typically 5–20× smaller.

---

## Troubleshooting

**`json.JSONDecodeError`** — Check file encoding:

```bash
file Localizable.xcstrings  # Should be UTF-8
```

**Keys revert after Xcode build** — Ensure "Use Compiler to Extract Swift Strings" is configured. Translations persist as long as `state: "translated"` is set (this workflow always does).

**Format specifier order** — If translation changes argument order, use positional specifiers (`%1$@`, `%2$@`) and note this in the translation task.

**Leftover `.xcstrings.bak.*` files** — `apply_translations.py` creates a backup on every run. Check for and clean up old `.bak` files before starting a fresh localization pass:

```bash
ls -la path/to/*.xcstrings.bak.*  # List any backups
rm path/to/*.xcstrings.bak.*      # Remove when no longer needed
```

The script uses timestamped names (e.g., `Localizable.xcstrings.bak.20260702143800`), so multiple runs produce multiple backups — check before you start a new session.
