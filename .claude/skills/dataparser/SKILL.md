---
name: dataparser
description: Use this skill when the user wants to compress, deduplicate, or extract repeated patterns from a large file of whitespace-separated numbers. Trigger on requests like "find patterns in numbers file", "compress number sequence file", "extract repeating templates from <path>", or "parse patterns out of <file>". Runs the bundled Python CLI and reports compression stats.
argument-hint: "<file-path> [--decode] [--batch-size N] [--max-passes N] [--min-len N] [--max-len N] [--out-dir <dir>]"
---

# Arguments
- $ARGUMENTS - file path and optional flags (if empty, ask the user). Pass `--decode` to decode an `.encoded.txt` file back to numbers.


# dataparser skill

Compress a large whitespace-separated number file by finding and replacing repeated sequences with reference tokens.

## When to use
- User provides a path to a file of numbers (integers, up to 2 decimal places, whitespace-separated)
- User wants to find/extract repeating number patterns
- User wants to compress or deduplicate number sequences

## How to run

If `$ARGUMENTS` is empty, ask the user to provide a file path.

**Encode (compress):**
```bash
python .claude/skills/dataparser/scripts/cli.py encode <file> [--batch-size 5000] [--max-passes 10] [--min-len 2] [--max-len 15] [--out-dir <dir>]
```

Outputs:
- `<stem>.encoded.txt` — token stream with `$id` references replacing repeated patterns
- `<stem>.patterns.txt` — dictionary: `id<TAB>token token ...` per line

**Decode in place** (when `--decode` is passed or `$ARGUMENTS` contains `--decode`):
```bash
python .claude/skills/dataparser/scripts/cli.py encode <stem>.encoded.txt --decode [--out-dir <dir>]
```

The patterns file is discovered automatically as `<stem>.patterns.txt` in the same directory. Output is written to `<stem>.decoded.txt`.

## What to report back
After encoding, read the final `.patterns.txt` and report:
- Number of unique patterns found
- Top 5 most-used patterns (id, sequence, usage count)
- Memory saving (original file bytes vs combined encoded + patterns file bytes) — the headline figure
- Token ratio (original token count vs encoded token count) — secondary
- Number of passes actually run (may be fewer than `--max-passes` if no changes found)
