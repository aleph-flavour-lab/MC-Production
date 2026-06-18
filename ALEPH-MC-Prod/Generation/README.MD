## Running the Container and generating $Z \to q\bar{q}$ events.

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
