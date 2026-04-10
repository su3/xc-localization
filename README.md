# xc-localization

A Claude Code skill for efficient Xcode project localization.

## Overview

This skill handles `.xcstrings` file localization for Xcode projects. It uses a token-efficient workflow that extracts only untranslated entries rather than reading entire files into context.

## Installation

Copy the skill directory into Claude Code's skills folder.

**Global** (all projects):

```bash
cp -r xc-localization ~/.claude/skills/
```

**Project-level** (current project only):

```bash
cp -r xc-localization .claude/skills/
```

## Usage

Once installed, the skill triggers automatically when you mention:

- Localization or internationalization (i18n)
- `.xcstrings` files
- Adding new languages to Xcode projects
- Translating missing strings
- Localization coverage audits

### Example Prompts

- "Add Japanese localization to my Xcode project"
- "Translate the missing strings in Localizable.xcstrings to Korean"
- "How many untranslated keys do I have in InfoPlist.xcstrings for French?"
- "Update the Chinese translations that are marked for review"

## Requirements

- Python 3.6+ (no external dependencies)
