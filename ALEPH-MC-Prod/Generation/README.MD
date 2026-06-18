## Running the Container

### From Outside the Container

To run a campaign without entering the container interactively, use the following script. It drops into the SLC4 environment, sources the necessary ALEPH setup files, and launches the job — all in one step:

```bash
exec bash -i <<'OUTER'
aleph-slc4

# ---------- everything below runs INSIDE the SLC4 container ----------
# Reproduce what the interactive rcfile would have sourced:
DIRLG="$ALEPHTOOLS/singularity"
. "$DIRLG/aleph-login.sh"
. "$DIRLG/alephenv-slc4.sh"

cd /afs/cern.ch/work/h/hfatehi/x

EOSBASE=/eos/user/h/hfatehi/aleph/campagins

# sanity: confirm the ALEPH binaries are on PATH before we start
echo "--- environment check ---"
which kinhvfl05 galeph julia miniprod 2>/dev/null || echo "WARNING: some binaries not found on PATH"
echo "python: $(which python)"
echo "-------------------------"

echo "================ Campaign (start 0) ================"
python hvfl05-Zqq.py --start 0 --njobs 1 --par 1 --outdir "$EOSBASE/1"
echo "================ Campaign finished ================"

exit
OUTER
```

---

### From Inside the Container

First, ensure you're inside the Scientific Linux environment. Set it up using the [Singularity guide](https://aleph-new.docs.cern.ch/legacy/singularity/), then run:

```bash
aleph-slc4
```

Then launch the job with:

```bash
python hvfl05-Zqq.py \
  --start 0 \
  --njobs 3333 \
  --par 50 \
  --workdir /tmp/$USER/mcchain_work_dir \
  --outdir /eos/user/U/USER/aleph/jobs0-3333
```

### Arguments

| Flag | Description |
|------|-------------|
| `--start` | Seed offset for generation. To run batches sequentially, set `--start` to `N` for the first batch and `N + 3000` for the next. |
| `--njobs` | Total number of jobs to run. |
| `--par` | Number of jobs to run in parallel. |
| `--workdir` | Working directory. Use `/tmp/$USER/...` to avoid running out of storage. |
| `--outdir` | Output directory for results. |
