# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

DataParser is a Python tool that compresses large whitespace-separated number files by detecting repeated subsequences and replacing them with reference tokens (`$id`). It produces two output files: a token stream (`.encoded.txt`) and a pattern dictionary (`.patterns.txt`).

## Running the CLI

The CLI entry point (`cli.py`) lives alongside the `dataparser` package under `.claude/skills/dataparser/scripts/`. Run from the project root:

```bash
# Encode (compress)
python .claude/skills/dataparser/scripts/cli.py encode <input_path> [--batch-size 5000] [--max-passes 10] [--min-len 2] [--max-len 15] [--out-dir <dir>]

# Decode (restore original)
python .claude/skills/dataparser/scripts/cli.py decode <encoded_file> <patterns_file> [-o <output_path>]
```

The `dataparser` package must be importable; run with the scripts directory on `PYTHONPATH` or install it as a local package if needed.

## Architecture

All library code is in `.claude/skills/dataparser/scripts/dataparser/`:

- **`tokenizer.py`** — I/O layer. Reads/writes token files where each token is either an `int` or a `$ref` string. `iter_batches()` chunks a flat token list for per-batch processing.
- **`patterns.py`** — `PatternStore` interns `tuple → int id` bidirectionally and serializes to `id<TAB>token token …` format. IDs are stable once assigned.
- **`detect.py`** — `find_and_replace()`: counts all n-grams (length `min_len`..`max_len`), ranks candidates by savings (`occurrences × (length − 1)`), then greedily replaces non-overlapping matches right-to-left using `PatternStore.intern()`.
- **`encode.py`** — Orchestrates two phases:
  - **Phase 1** (`phase1_encode`): runs up to `max_passes` over sliding batches (batch size grows each pass); stops early when a pass finds no replacements; intermediate versioned files are cleaned up on each pass.
  - **Phase 2** (`phase2_encode`): global full-stream detection; iterates until convergence.
  - `finalize()` renames the last working file to the canonical output name.

## Rules
- Always ask clarifying questions before starting planning 
- Save all results to output folder
- Never expose anayled original data outside of this project

### Data flow

```
input.txt
  └─ phase1_encode → input.v1.txt → input.v2.txt … → last vN.txt
       └─ phase2_encode → further vN+1.txt … → convergence
            └─ finalize → input.encoded.txt  +  PatternStore.save → input.patterns.txt
```

Tokens in encoded files mix raw integers and `$id` references; `detect.py` treats both uniformly as opaque values when scanning for repeated sequences.
