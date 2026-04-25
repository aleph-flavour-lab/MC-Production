#!/usr/bin/env python3
"""
Run RWedm4hep_exec in parallel on all mini_XXXXX.fort64 files.
Output .root files are saved to /eos/user/h/hfatehi/aleph/edm4hep-processed/

Usage:
  python run_edm4hep.py              # process all files, 8 workers
  python run_edm4hep.py --dry-run
  python run_edm4hep.py --workers 16
  python run_edm4hep.py --start 1 --end 100
"""

import os
import sys
import glob
import subprocess
import argparse
import time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
INPUT_DIR  = Path("/eos/user/h/hfatehi/aleph/dumpa-processed")
OUTPUT_DIR = Path("/eos/user/h/hfatehi/aleph/edm4hep-processed")
RW_DIR     = Path("/afs/cern.ch/work/h/hfatehi/for-Apranik/RWedm4hep")
RW_BIN     = RW_DIR / "RWedm4hep_exec"

# ---------------------------------------------------------------------------
# Worker function
# ---------------------------------------------------------------------------

def process_file(fort64_path: Path) -> tuple[str, bool, str]:
    stem     = fort64_path.stem.replace(".fort64", "")   # mini_00042
    out_file = OUTPUT_DIR / f"{stem}.root"

    if out_file.exists():
        return (fort64_path.name, True, "SKIP (already exists)")

    cmd = [RW_BIN, "--input", fort64_path, "--output", out_file]

    try:
        result = subprocess.run(
            cmd,
            cwd=RW_DIR,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            msg = f"exited {result.returncode}\nSTDOUT: {result.stdout[-500:]}\nSTDERR: {result.stderr[-500:]}"
            return (fort64_path.name, False, msg)

        if not out_file.exists():
            return (fort64_path.name, False, "output .root file not produced")

        return (fort64_path.name, True, f"OK -> {out_file}")

    except Exception as exc:
        return (fort64_path.name, False, f"Exception: {exc}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Run RWedm4hep in parallel on all dumpa-processed fort64 files."
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Print what would be done without running anything.")
    parser.add_argument("--workers", type=int, default=8,
                        help="Number of parallel workers (default: 8).")
    parser.add_argument("--start", type=int, default=None,
                        help="Only process files with index >= START.")
    parser.add_argument("--end", type=int, default=None,
                        help="Only process files with index <= END.")
    args = parser.parse_args()

    # --- Sanity checks ---
    for path, label in [
        (RW_BIN,    "RWedm4hep_exec binary"),
        (INPUT_DIR, "input directory (dumpa-processed)"),
    ]:
        if not path.exists():
            print(f"ERROR: {label} not found: {path}")
            sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # --- Gather and sort input files ---
    fort64_files = sorted(INPUT_DIR.glob("mini_?????.fort64"))

    if not fort64_files:
        print(f"No .fort64 files found in {INPUT_DIR}")
        sys.exit(1)

    # --- Optional numeric range filter ---
    if args.start is not None or args.end is not None:
        fort64_files = [
            f for f in fort64_files
            if (args.start or 0) <= int(f.name[5:10]) <= (args.end or 99999)
        ]

    total = len(fort64_files)

    print("=" * 60)
    print(f"Input dir  : {INPUT_DIR}")
    print(f"Output dir : {OUTPUT_DIR}")
    print(f"Files found: {total}")
    print(f"Workers    : {args.workers}")

    if args.dry_run:
        print("*** DRY RUN MODE ***")
        for f in fort64_files:
            print(f"  would process: {f.name}")
        return

    print("=" * 60)

    # --- Run in parallel ---
    t_start = time.monotonic()
    success = 0
    failed  = []
    done    = 0

    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(process_file, f): f for f in fort64_files}

        for future in as_completed(futures):
            done += 1
            basename, ok, msg = future.result()
            if ok:
                success += 1
                print(f"[{done}/{total}] {basename:<25} {msg}")
            else:
                failed.append(basename)
                print(f"[{done}/{total}] FAILED {basename:<20} {msg}")

    elapsed = time.monotonic() - t_start

    # --- Summary ---
    print("=" * 60)
    print(f"Finished in {elapsed:.1f}s.  {success}/{total} succeeded.")
    if failed:
        print(f"Failed ({len(failed)}):")
        for f in failed:
            print(f"  {f}")
    print("=" * 60)


if __name__ == "__main__":
    main()
