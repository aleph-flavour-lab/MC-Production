#!/usr/bin/env python
"""
ALEPH LEP MC Full Simulation Chain Orchestrator
================================================
Python 2.3 compatible (no subprocess, no generator expressions).

Runs KINGAL -> GALEPH -> JULIA -> MINIPROD for N jobs of 1000 events each.
Seeds are assigned deterministically by global job index so successive
campaigns never collide:

    campaign 1 : --start 0   --njobs 100   -> LOSEED 1..100
    campaign 2 : --start 100 --njobs 1000  -> LOSEED 101..1100

Each job runs in its own sub-directory  job_<LOSEED>/  so files never clash
and a failed job does not corrupt neighbours.

Usage
-----
    python aleph_mcchain.py [options]

Options
-------
    --start   INT   First global job index  (default: 0)
    --njobs   INT   Number of jobs to run   (default: 10)
    --par     INT   Max parallel jobs       (default: 4)
    --inseed  INT   INSEED for KINGAL       (default: 91)
    --ecms    FLOAT Centre-of-mass energy   (default: 91.2)
    --flavor  INT   IFLAVOR for KINGAL      (default: 1)
    --date    INT   DATE card for GALEPH    (default: 94)
    --workdir STR   Root working directory  (default: ./mcchain_work)
    --dbase   STR   Path to ADBS database
    --dry-run       Write cards but do not execute anything

Examples
--------
# First 10k events
python aleph_mcchain.py --start 0 --njobs 10 --par 8

# Next 90k (skips already-done jobs automatically)
python aleph_mcchain.py --start 10 --njobs 90 --par 8

# 1M events total, aggressive parallelism
python aleph_mcchain.py --start 0 --njobs 1000 --par 32

# Test card generation without running anything
python aleph_mcchain.py --start 0 --njobs 3 --dry-run

# Different energy (LEP2, WW production)
python aleph_mcchain.py --start 0 --njobs 100 --ecms 183.0 --flavor 3 --date 97

# Custom output location
python aleph_mcchain.py --start 0 --njobs 100 --workdir /afs/cern.ch/work/h/hfatehi/aleph/mc_1M
"""

import os
import sys
import threading
import optparse
import traceback

# ---------------------------------------------------------------------------
# Default parameters
# ---------------------------------------------------------------------------
EVENTS_PER_JOB = 1000
DEFAULT_INSEED  = 91
DEFAULT_ECMS    = 91.2
DEFAULT_FLAVOR  = 1
DEFAULT_DATE    = 94
DEFAULT_DBASE   = '/cvmfs/aleph.cern.ch/i386_redhat42/dbase/adbs314.daf'

# ---------------------------------------------------------------------------
# Card-file generators
# ---------------------------------------------------------------------------

def make_pythia_cards(loseed, inseed, ecms, flavor, workdir):
    epio_out = os.path.join(workdir, 'pythia_%05d.epio' % loseed)
    cards = """\
KCAR 0 / $TEXT
POFF
*---  set up modification
MSTP   3  /     1
MSTP  11  /     1
MSTP  83  /   200
*-----------------------------------------------------------
PMA1   6  /     174.
PMA1   7  /     250.
PMA1   8  /     350.
PMA1  23  /     91.182
PMA2  23  /     2.484
PMA1  24  /     80.25
PMA1  25  /     300.
PMA1 10221 /    1.0
PMA1 20213 /    1.251
PARU 102  /     .232
PARJ 123  /     91.182
PARJ 124  /     2.484
PMA4 130 /     5.1700E-08
PMA4 310 /     0.8926E-10
PMA4 411 /     1.0570E-12
PMA4 421 /     0.4150E-12
PMA4 431 /     0.4670E-12
*------------------------------Jetset setup------------------
MSTU  16  /     2
MSTJ   1  /     1
MSTJ  11  /     3
MSTJ  12  /     2
MSTJ  24  /     2
MSTJ  41  /     2
MSTJ  42  /     2
MSTJ  43  /     4
MSTJ  44  /     2
MSTJ  46  /     3
MSTJ  47  /     2
MSTJ 101  /     5
PARJ   1  /     0.107
PARJ   2  /     0.287
PARJ   3  /     0.68
PARJ  11  /     0.56
PARJ  12  /     0.47
PARJ  13  /     0.65
PARJ  14  /     0.120
PARJ  15  /     0.040
PARJ  16  /     0.120
PARJ  17  /     0.20
PARJ  19  /     0.56
PARJ  21  /     0.371
PARJ  26  /     0.27
PARJ  41  /     0.4
PARJ  42  /     0.805
PARJ  54  /     -0.040
PARJ  55  /     -0.0035
PARJ  81  /     0.291
PARJ  82  /     1.52
*
RUN  912  'PYTHIA 6.1 Z hadronic run LOSEED %(loseed)d'
TRIG     1  %(nevt)d
DEBU 6 / 1  3
TIME    10
FILO '%(epio_out)s|EPIO'
RMAR    %(inseed)s    %(loseed)d
SVRT  0.0113   0.0005   0.79
GPYT    %(flavor)d    %(ecms)s    1
END$
""" % {'loseed': loseed, 'nevt': EVENTS_PER_JOB,
       'epio_out': epio_out, 'inseed': inseed,
       'ecms': ecms, 'flavor': flavor}
    return cards, epio_out


def make_galeph_cards(loseed, pythia_epio, workdir, date):
    epio_out = os.path.join(workdir, 'galeph_%05d.epio' % loseed)
    cards = """\
TIME 100
FILI '%(fili)s | EPIO'
FILO '%(filo)s | EPIO'
DISP 0 /
NEVT 1 -%(nevt)d
SETS 'VDET' 'ITC ' 'TPC ' 'ECAL' 'LCAL' 'HCAL' 'MUON' 'SICA'
PROC 'TRAC' 'HITS' 'DIGI' 'TRIG'
DEBU 1 10 1
PRINT 'INPU' 'OUTP'
DATE %(date)d
TPCSIM
ENDQ
""" % {'fili': pythia_epio, 'filo': epio_out,
       'nevt': EVENTS_PER_JOB, 'date': date}
    return cards, epio_out


def make_julia_cards(loseed, galeph_epio, workdir, dbase):
    epio_out = os.path.join(workdir, 'julia_%05d.epio' % loseed)
    cards = """\
FDBA '%(dbase)s'
FILI '%(fili)s | EPIO'
FILO '%(filo)s | EPIO'
ENDQ
""" % {'dbase': dbase, 'fili': galeph_epio, 'filo': epio_out}
    return cards, epio_out


def make_miniprod_cards(loseed, julia_epio, workdir):
    epio_out = os.path.join(workdir, 'mini_%05d.epio' % loseed)
    cards = """\
MINP
TIME 1500000000000000000000
DEBU 0
MPRI 0
*** Input & Output files
FILI '%(fili)s | EPIO'
FILO '%(filo)s | EPIO'
ENDQ
""" % {'fili': julia_epio, 'filo': epio_out}
    return cards, epio_out


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def write_file(path, text):
    f = open(path, 'w')
    f.write(text)
    f.close()


def run_cmd(cmd, env, logfile):
    """
    Run a shell command, capturing stdout+stderr into logfile.
    Returns the integer exit code.

    Python 2.3 compatible: uses a wrapper shell script + sentinel file
    to capture both output and the exit code, since os.popen4 does not
    expose the return code and subprocess does not exist in 2.3.
    """
    # Build env export block; skip BASH_FUNC_* and other
    # non-identifier keys that /bin/sh (dash) cannot export.
    import re as _re
    _vkey = _re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')
    env_lines = []
    for k, v in env.items():
        if not _vkey.match(k):
            continue
        v_esc = v.replace("'", "'\\''")
        env_lines.append("export %s='%s'" % (k, v_esc))
    env_block = '\n'.join(env_lines)

    sentinel = logfile + '.rc'
    wrapper  = logfile + '.sh'

    wrapper_text = """\
#!/bin/sh
%(env_block)s
%(cmd)s >> %(logfile)s 2>&1
echo $? > %(sentinel)s
""" % {'env_block': env_block, 'cmd': cmd,
       'logfile': logfile, 'sentinel': sentinel}

    # Write a header to the log before running
    lf = open(logfile, 'a')
    lf.write('=' * 60 + '\n')
    lf.write('CMD: %s\n' % cmd)
    lf.write('=' * 60 + '\n')
    lf.close()

    write_file(wrapper, wrapper_text)
    os.chmod(wrapper, 0755)
    os.system('/bin/sh ' + wrapper)

    # Read back exit code from sentinel
    rc = 1
    try:
        rf = open(sentinel)
        rc = int(rf.read().strip())
        rf.close()
        os.remove(sentinel)
    except Exception:
        pass
    try:
        os.remove(wrapper)
    except Exception:
        pass

    lf = open(logfile, 'a')
    lf.write('\nEXIT CODE: %d\n' % rc)
    lf.close()
    return rc


# ---------------------------------------------------------------------------
# Single-job pipeline
# ---------------------------------------------------------------------------

def run_job(loseed, inseed, ecms, flavor, date, dbase, root_workdir, dry_run):
    """
    Execute the full chain for one LOSEED value.
    Returns (loseed, success, message).
    """
    jobdir = os.path.join(root_workdir, 'job_%05d' % loseed)
    if not os.path.exists(jobdir):
        os.makedirs(jobdir)

    logfile     = os.path.join(jobdir, 'chain.log')
    status_file = os.path.join(jobdir, 'STATUS')

    # Safe restart: skip jobs already finished successfully
    if os.path.exists(status_file):
        sf = open(status_file)
        status = sf.read().strip()
        sf.close()
        if status == 'DONE':
            return (loseed, True, 'already complete, skipped')

    def log(msg):
        line = '[LOSEED %05d] %s' % (loseed, msg)
        print line
        sys.stdout.flush()
        lf = open(logfile, 'a')
        lf.write(line + '\n')
        lf.close()

    log('Starting job in %s' % jobdir)

    # ------------------------------------------------------------------
    # Step 1 : KINGAL / PYTHIA
    # ------------------------------------------------------------------
    pyth_text, pythia_epio = make_pythia_cards(
        loseed, inseed, ecms, flavor, jobdir)
    pyth_path = os.path.join(jobdir, 'pythia_%05d.cards' % loseed)
    write_file(pyth_path, pyth_text)
    log('Wrote %s' % pyth_path)

    if not dry_run:
        env = os.environ.copy()
        env['KINGALCARDS'] = pyth_path
        rc = run_cmd('kinpyth05 %s' % pyth_path, env, logfile)
        if rc != 0:
            msg = 'KINGAL failed (rc=%d)' % rc
            log(msg)
            write_file(status_file, 'FAILED:KINGAL')
            return (loseed, False, msg)
        if not os.path.exists(pythia_epio):
            msg = 'KINGAL produced no output: %s' % pythia_epio
            log(msg)
            write_file(status_file, 'FAILED:KINGAL_OUTPUT')
            return (loseed, False, msg)
        log('KINGAL OK -> %s' % pythia_epio)
    else:
        log('[DRY-RUN] kinpyth05 %s' % pyth_path)

    # ------------------------------------------------------------------
    # Step 2 : GALEPH
    # ------------------------------------------------------------------
    gal_text, galeph_epio = make_galeph_cards(
        loseed, pythia_epio, jobdir, date)
    gal_path = os.path.join(jobdir, 'galeph_%05d.cards' % loseed)
    write_file(gal_path, gal_text)
    log('Wrote %s' % gal_path)

    if not dry_run:
        env = os.environ.copy()
        env['GALEPHCARDS'] = gal_path
        rc = run_cmd('galeph', env, logfile)
        if rc != 0:
            msg = 'GALEPH failed (rc=%d)' % rc
            log(msg)
            write_file(status_file, 'FAILED:GALEPH')
            return (loseed, False, msg)
        if not os.path.exists(galeph_epio):
            msg = 'GALEPH produced no output: %s' % galeph_epio
            log(msg)
            write_file(status_file, 'FAILED:GALEPH_OUTPUT')
            return (loseed, False, msg)
        log('GALEPH OK -> %s' % galeph_epio)
    else:
        log('[DRY-RUN] galeph (cards=%s)' % gal_path)

    # ------------------------------------------------------------------
    # Step 3 : JULIA
    # ------------------------------------------------------------------
    jul_text, julia_epio = make_julia_cards(
        loseed, galeph_epio, jobdir, dbase)
    jul_path = os.path.join(jobdir, 'julia_%05d.cards' % loseed)
    write_file(jul_path, jul_text)
    log('Wrote %s' % jul_path)

    if not dry_run:
        env = os.environ.copy()
        env['JULIACARDS'] = jul_path
        rc = run_cmd('julia', env, logfile)
        if rc != 0:
            msg = 'JULIA failed (rc=%d)' % rc
            log(msg)
            write_file(status_file, 'FAILED:JULIA')
            return (loseed, False, msg)
        if not os.path.exists(julia_epio):
            msg = 'JULIA produced no output: %s' % julia_epio
            log(msg)
            write_file(status_file, 'FAILED:JULIA_OUTPUT')
            return (loseed, False, msg)
        log('JULIA OK -> %s' % julia_epio)
    else:
        log('[DRY-RUN] julia (cards=%s)' % jul_path)

    # ------------------------------------------------------------------
    # Step 4 : MINIPROD
    # ------------------------------------------------------------------
    mini_text, mini_epio = make_miniprod_cards(loseed, julia_epio, jobdir)
    mini_path = os.path.join(jobdir, 'miniprod_%05d.cards' % loseed)
    write_file(mini_path, mini_text)
    log('Wrote %s' % mini_path)

    if not dry_run:
        env = os.environ.copy()
        env['ALPHACARDS'] = mini_path
        rc = run_cmd('miniprod', env, logfile)
        if rc != 0:
            msg = 'MINIPROD failed (rc=%d)' % rc
            log(msg)
            write_file(status_file, 'FAILED:MINIPROD')
            return (loseed, False, msg)
        if not os.path.exists(mini_epio):
            msg = 'MINIPROD produced no output: %s' % mini_epio
            log(msg)
            write_file(status_file, 'FAILED:MINIPROD_OUTPUT')
            return (loseed, False, msg)
        log('MINIPROD OK -> %s' % mini_epio)

        # Remove large intermediate EPIO files; keep mini + cards + log
        for f in [pythia_epio, galeph_epio, julia_epio]:
            if os.path.exists(f):
                os.remove(f)
                log('Removed intermediate %s' % f)

        write_file(status_file, 'DONE')
        log('Job complete. Final output: %s' % mini_epio)
    else:
        log('[DRY-RUN] miniprod (cards=%s)' % mini_path)
        write_file(status_file, 'DRYRUN')

    return (loseed, True, 'success')


# ---------------------------------------------------------------------------
# Thread worker
# ---------------------------------------------------------------------------

class JobThread(threading.Thread):
    def __init__(self, loseed, opts):
        threading.Thread.__init__(self)
        self.loseed = loseed
        self.opts   = opts
        self.result = None

    def run(self):
        try:
            self.result = run_job(
                loseed       = self.loseed,
                inseed       = self.opts.inseed,
                ecms         = self.opts.ecms,
                flavor       = self.opts.flavor,
                date         = self.opts.date,
                dbase        = self.opts.dbase,
                root_workdir = self.opts.workdir,
                dry_run      = self.opts.dry_run,
            )
        except Exception:
            tb = traceback.format_exc()
            self.result = (self.loseed, False, 'EXCEPTION:\n' + tb)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args():
    p = optparse.OptionParser(usage=__doc__)
    p.add_option('--start',   type='int',   default=0)
    p.add_option('--njobs',   type='int',   default=10)
    p.add_option('--par',     type='int',   default=4)
    p.add_option('--inseed',  type='int',   default=DEFAULT_INSEED)
    p.add_option('--ecms',    type='float', default=DEFAULT_ECMS)
    p.add_option('--flavor',  type='int',   default=DEFAULT_FLAVOR)
    p.add_option('--date',    type='int',   default=DEFAULT_DATE)
    p.add_option('--workdir', default='./mcchain_work')
    p.add_option('--dbase',   default=DEFAULT_DBASE)
    p.add_option('--dry-run', dest='dry_run', action='store_true', default=False)
    opts, args = p.parse_args()
    return opts


def main():
    opts = parse_args()

    if not os.path.exists(opts.workdir):
        os.makedirs(opts.workdir)

    # LOSEED = global job index, 1-based to avoid seed=0
    loseeds = range(opts.start + 1, opts.start + opts.njobs + 1)

    print 'ALEPH MC chain orchestrator'
    print '  Events per job : %d' % EVENTS_PER_JOB
    print '  Total jobs     : %d  (%d events)' % (
        opts.njobs, opts.njobs * EVENTS_PER_JOB)
    print '  LOSEED range   : %d .. %d' % (loseeds[0], loseeds[-1])
    print '  Parallelism    : %d' % opts.par
    print '  Work dir       : %s' % opts.workdir
    print '  Dry run        : %s' % opts.dry_run
    print ''
    sys.stdout.flush()

    total  = len(loseeds)
    done   = 0
    failed = []

    for batch_start in range(0, total, opts.par):
        batch   = loseeds[batch_start: batch_start + opts.par]
        threads = []
        for ls in batch:
            t = JobThread(ls, opts)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()
            loseed, ok, msg = t.result
            done += 1
            if ok:
                print '[%d/%d] LOSEED %05d : OK  (%s)' % (
                    done, total, loseed, msg)
            else:
                print '[%d/%d] LOSEED %05d : FAIL (%s)' % (
                    done, total, loseed, msg)
                failed.append((loseed, msg))
            sys.stdout.flush()

    print ''
    print '=' * 60
    print 'Campaign summary'
    print '  Jobs attempted : %d' % total
    print '  Jobs succeeded : %d' % (total - len(failed))
    print '  Jobs failed    : %d' % len(failed)
    if failed:
        print '  Failed LOSEEDs :'
        for ls, msg in failed:
            print '    LOSEED %05d  ->  %s' % (ls, msg)

    summary_path = os.path.join(
        opts.workdir,
        'summary_start%d_n%d.txt' % (opts.start, opts.njobs))
    sf = open(summary_path, 'w')
    sf.write('start=%d njobs=%d ecms=%s flavor=%d date=%d\n' % (
        opts.start, opts.njobs, opts.ecms, opts.flavor, opts.date))
    sf.write('failed_loseeds=%s\n' % ','.join([str(ls) for ls, _ in failed]))
    sf.close()
    print '  Summary written: %s' % summary_path
    print '=' * 60

    if failed:
        sys.exit(1)


if __name__ == '__main__':
    main()
