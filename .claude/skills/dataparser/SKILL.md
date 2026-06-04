---
name: dataparser
description: Use this skill when the user wants to compress, deduplicate, or extract repeated patterns from a large file of whitespace-separated numbers. Trigger on requests like "find patterns in numbers file", "compress number sequence file", "extract repeating templates from <path>", or "parse patterns out of <file>". Runs the bundled Python CLI and reports compression stats.
model: sonnet
argument-hint: <file-path>
---

# dataparser skill

Compress a large whitespace-separated number file by finding and replacing repeated sequences with reference tokens.

## When to use
- User provides a path to a file of numbers (integers, up to 2 decimal places, whitespace-separated)
- User wants to find/extract repeating number patterns
- User wants to compress or deduplicate number sequences

## How to run

The file path comes from `$ARGUMENTS` (the value passed after `/dataparser`).

```bash
python .claude/skills/dataparser/scripts/cli.py encode $ARGUMENTS [--batch-size 5000] [--max-passes 10] [--min-len 2] [--max-len 15] [--out-dir <dir>]
```

If `$ARGUMENTS` is empty, ask the user to provide a file path.

Outputs:
- `<input>.encoded.txt` — token stream with `$id` references replacing repeated patterns
- `<input>.patterns.txt` — dictionary: `id<TAB>token token ...` per line

To decode back to original:
```bash
python .claude/skills/dataparser/scripts/cli.py decode <encoded_file> <patterns_file> [-o <output_path>]
```

## What to report back
After encoding, read the final `.patterns.txt` and report:
- Number of unique patterns found
- Top 5 most-used patterns (id, sequence, usage count)
- Memory saving (original file bytes vs combined encoded + patterns file bytes) — the headline figure
- Token ratio (original token count vs encoded token count) — secondary
- Number of passes actually run (may be fewer than `--max-passes` if no changes found)
