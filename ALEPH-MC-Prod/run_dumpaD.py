#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Run dumpa in parallel (8 workers) on each *.AL file.
Each worker gets its own scratch directory to avoid fort.64/fort.76 collisions.
Output fort.64 files are saved to OUTPUT_DIR.

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
INPUT_DIR      = "/eos/experiment/aleph/LEP1/DATA/MINI/1992"
OUTPUT_DIR     = "/eos/user/h/hfatehi/ALEPH-DATA/1992"
DUMPA_DIR      = "/afs/cern.ch/work/h/hfatehi/for-Apranik/dumpa"
DUMPA_BIN      = os.path.join(DUMPA_DIR, "dumpa")
CARDS_TEMPLATE = os.path.join(DUMPA_DIR, "example_dumpa.cards")

# ---------------------------------------------------------------------------
# Worker function (runs in a subprocess via multiprocessing)
# ---------------------------------------------------------------------------

def process_file(al_path):
    """
    Process a single .AL file (e.g. Y15222.24.AL):
      1. Create a private scratch directory (avoids fort.64 collisions).
      2. Write a cards file pointing at this file.
      3. Run dumpa with ALPHACARDS set.
      4. Move fort.64 to the output directory.
      5. Clean up the scratch directory.
    Returns (basename, ok, message).
    """
    basename = os.path.basename(al_path)
    stem     = basename
    if stem.upper().endswith(".AL"):
        stem = stem[:-3]

    out_name = stem + ".fort64"
    out_file = os.path.join(OUTPUT_DIR, out_name)

    # Already done — skip
    if os.path.exists(out_file):
        return (basename, True, "SKIP (already exists)")

    safe_stem = stem.replace(".", "_")
    scratch   = tempfile.mkdtemp(prefix="dumpa_%s_" % safe_stem)

    try:
        # --- Write cards file into scratch dir ---
        cards_path = os.path.join(scratch, "dumpa.cards")
        with open(CARDS_TEMPLATE, "r") as fh:
            lines = fh.read().splitlines()

        fili_line = "FILI '%s | EPIO'" % al_path
        new_lines = []
        replaced  = False
        for line in lines:
            stripped = line.strip().upper()
            if stripped.startswith("FILI"):
                new_lines.append(fili_line)
                replaced = True
            elif stripped.startswith("EFLW") or stripped.startswith("EFLJ"):
                # Remove these lines — working example uses ENDQ instead
                continue
            else:
                new_lines.append(line)

        if not replaced:
            # Insert FILI just before ENDQ
            for i, line in enumerate(new_lines):
                if line.strip().upper().startswith("ENDQ"):
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
            cwd=scratch,
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
        shutil.rmtree(scratch, ignore_errors=True)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Run dumpa in parallel on all ALEPH .AL mini files."
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Print what would be done without running dumpa.")
    parser.add_argument("--workers", type=int, default=8,
                        help="Number of parallel workers (default: 8).")
    parser.add_argument("--start", type=int, default=None,
                        help="Only process files with run number >= START.")
    parser.add_argument("--end", type=int, default=None,
                        help="Only process files with run number <= END.")
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

    # --- Gather and sort .AL input files ---
    pattern    = os.path.join(INPUT_DIR, "*.AL")
    al_files   = sorted(glob.glob(pattern))

    # Also catch lowercase .al extension just in case
    pattern_lc = os.path.join(INPUT_DIR, "*.al")
    al_files   = sorted(set(al_files + glob.glob(pattern_lc)))

    if not al_files:
        print("No .AL files found in %s" % INPUT_DIR)
        sys.exit(1)

    # --- Optional numeric range filter on run number ---
    # Filename format: Y15222.24.AL -> run number is the first numeric group (15222)
    if args.start is not None or args.end is not None:
        filtered = []
        for f in al_files:
            bn = os.path.basename(f)
            digits = ""
            for ch in bn:
                if ch.isdigit():
                    digits += ch
                elif digits:
                    break
            try:
                num = int(digits)
            except ValueError:
                filtered.append(f)
                continue
            if args.start is not None and num < args.start:
                continue
            if args.end is not None and num > args.end:
                continue
            filtered.append(f)
        al_files = filtered

    total = len(al_files)

    print("=" * 60)
    print("Input dir  : %s" % INPUT_DIR)
    print("Output dir : %s" % OUTPUT_DIR)
    print("Files found: %d" % total)
    print("Workers    : %d" % args.workers)
    if args.dry_run:
        print("*** DRY RUN MODE ***")
        for f in al_files:
            print("  would process: %s" % os.path.basename(f))
        return
    print("=" * 60)

    # --- Run in parallel ---
    t_start = time.time()
    success = 0
    failed  = []
    done    = 0

    pool = multiprocessing.Pool(processes=args.workers)

    for (basename, ok, msg) in pool.imap_unordered(process_file, al_files):
        done += 1
        if ok:
            success += 1
            print("[%d/%d] %-30s %s" % (done, total, basename, msg))
        else:
            failed.append(basename)
            print("[%d/%d] FAILED %-25s %s" % (done, total, basename, msg))

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
