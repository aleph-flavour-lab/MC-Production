#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Run dumpa in parallel (8 workers) on each mini_XXXXX.epio file.
Each worker gets its own scratch directory to avoid fort.64/fort.76 collisions.
Output fort.64 files are saved to /eos/user/h/hfatehi/aleph/dumpa-processed/

Compatible with Python 2.6/2.7 (Scientific Linux 6)
Usage:
  python run_dumpa.py              # process all files, 8 workers
  python run_dumpa.py --dry-run   # print what would be done
  python run_dumpa.py --workers 4 # use a different number of workers
  python run_dumpa.py --start 1 --end 100
"""

from __future__ import print_function
import os
import sys
import glob
import shutil
import subprocess
import argparse
import time
import multiprocessing
import tempfile

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
INPUT_DIR      = "/eos/user/h/hfatehi/aleph"
OUTPUT_DIR     = "/eos/user/h/hfatehi/aleph/dumpa-processed"
DUMPA_DIR      = "/afs/cern.ch/work/h/hfatehi/for-Apranik/dumpa"
DUMPA_BIN      = os.path.join(DUMPA_DIR, "dumpa")
CARDS_TEMPLATE = os.path.join(DUMPA_DIR, "example_dumpa.cards")

# ---------------------------------------------------------------------------
# Worker function (runs in a subprocess via multiprocessing)
# ---------------------------------------------------------------------------

def process_file(epio_path):
    """
    Process a single epio file:
      1. Create a private scratch directory (avoids fort.64 collisions).
      2. Write a cards file pointing at this epio file.
      3. Run dumpa with ALPHACARDS set.
      4. Move fort.64 to the output directory.
      5. Clean up the scratch directory.
    Returns (basename, ok, message).
    """
    basename = os.path.basename(epio_path)
    stem     = os.path.splitext(basename)[0]
    out_file = os.path.join(OUTPUT_DIR, stem + ".fort64")

    # Already done — skip
    if os.path.exists(out_file):
        return (basename, True, "SKIP (already exists)")

    # Private scratch dir so parallel workers don't share fort.64/fort.76
    scratch = tempfile.mkdtemp(prefix="dumpa_%s_" % stem)

    try:
        # --- Write cards file into scratch dir ---
        cards_path = os.path.join(scratch, "dumpa.cards")
        with open(CARDS_TEMPLATE, "r") as fh:
            lines = fh.read().splitlines()

        fili_line = "FILI '%s | EPIO'" % epio_path
        new_lines = []
        replaced  = False
        for line in lines:
            if line.strip().upper().startswith("FILI"):
                new_lines.append(fili_line)
                replaced = True
            else:
                new_lines.append(line)

        if not replaced:
            for i, line in enumerate(new_lines):
                if line.strip().upper().startswith("EFLW"):
                    new_lines.insert(i, fili_line)
                    replaced = True
                    break
            if not replaced:
                new_lines.append(fili_line)

        with open(cards_path, "w") as fh:
            fh.write("\n".join(new_lines) + "\n")

        # --- Run dumpa from scratch dir (fort.64 lands here) ---
        env = os.environ.copy()
        env["ALPHACARDS"] = cards_path

        proc = subprocess.Popen(
            [DUMPA_BIN],
            cwd=scratch,          # <-- each worker writes fort.64 to its own dir
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = proc.communicate()

        if proc.returncode != 0:
            msg = "dumpa exited %d\nSTDOUT: %s\nSTDERR: %s" % (
                proc.returncode,
                stdout[-500:] if stdout else "",
                stderr[-500:] if stderr else "",
            )
            return (basename, False, msg)

        fort64 = os.path.join(scratch, "fort.64")
        if not os.path.exists(fort64):
            return (basename, False, "fort.64 not produced")

        shutil.move(fort64, out_file)
        return (basename, True, "OK -> %s" % out_file)

    except Exception as exc:
        return (basename, False, "Exception: %s" % str(exc))

    finally:
        # Always remove the scratch directory
        shutil.rmtree(scratch, ignore_errors=True)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Run dumpa in parallel on all ALEPH mini epio files."
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Print what would be done without running dumpa.")
    parser.add_argument("--workers", type=int, default=8,
                        help="Number of parallel workers (default: 8).")
    parser.add_argument("--start", type=int, default=None,
                        help="Only process files with index >= START.")
    parser.add_argument("--end", type=int, default=None,
                        help="Only process files with index <= END.")
    args = parser.parse_args()

    # --- Sanity checks ---
    for path, label in [
        (DUMPA_BIN,      "dumpa binary"),
        (CARDS_TEMPLATE, "cards template"),
        (INPUT_DIR,      "input directory"),
    ]:
        if not os.path.exists(path):
            print("ERROR: %s not found: %s" % (label, path))
            sys.exit(1)

    if not args.dry_run:
        if not os.path.isdir(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)

    # --- Gather and sort input files ---
    pattern    = os.path.join(INPUT_DIR, "mini_?????.epio")
    epio_files = sorted(glob.glob(pattern))

    if not epio_files:
        print("No .epio files matching %s" % pattern)
        sys.exit(1)

    # --- Optional numeric range filter ---
    if args.start is not None or args.end is not None:
        filtered = []
        for f in epio_files:
            try:
                num = int(os.path.basename(f)[5:10])
            except ValueError:
                continue
            if args.start is not None and num < args.start:
                continue
            if args.end is not None and num > args.end:
                continue
            filtered.append(f)
        epio_files = filtered

    total = len(epio_files)

    print("=" * 60)
    print("Input dir  : %s" % INPUT_DIR)
    print("Output dir : %s" % OUTPUT_DIR)
    print("Files found: %d" % total)
    print("Workers    : %d" % args.workers)
    if args.dry_run:
        print("*** DRY RUN MODE ***")
        for f in epio_files:
            print("  would process: %s" % os.path.basename(f))
        return
    print("=" * 60)

    # --- Run in parallel ---
    t_start  = time.time()
    success  = 0
    failed   = []
    done     = 0

    pool = multiprocessing.Pool(processes=args.workers)

    # imap_unordered gives us results as they finish
    for (basename, ok, msg) in pool.imap_unordered(process_file, epio_files):
        done += 1
        if ok:
            success += 1
            print("[%d/%d] %-25s %s" % (done, total, basename, msg))
        else:
            failed.append(basename)
            print("[%d/%d] FAILED %-20s %s" % (done, total, basename, msg))

    pool.close()
    pool.join()

    elapsed = time.time() - t_start

    # --- Summary ---
    print("=" * 60)
    print("Finished in %.1fs.  %d/%d succeeded." % (elapsed, success, total))
    if failed:
        print("Failed (%d):" % len(failed))
        for f in failed:
            print("  " + f)
    print("=" * 60)


if __name__ == "__main__":
    main()
