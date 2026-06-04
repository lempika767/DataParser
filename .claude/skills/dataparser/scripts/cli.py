#!/usr/bin/env python3
"""DataParser CLI: encode and decode large number files."""
import argparse
import os
import sys

# Allow running from any working directory
sys.path.insert(0, os.path.dirname(__file__))

from dataparser.tokenizer import read_all_tokens, write_tokens
from dataparser.patterns import PatternStore
from dataparser.encode import phase1_encode, phase2_encode, finalize
from dataparser.cleanup import run_cleanup, renumber
from dataparser.decode import decode


def _decode_from_input(args):
    input_path = os.path.abspath(args.input)
    if not os.path.exists(input_path):
        print(f"Error: file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    basename = os.path.basename(input_path)
    dir_path = os.path.dirname(input_path)
    if basename.endswith(".encoded.txt"):
        stem = basename[: -len(".encoded.txt")]
    else:
        stem = os.path.splitext(basename)[0]

    patterns_path = os.path.join(dir_path, stem + ".patterns.txt")
    if not os.path.exists(patterns_path):
        print(f"Error: patterns file not found: {patterns_path}", file=sys.stderr)
        sys.exit(1)

    out_dir = args.out_dir or dir_path
    os.makedirs(out_dir, exist_ok=True)
    output_path = os.path.join(out_dir, stem + ".decoded.txt")

    count = decode(input_path, patterns_path, output_path)
    print(f"Decoded {count} tokens -> {output_path}")


def cmd_encode(args):
    if args.decode:
        return _decode_from_input(args)

    input_path = os.path.abspath(args.input)
    if not os.path.exists(input_path):
        print(f"Error: file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    out_dir = args.out_dir or os.path.dirname(input_path)
    os.makedirs(out_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(input_path))[0]

    work_base = os.path.join(out_dir, base_name + ".encoded_work.txt")
    encoded_final = os.path.join(out_dir, base_name + ".encoded.txt")
    patterns_path = os.path.join(out_dir, base_name + ".patterns.txt")

    store = PatternStore()

    # Phase 1
    print(f"Phase 1: per-batch iterative replacement (max {args.max_passes} passes)...")
    current, passes_run = phase1_encode(
        input_path, store, work_base,
        batch_size=args.batch_size,
        max_passes=args.max_passes,
        min_len=args.min_len,
        max_len=args.max_len,
    )
    print(f"  Done in {passes_run} pass(es). Patterns so far: {len(store)}")

    # Phase 2
    print("Phase 2: global cross-batch pattern detection...")
    current = phase2_encode(current, store, work_base, args.min_len, args.max_len)
    print(f"  Patterns after phase 2: {len(store)}")

    # Phase 3 cleanup
    print("Phase 3: reference garbage collection...")
    final_tokens, removed = run_cleanup(current, store)
    if removed:
        print(f"  Removed {removed} unused/single-use pattern(s).")
    final_tokens, store = renumber(final_tokens, store)
    print(f"  Final pattern count: {len(store)}")

    # Write outputs
    write_tokens(encoded_final, final_tokens)
    store.save(patterns_path)

    # Clean up the intermediate work file. Guard against the input file:
    # when no patterns are found, the phases return the input path unchanged,
    # and removing it here would destroy the user's original data.
    if current not in (input_path, encoded_final) and os.path.exists(current):
        os.remove(current)

    # Stats
    original_count = sum(1 for _ in open(input_path).read().split())
    encoded_count = len(final_tokens)
    ratio = encoded_count / original_count if original_count else 1.0

    # Byte-based memory saving: the real on-disk footprint is the encoded file
    # PLUS the patterns dictionary, both of which are required to reconstruct.
    original_bytes = os.path.getsize(input_path)
    encoded_bytes = os.path.getsize(encoded_final)
    patterns_bytes = os.path.getsize(patterns_path)
    combined_bytes = encoded_bytes + patterns_bytes
    saving = (original_bytes - combined_bytes) / original_bytes if original_bytes else 0.0

    print(f"\nDone.")
    print(f"  Input tokens   : {original_count}")
    print(f"  Encoded tokens : {encoded_count}")
    print(f"  Token ratio    : {ratio:.2%}")
    print(f"  Original size  : {original_bytes} bytes")
    print(f"  Encoded size   : {encoded_bytes} bytes")
    print(f"  Patterns size  : {patterns_bytes} bytes")
    print(f"  Combined size  : {combined_bytes} bytes (encoded + patterns)")
    print(f"  Memory saving  : {saving:.2%}")
    print(f"  Passes run     : {passes_run}")
    print(f"  Patterns found : {len(store)}")
    print(f"  Encoded file   : {encoded_final}")
    print(f"  Patterns file  : {patterns_path}")


def cmd_decode(args):
    encoded_path = os.path.abspath(args.encoded)
    patterns_path = os.path.abspath(args.patterns)
    out = args.output or encoded_path.replace(".encoded.txt", ".decoded.txt")
    count = decode(encoded_path, patterns_path, out)
    print(f"Decoded {count} tokens -> {out}")


def main():
    parser = argparse.ArgumentParser(description="DataParser: compress/decompress number files")
    sub = parser.add_subparsers(dest="command")

    enc = sub.add_parser("encode", help="Encode a number file")
    enc.add_argument("input", help="Path to input number file")
    enc.add_argument("--batch-size", type=int, default=5000)
    enc.add_argument("--max-passes", type=int, default=10)
    enc.add_argument("--min-len", type=int, default=2)
    enc.add_argument("--max-len", type=int, default=15)
    enc.add_argument("--out-dir", default=None)
    enc.add_argument("--decode", action="store_true", default=False,
                     help="Decode the input .encoded.txt file back to numbers")

    dec = sub.add_parser("decode", help="Decode an encoded file")
    dec.add_argument("encoded", help="Path to .encoded.txt file")
    dec.add_argument("patterns", help="Path to .patterns.txt file")
    dec.add_argument("-o", "--output", default=None)

    args = parser.parse_args()
    if args.command == "encode":
        cmd_encode(args)
    elif args.command == "decode":
        cmd_decode(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
