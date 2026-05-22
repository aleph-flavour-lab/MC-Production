#!/usr/bin/env python
"""
ALEPH LEP MC Full Simulation Chain Orchestrator
================================================
Configured for: qq-bar production, 5 flavours, 1994 conditions
  - PYTHIA 6.1,  IFLAVOR=1  (hadrons, 5 flavours, no top)
  - ECM = 91.2 GeV  (LEP1 Z-peak)
  - 1994 vertex smearing: sx=0.0124 sy=0.0005 sz=0.72
  - GALEPH DATE = 94
  - G. Rudolph June 2001 Pythia 6.1 fragmentation tuning applied on top
    of the standard pyth05/kk2f base parameter set

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
    python aleph_mcchain_qqbar5f_94.py [options]

Options
-------
    --start   INT   First global job index  (default: 0)
    --njobs   INT   Number of jobs to run   (default: 10)
    --par     INT   Max parallel jobs       (default: 4)
    --inseed  INT   INSEED for KINGAL       (default: 91)
    --workdir STR   Root working directory  (default: ./mcchain_work)
    --dbase   STR   Path to ADBS database
    --last-step STR Last step to run: kingal, galeph, julia, miniprod
                    (default: miniprod)
    --outdir  STR   Output directory for final EPIO files
    --dry-run       Write cards but do not execute anything

Examples
--------
    # First campaign: 100 jobs = 100k events
    python aleph_mcchain_qqbar5f_94.py --start 0 --njobs 100 --par 8

    # Second campaign: seeds pick up where the first left off
    python aleph_mcchain_qqbar5f_94.py --start 100 --njobs 1000 --par 8

    # Generator level only
    python aleph_mcchain_qqbar5f_94.py --start 0 --njobs 100 --par 16 --last-step kingal

    # Full chain to EOS
    python aleph_mcchain_qqbar5f_94.py \\
            --start 0 --njobs 1000 --par 8 --last-step miniprod \\
            --outdir /eos/user/h/hfatehi/aleph/qqbar5f_94
"""

import os
import sys
import threading
import optparse

# ---------------------------------------------------------------------------
# Fixed physics parameters for this sample
# ---------------------------------------------------------------------------
EVENTS_PER_JOB = 1000

# PYTHIA IFLAVOR=1 : qq-bar, 5 flavours (u d s c b), no top
IFLAVOR  = 1

# LEP1 Z-peak
ECMS     = 91.2

# 1994 vertex smearing (cm)  -- from ALEPH run-period table
SVRT_X   = 0.0124
SVRT_Y   = 0.0005
SVRT_Z   = 0.72

# GALEPH date tag
GALEPH_DATE = 94

# Default INSEED and database
DEFAULT_INSEED = 91
DEFAULT_DBASE  = '/cvmfs/aleph.cern.ch/i386_redhat42/dbase/adbs314.daf'


# ---------------------------------------------------------------------------
# Card-file generators
# ---------------------------------------------------------------------------

def make_pythia_cards(loseed, inseed, workdir):
    """
    Build PYTHIA 6.1 cards for qq-bar, 5 flavours, 91.2 GeV, 1994 vertex.

    Parameter block is the standard pyth05 base set (from the reference cards)
    with the G. Rudolph June 2001 Pythia 6.1 re-tuning overlay applied
    (from pythia61.cards):
        MSTJ 12/2        old diquark + popcorn (= JETSET 7.4 default)
        PARJ 81/0.277    lambda_QCD  (was 0.291)
        PARJ 82/1.58     M_min       (was 1.52)
        PARJ 21/0.372    sigma_mt    (was 0.371)
        PARJ 41/0.50     a           (was 0.40)
        PARJ 42/0.894    B           (was 0.805)
        PARJ 55/-0.0024  epsilon_b   (was -0.0035)

    The GPYT card uses IFLAVOR=1 (5 flavours), matching pyth03 / pyth05
    style, with ECMS=91.2 GeV.
    """
    epio_out = os.path.join(workdir, 'pythia_%05d.epio' % loseed)

    cards = """\
KCAR 0 / $TEXT
POFF
*---  Standard parameter block (pyth05 base) ----------------------------
*  Source: /cvmfs/aleph.cern.ch/reference/kin/pyth05.cards
*          /cvmfs/aleph.cern.ch/reference/kin/pythia61.cards
*-------------------------------------------------------------------------

*--- Pythia switches
MSTP   3  /     1         ! take lambda_QCD from PARJ(81)
MSTP  11  /     1         ! initial state radiation ON
MSTP  83  /   200         ! MC phase-space points if MSTP(82)>2

*--- Particle masses (standard ALEPH set)
PMA1   6  /     174.      ! top mass (inaccessible at 91 GeV)
PMA1   7  /     250.      ! b' mass (4th gen, pushed away)
PMA1   8  /     350.      ! t' mass
PMA1  23  /     91.182    ! Z0 mass
PMA2  23  /     2.484     ! Z0 width
PMA1  24  /     80.25     ! W mass
PMA1  25  /     300.      ! Higgs mass
PMA1 10221 /    1.0       ! f0(975): avoids infinite loops in LUDECY
PMA1 20213 /    1.251     ! a1 mass

*--- EW parameters
PARU 102  /     0.232     ! sin^2(theta_W)
PARJ 123  /     91.182    ! M_Z  (for JETSET internal use)
PARJ 124  /     2.484     ! Gamma_Z

*--- Lifetimes (PDG 94 values)
PMA4 130 /     5.1700E-08 ! K0L
PMA4 310 /     0.8926E-10 ! K0S
PMA4 411 /     1.0570E-12 ! D+
PMA4 421 /     0.4150E-12 ! D0
PMA4 431 /     0.4670E-12 ! Ds

*--- JETSET / string fragmentation switches
MSTU  16  /     2         ! link hadrons to proper end of string
MSTJ   1  /     1         ! string fragmentation
MSTJ  11  /     3         ! Peterson fragmentation for c and b quarks
MSTJ  24  /     2         ! truncated Breit-Wigner for resonances
MSTJ  41  /     2         ! FSR from quarks and leptons
MSTJ  42  /     2         ! coherent parton shower
MSTJ  43  /     4         ! z definition: global unconstrained
MSTJ  44  /     2         ! alpha_s scale: z(1-z)m^2
MSTJ  46  /     3         ! azimuthal correlations + coherence + gluon pol.
MSTJ  47  /     2         ! correction at first branching (qqg)
MSTJ 101  /     5         ! parton shower option
MSTJ  28  /     0         ! external tau library off (TAUOLA handled later)

*--- Disable W->top decays (top inaccessible)
MDM1 174  /     0         ! W -> t b  off
MDM1 337  /     0         ! W_virt -> t b  off

*--- Fragmentation parameters (pyth05 base values) ----------------------
PARJ   1  /     0.107     ! qq/q diquark suppression
PARJ   2  /     0.287     ! s/u strangeness suppression
PARJ   3  /     0.68      ! su/du
PARJ  11  /     0.56      ! V/(V+P) for ud
PARJ  12  /     0.47      ! V/(V+P) for s
PARJ  13  /     0.65      ! V/(V+P) for c,b
PARJ  14  /     0.120     ! = PARJ(16)
PARJ  15  /     0.040     ! = PARJ(17)/5
PARJ  16  /     0.120     ! = 3*PARJ(17)/5
PARJ  17  /     0.20      ! tensor meson nonets
PARJ  19  /     0.56      ! leading baryon suppression
PARJ  26  /     0.27      ! eta-prime suppression
PARJ  54  /     -0.040    ! epsilon_c  (Peterson)

*--- G. Rudolph June 2001 Pythia 6.1 re-tuning overlay ------------------
*  Source: /cvmfs/aleph.cern.ch/reference/kin/pythia61.cards
MSTJ  12  /     2         ! old diquark+popcorn (= JETSET 7.4 =3)
PARJ  81  /     0.277     ! lambda_QCD  (was 0.291 in JETSET 7.4)
PARJ  82  /     1.58      ! M_min       (was 1.52)
PARJ  21  /     0.372     ! sigma_mt    (was 0.371)
PARJ  41  /     0.50      ! a           (was 0.40)
PARJ  42  /     0.894     ! B           (was 0.805)
PARJ  55  /     -0.0024   ! epsilon_b   (was -0.0035)

*--- Run steering ----------------------------------------------------------
RUN  912  'PYTHIA 6.1 qqbar 5f 91.2 GeV 1994 LOSEED %(loseed)d'
TRIG     1  %(nevt)d
DEBU 6 / 1  3
TIME    10
FILO '%(epio_out)s|EPIO'
*  INSEED: institute range  LOSEED: local run counter (unique per job)
RMAR    %(inseed)d    %(loseed)d
*  1994 vertex smearing (cm)
SVRT  %(sx)s   %(sy)s   %(sz)s
*  IFLAVOR=1 -> qq-bar, 5 flavours  ECMS=91.2 GeV  IPRINT=1
GPYT    %(flavor)d    %(ecms)s    1
END$
""" % {
        'loseed':   loseed,
        'nevt':     EVENTS_PER_JOB,
        'epio_out': epio_out,
        'inseed':   inseed,
        'ecms':     ECMS,
        'flavor':   IFLAVOR,
        'sx':       SVRT_X,
        'sy':       SVRT_Y,
        'sz':       SVRT_Z,
    }
    return cards, epio_out


def make_galeph_cards(loseed, pythia_epio, workdir):
    """
    GALEPH detector simulation cards, 1994 conditions (DATE=94).
    """
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
""" % {
        'fili': pythia_epio,
        'filo': epio_out,
        'nevt': EVENTS_PER_JOB,
        'date': GALEPH_DATE,
    }
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


def move_to_outdir(src, outdir, log):
    import shutil
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    dst = os.path.join(outdir, os.path.basename(src))
    shutil.move(src, dst)
    log('Moved final output to %s' % dst)
    return dst


def run_cmd(cmd, env, logfile):
    """
    Run a shell command, capturing stdout+stderr into logfile.
    Returns the integer exit code.
    Python 2.3 compatible: uses a wrapper shell script + sentinel file.
    """
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

    lf = open(logfile, 'a')
    lf.write('=' * 60 + '\n')
    lf.write('CMD: %s\n' % cmd)
    lf.write('=' * 60 + '\n')
    lf.close()

    write_file(wrapper, wrapper_text)
    os.chmod(wrapper, 0755)
    os.system('/bin/sh ' + wrapper)

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

def run_job(loseed, inseed, dbase, root_workdir, dry_run,
            last_step='miniprod', outdir=None):
    """
    Execute the chain up to last_step for one LOSEED value.
    Physics (IFLAVOR, ECMS, SVRT, DATE) are module-level constants
    for this qq-bar 5f 1994 sample.
    Returns (loseed, success, message).
    """
    jobdir = os.path.join(root_workdir, 'job_%05d' % loseed)
    if not os.path.exists(jobdir):
        os.makedirs(jobdir)

    logfile     = os.path.join(jobdir, 'chain.log')
    status_file = os.path.join(jobdir, 'STATUS')

    # Safe restart: skip completed jobs
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
    log('Physics: IFLAVOR=%d  ECMS=%s  DATE=%d  SVRT=(%s,%s,%s)' % (
        IFLAVOR, ECMS, GALEPH_DATE, SVRT_X, SVRT_Y, SVRT_Z))

    # ------------------------------------------------------------------
    # Step 1: KINGAL / PYTHIA 6.1
    # ------------------------------------------------------------------
    pyth_text, pythia_epio = make_pythia_cards(loseed, inseed, jobdir)
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

    if last_step == 'kingal':
        if outdir:
            move_to_outdir(pythia_epio, outdir, log)
        write_file(status_file, 'DONE')
        log('Stopping after KINGAL as requested.')
        return (loseed, True, 'success')

    # ------------------------------------------------------------------
    # Step 2: GALEPH (1994 conditions)
    # ------------------------------------------------------------------
    gal_text, galeph_epio = make_galeph_cards(loseed, pythia_epio, jobdir)
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

    if last_step == 'galeph':
        if outdir:
            move_to_outdir(galeph_epio, outdir, log)
        write_file(status_file, 'DONE')
        log('Stopping after GALEPH as requested.')
        return (loseed, True, 'success')

    # ------------------------------------------------------------------
    # Step 3: JULIA
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

    if last_step == 'julia':
        if outdir:
            move_to_outdir(julia_epio, outdir, log)
        write_file(status_file, 'DONE')
        log('Stopping after JULIA as requested.')
        return (loseed, True, 'success')

    # ------------------------------------------------------------------
    # Step 4: MINIPROD
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

        # Remove large intermediate files; keep mini + cards + log
        for f in [pythia_epio, galeph_epio, julia_epio]:
            if os.path.exists(f):
                os.remove(f)
                log('Removed intermediate %s' % f)

        if outdir:
            move_to_outdir(mini_epio, outdir, log)
        else:
            log('Final output: %s' % mini_epio)

        write_file(status_file, 'DONE')
        log('Job complete.')
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
                dbase        = self.opts.dbase,
                root_workdir = self.opts.workdir,
                dry_run      = self.opts.dry_run,
                last_step    = self.opts.last_step,
                outdir       = self.opts.outdir or None,
            )
        except Exception:
            ei = sys.exc_info()
            tb = '%s: %s' % (ei[0], ei[1])
            self.result = (self.loseed, False, 'EXCEPTION: ' + tb)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args():
    p = optparse.OptionParser(usage=__doc__)
    p.add_option('--start',   type='int',   default=0)
    p.add_option('--njobs',   type='int',   default=10)
    p.add_option('--par',     type='int',   default=4)
    p.add_option('--inseed',  type='int',   default=DEFAULT_INSEED)
    p.add_option('--workdir', default='./mcchain_work')
    p.add_option('--dbase',   default=DEFAULT_DBASE)
    p.add_option('--last-step', dest='last_step', default='miniprod',
                 help='Last step: kingal, galeph, julia, miniprod')
    p.add_option('--outdir', dest='outdir', default='',
                 help='Output directory for final EPIO files')
    p.add_option('--dry-run', dest='dry_run',
                 action='store_true', default=False)
    opts, args = p.parse_args()
    return opts


def main():
    opts = parse_args()

    valid_steps = ['kingal', 'galeph', 'julia', 'miniprod']
    if opts.last_step not in valid_steps:
        print 'ERROR: --last-step must be one of: %s' % ', '.join(valid_steps)
        sys.exit(1)

    if not os.path.exists(opts.workdir):
        os.makedirs(opts.workdir)

    # LOSEED is 1-based to avoid seed=0; unique across campaigns via --start
    loseeds = range(opts.start + 1, opts.start + opts.njobs + 1)

    print 'ALEPH MC chain: qq-bar, 5 flavours, 1994 conditions'
    print '  IFLAVOR        : %d  (qq-bar, 5 flavours, no top)' % IFLAVOR
    print '  ECMS           : %s GeV' % ECMS
    print '  Vertex smearing: sx=%.4f sy=%.4f sz=%.2f cm (1994)' % (
        SVRT_X, SVRT_Y, SVRT_Z)
    print '  GALEPH DATE    : %d' % GALEPH_DATE
    print '  Fragmentation  : Pythia 6.1 (G.Rudolph June 2001 tuning)'
    print '  Events per job : %d' % EVENTS_PER_JOB
    print '  Total jobs     : %d  (%d events)' % (
        opts.njobs, opts.njobs * EVENTS_PER_JOB)
    print '  LOSEED range   : %d .. %d' % (loseeds[0], loseeds[-1])
    print '  Parallelism    : %d' % opts.par
    print '  Work dir       : %s' % opts.workdir
    print '  Last step      : %s' % opts.last_step
    print '  Output dir     : %s' % (opts.outdir or '(same as workdir)')
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
        'summary_qqbar5f94_start%d_n%d.txt' % (opts.start, opts.njobs))
    sf = open(summary_path, 'w')
    sf.write('sample=qqbar5f_94 iflavor=%d ecms=%s date=%d\n' % (
        IFLAVOR, ECMS, GALEPH_DATE))
    sf.write('svrt=%s,%s,%s\n' % (SVRT_X, SVRT_Y, SVRT_Z))
    sf.write('start=%d njobs=%d\n' % (opts.start, opts.njobs))
    sf.write('failed_loseeds=%s\n' % ','.join(
        [str(ls) for ls, _ in failed]))
    sf.close()
    print '  Summary written: %s' % summary_path
    print '=' * 60

    if failed:
        sys.exit(1)


if __name__ == '__main__':
    main()
