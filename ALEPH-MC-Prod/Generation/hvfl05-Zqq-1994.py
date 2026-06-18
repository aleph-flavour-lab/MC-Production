#!/usr/bin/env python
"""
ALEPH LEP MC Full Simulation Chain Orchestrator
================================================
Python 2.3 compatible (no subprocess, no generator expressions).

Runs KINGAL(HVFL05) -> GALEPH -> JULIA -> MINIPROD for N jobs of 1000
events each.  Seeds are assigned deterministically by global job index
so successive campaigns never collide:

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
    --inseed  INT   INSEED (first RMAR seed for KINGAL)  (default: 100)
    --ecms    FLOAT Centre-of-mass energy   (default: 91.2)  [banner only]
    --flavor  INT   IFLAVOR                  (default: 1)     [banner only]
    --workdir STR   Root working directory  (default: ./mcchain_work)
    --dbase   STR   Path to ADBS database
    --last-step STR Last step to run: kingal, galeph, julia, miniprod (default: miniprod)
    --outdir    STR Output directory for final EPIO files (default: same as workdir)
    --dry-run       Write cards but do not execute anything

Examples
--------
        # First campaign: 100 jobs = 100k events
        python aleph_mcchain.py --start 0 --njobs 100 --par 8

        # Second campaign: seeds pick up where the first left off
        python aleph_mcchain.py --start 100 --njobs 1000 --par 8

        # Generator level only (fastest — just KINGAL output)
        python aleph_mcchain.py --start 0 --njobs 100 --par 16 --last-step kingal

        # Through detector simulation but skip reconstruction
        python aleph_mcchain.py --start 0 --njobs 100 --par 8 --last-step galeph

        # Through JULIA (full DST) but skip miniprod reduction
        python aleph_mcchain.py --start 0 --njobs 100 --par 8 --last-step julia

        # Full chain (default)
        python aleph_mcchain.py --start 0 --njobs 100 --par 8 --last-step miniprod


        python aleph_mcchain.py \
                --start 0 \
                --njobs 1000 \
                --par 8 \
                --last-step miniprod \
                --outdir /eos/user/h/hfatehi/aleph

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
DEFAULT_INSEED  = 100
DEFAULT_ECMS    = 91.2
DEFAULT_FLAVOR  = 1
DEFAULT_DATE    = 94
DEFAULT_DBASE   = '/cvmfs/aleph.cern.ch/i386_redhat42/dbase/adbs314.daf'

KINHVFL05 = '/cvmfs/aleph.cern.ch/i386_redhat42/kin/kinhvfl05'

# ---------------------------------------------------------------------------
# Card-file generators
# ---------------------------------------------------------------------------

def make_kingal_cards(loseed, inseed, ecms, flavor, workdir):
    """
    Build the HVFL05 KINGAL steering cards.

    The card body contains many literal '%' characters (branching-ratio
    comments such as '= 9 %'), so we must NOT use Python '%' string
    formatting on it.  Instead we substitute three placeholder tokens with
    plain str.replace(), which is Python 2.3 safe:

        __KINGAL_EPIO__  -> per-job EPIO output path
        __NEVT__         -> events to generate (TRIG card)
        __INSEED__       -> first  RMAR seed
        __LOSEED__       -> second RMAR seed (global job index)
    """
    epio_out = os.path.join(workdir, 'kingal_%05d.epio' % loseed)

    cards = """\
KCAR 0 / $TEXT
POFF
*   HERE ARE THE STEERING DATA CARDS        *
*============================================
*     RUN #     RUN'S TITLE
RUN   111  'HEAVY FLAVOR HVFL05:DYMU3+FSR PS+photos,MIXED FLAVORS'
*     FIRST EVENT    LAST EVENT    TO BE GENERATED
TRIG     1   __NEVT__
*    UNIT # / FIRST EVENT   LAST EVENT TO DEBUG
DEBU  6     /     1          5
*  Keep some time at end of job  (IBM 168 seconds)
TIME    10
FILO '__KINGAL_EPIO__|EPIO'
*  use RANMAR generator for random numbers
*  INSEED : first seed (range assigned per institute)
*  LOSEED : second seed (incremented locally for new runs)
*      INSEED          LOSEED (1-30000)
RMAR     __INSEED__             __LOSEED__
*  vertex smearing x     y     z      94 values
SVRT          0.0124   0.0005   0.72
*    IGENE  : qqbar producer code  1 = LUND 7.4+ PARTON SHOWER
*                                  3 = DYMU3   + PARTON SHOWER
*                                 -1 = SINGLE PARTICLE MODE
*    IWEIT  : weight flag  0 = produce unweighted events, 1 = weighted
*    WTMAX  : in case IWEIT=0 required , maximum weight produced by basic
*             generator (used for rejection method).Irrelevant for LUND
*    IPPART : lowest digit ON =Printout of PART and decay tables
*             decimal digit ON = event analysis in terms of particles
*    IGENE IWEIT   WTMAX   IPPART
GHVF    3    0     1.001      10
* LUNTYP  Lund type of particle
* PMIN    minimum momentum(Gev)         PMAX    maximum momentum(Gev)
* CMIN    minimum costheta              CMAX    maximum costheta
* PHMIN   minimum phi (radians)         PHMAX   maximum phi  (radians)
*  LUNTYP   PMIN   PMAX   CMIN   CMAX   PHMIN   PHMAX
GSIN  511    5.     15.    0.     .99    0.      6.2832
* FLAVOR CODE(0=MIX,1=D,2=U,3=S,4=C,5=B,6=T)
* ECMS  Center of mass energy in Gev
*     IFLAVOR     ECMS
GLUN    0          91.2
*         FTYPE   EBEAM  ZMASS  GAMM   SW2  IDEBUG
GDYM      10.     45.6   91.182 2.484  .232     0
* ID2    TAU    FINEXP   POIDS    XK0  QCDFAC    NQUA  IFIRST   NEVMA
   0.     0.      1.       1.    0.003  1.04       5    11      5000
*           HERE ARE THE MODIFICATIONS TO PARAMETERS   *
*=====Mixing==============================================
MSTJ 26 / 0     ! Let HVFL handle the mixing ...not JETSET
* XD,YD Mixing parameters for Bd mesons (both 0. means no mixing)
* XS,YS Mixing parameters for Bs mesons (both 0. means no mixing)
*  Bs mixing : higher chi value ( xs was 2.4 , now tried 5.)
*       xd    yd     xs    ys
GMIX    0.7   0.    5.0    0.
GCPV  1.      0.    1.     0.
GSTA  0     443    310     1.   0.
*=====Vbu transitions=====================================
*   IMATBU  :Lund matrix element (42 or 43) 42=the u and spectator jet
*            collapse into one meson
*                                           43=other mesonic systems can
*            be produced if the available invariant mass is large enough
*   PRBUBC  :probability to get a b-->u transition
*   PARDBU  :PARJ(32) value to be used in conjunction with IMATBU=44 to
*            produce more realistic states (Gev).
*   ITYPBU  : b-->u transition model
*             1 = Free Quark Model
*             2 = NLL QCD corrections with constituant quark masses
*             3 = NLL QCD corrections with current quark masses
*             4 = User's defined final states and branching fractions
*                 (see GBUS card)
*     IMATBU   PRBUBC  PARDBU  ITYPBU
GVBU    43     0.03      1.      1
* following only relevant if ITYPBU =4 is selected
* Be careful to give first neutrino , then lepton, then others in case
* of semi-leptonic decay.It describes the decay of the bbar quark !
* 81 is the spectator quark and will be replaced on the fly by the
* appropriate one .
*       MXEL   Final state particle codes (1---4), branching fraction
GBUS    42    12 -11    -2    81                 0.1
        42    14 -13    -2    81                 0.1
        42    16 -15    -2    81                 0.1
        43     2  -1    -2    81                 0.7
*=====semileptonic B decays models========================
GSEM   1     1
*=====semileptonic radiative decays=======================
*  radiative (semi) leptoic decays of c_ and b_ hadrons
* call PHOTOS for semi-leptonic decays of B and D hadrons
*  IPHO = 0  no internal brem
*       xx1  internal brems on D meson semi lep decay only
*       xx2  internal brems on B meson semi lep decay only
*       xx3  internal brems on both
*       x1x  internal brems on D baryon semi lep decay only
*       x2x  internal brems on B baryon semi lep decay only
*       x3x  internal brems on both
*       1xx  internal brems on Psi and Psi' leptonic decays
GPHO 333
*=====JETSET Set up switches and parameters================
*MSTJ 28 / 2      ! SWITCH ON EXTERNAL LIBRARY FOR TAU DECAYS
MSTJ 107 / 1              ! ISR on for jetset
MSTJ 41 / 2               ! FSR from quarks
MSTJ 115 / 3              ! stores Z0 in history
MSTJ 24 / 2               ! truncated Breit-Wigner for resonances
MSTJ 11 / 3               ! hybrid scheme in longituninal fragmentation
MSTU 16 / 2               ! links hadrons to proper end of the sting
PMA1 6 / 182.             ! top mass
PMA1 7 / 250.          !  nest quark family
PMA1 8 / 350.          !
PMA1 25 / 100.         ! Higgs mass
PMA1 23 / 91.182
PMA1 10221 / 1.    !  Set f0(975) mass to allow KK decays
*-----------------------------------------------------------
*   modification to Lund parameters
*  They come from Gerald's fit and/or  heavy flavor group
*---------------------------------------------------------------
*   QCD FIT FROM G. RUDOLPH  (22/01/96) 4+6 variables, with leading baryon suppr.
*   No extra suppression for c- and b-baryons.
*   parton shower parameters :
MSTJ 46 / 0             ! azimuthal isotropy
PARJ 81 / 0.314         ! LAMBDA QCD was .321 in HVFL04
PARJ 82 / 1.46          ! M min.     was 1.74
*   flavor-neutral fragmentation parameters  :
PARJ 21 / 0.363         ! SIGMA MT   was .333
PARJ 41 / 0.40          ! a          was .5
PARJ 42 / 0.916         ! B          was .973
* hadron production parameters  :
*     modified V/P/T production
PARJ 11 /  0.569        ! FRACTION V/P FOR UD =VUD             WAS 0.516
PARJ 12 /  0.514        ! FRACTION V/P FOR S  =VS              WAS 0.566
PARJ 13 /  0.60         ! FRACTION V/P FOR C AND HEAVIER =VCB  WAS 0.65
PARJ 14 /  0.12         ! FRACTION S 0 L 1 J 1                 was 0.108
PARJ 15 /  0.04         ! FRACTION S 1 L 1 J 0                 was 0.036
PARJ 16 /  0.12         ! FRACTION S 1 L 1 J 1                 was 0.108
PARJ 17 /  0.20         ! FRACTION T/T+V FOR ALL FLAVORS  J 2  WAS 0.18
*  reject 75% of eta' produced by fragmentation ( keep 25%)
PARJ 26 / 0.25                                                 WAS 0.25
*     modified Baryon , strange production etc...
PARJ 1  /  0.1036       ! FRACTION OF BARYON VS MESON PRODUCED WAS 0.095
PARJ 2  /  0.292        ! FRACTION OF S/U                      WAS 0.298
PARJ 3  /  0.634        ! FRACTION OF US/DU                    WAS 0.48
PARJ 4  /  0.05         ! FRACTION OF (QQ)1 /( QQ)0            WAS 0.05
PARJ 19 / 0.40          ! 1st rank baryon suppression          was 1.
MSTJ 12 / 3             ! switch on 1st rank baryon suppression was 0
PARJ 33 /  0.80         ! WMIN IN SYMETRIC LUND FRAGMENTATION  WAS 0.80
*   Use Standard LUND values for  Epsilon_c
*   Measured one for Epsilon_b
*   ( Peterson's fragm. functions params )
PARJ 54 / -0.030         ! EPSILON_C                          was -0.040
PARJ 55 / -0.0045        ! Epsilon_b                          was -0.006
* FRACTION s/u    =P02  for flavor dependence
*         u,d    s      c      b
*GP02     0.292  0.292  0.292  0.292         ! all identical here ...
*..............................................
*  charmed frations as given by P. Colas  2/12/94
*  b       frations as given by S. Schael 2/12/94
* FRACTION V/P+V  =P13  for flavor dependence
*                       c      b
GP13                   0.563   0.73
*         u,d    s       c         b
GP14     0.12    0.12    0.20613   0.25
GP15     0.04    0.04    0.16      0.0278
GP16     0.12    0.12    0.16      0.0833
* FRACTION T/T+V  =P17  for flavor dependence
*         u,d    s      c      b
GP17     0.20   0.20   0.16   0.1389
* FRACTION s/u and T/T+V  at B decay  ( commented ! )
*     i   parj(i)  i  parj(i)
*GBDK  2    0.3    17  0.18
* FRACTION S/U AND T/T+V  AT C DECAY
*     i parj(i)  i  parj(i)
*GCDK  2    0.3  17  0.18             ( commented ! )
* ISPIN = switch for spin effect (on=1/off=0)
* IFORM = switch for form factor in Lam_b --> Lam_c
* W0    = form factor value
*      ISPIN    IFORM   W0
GLAM    0        1      0.89
*------------------------------------------------------------------
*   updates life times     PDG 94 values
*------------------------------------------------------------------
PMA4 130 / 5.1700E-08 ! K0L
PMA4 310 / 0.8926E-10 ! K0S
PMA4 411 / 1.0570E-12 ! D+
PMA4 421 / 0.4150E-12 ! D0
PMA4 431 / 0.4670E-12 ! DS
*------------------------------------------------------------------
*    D*  sector
*------------------------------------------------------------------
PMA1 423 / 2.0067             ! Set D*0 mass
GMOB 423 0.636 0.364          ! PDG 94 values
GMOB 413 0.681 0.308 0.011    ! PDG 94 values
*------------------------------------------------------------------
*    D** sector    masses and widthes as set up by P. Colas 12/12/94
*-----------------the narrow ones----------------------------------
PMA1 415 / 2.463   !  Set D*_2+ mass
PMA2 415 / 0.023   !  Set D*_2+ width
PMA3 415 / 0.100   !  Set D*_2+ truncation
PMA1 425 / 2.459   !  Set D*_20 mass
PMA2 425 / 0.023   !  Set D*_20 width
PMA3 425 / 0.100   !  Set D*_20 truncation
PMA1 435 / 2.573   !  Set D*_2s+ mass (guess)
PMA2 435 / 0.023   !  Set D*_2s+ width(guess)
PMA3 435 / 0.060   !  Set D*_2s+ truncation
PMA1 10413 / 2.425 !  Set D_1+ mass
PMA2 10413 / 0.021 !  Set D_1+ width
PMA3 10413 / 0.100 !  Set D_1+ truncation
PMA1 10423 / 2.421 !  Set D_10 mass
PMA2 10423 / 0.021 !  Set D_10 width
PMA3 10423 / 0.100 !  Set D_10 truncation
PMA1 10433 / 2.535 !  Set D_1s+ mass (guess)
PMA2 10433 / 0.010 !  Set D_1s+ width(guess)  mod by G. Rudolph
PMA3 10433 / 0.020 !  Set D_1s+ truncation      "     March 95
*---------------- the broad ones
PMA1 10411 / 2.415 !  Set D*_0+ mass
PMA2 10411 / 0.060 !  Set D*_0+ width
PMA3 10411 / 0.120 !  Set D*_0+ truncation
PMA1 10421 / 2.419 !  Set D*_00 mass
PMA2 10421 / 0.060 !  Set D*_00 width
PMA3 10421 / 0.120 !  Set D*_00 truncation
PMA1 10431 / 2.529 !  Set D*_0s+ mass (guess)
PMA2 10431 / 0.060 !  Set D*_0s+ width(guess)
PMA3 10431 / 0.120 !  Set D*_0s+ truncation
PMA1 20413 / 2.425 !  Set D*_1+ mass
PMA2 20413 / 0.100 !  Set D*_1+ width
PMA3 20413 / 0.200 !  Set D*_1+ truncation
PMA1 20423 / 2.421 !  Set D*_10 mass
PMA2 20423 / 0.060 !  Set D*_10 width
PMA3 20423 / 0.120 !  Set D*_10 truncation
PMA1 20433 / 2.565 !  Set D*_1s+ mass (guess)
PMA2 20433 / 0.060 !  Set D*_1s+ width(guess)
PMA3 20433 / 0.020 !  Set D*_1s+ truncation
*------------------------------------------------------------------
* Update of the branching ratios of the D** to 70% D , 30% D*
*   P. Colas 2/12/94
*----------------------------------------------------------------------
*        <-D pi----->  <---D* pi-->  <--D* pi pi-> <--D pi pi-->
GMOB 415 0.327  0.163  0.14   0.07   0.060  0.030  0.14   0.07  ! new
GMOB 425 0.327  0.163  0.14   0.07   0.060  0.030  0.14   0.07  ! new
*        <-D K ----->  <---D* K -->
GMOB 435 0.35   0.35   0.15   0.15
* ----------------------------------
* resultats du fit global pour le D+  original BR's , then fitted ones
* ----------------------------------
*1  0.07000   e+    nu_e  K~0         *12 0.07000   mu+   nu_mu K~0
*2  0.06500   e+    nu_e  K*~0        *13 0.06500   mu+   nu_mu K*~0
*3  0.00500   e+    nu_e  K~0         *14 0.00500   mu+   nu_mu K~0
*4  0.00500   e+    nu_e  K-          *15 0.00500   mu+   nu_mu K-
*5  0.01100   e+    nu_e  K*~0        *16 0.01100   mu+   nu_mu K*~0
*6  0.01100   e+    nu_e  K*-         *17 0.01100   mu+   nu_mu K*-
*7  0.00100   e+    nu_e  pi0         *18 0.00100   mu+   nu_mu pi0
*8  0.00100   e+    nu_e  eta         *19 0.00100   mu+   nu_mu eta
*9  0.00100   e+    nu_e  eta'        *20 0.00100   mu+   nu_mu eta'
*10 0.00100   e+    nu_e  rho0        *21 0.00100   mu+   nu_mu rho0
*11 0.00100   e+    nu_e  omega       *22 0.00100   mu+   nu_mu omega
*23 0.02600   K~0   pi+               *24 0.01900   K*~0  pi+
*25 0.06600   K~0   rho+              *26 0.04100   K*~0  rho+
*27 0.04500   K*_1~0pi+               *28 0.07600   K~0   a_1+
*29 0.00730   K~0   K+                *30 0.00470   K*~0  K+
*31 0.00470   K~0   K*+               *32 0.02600   K*~0  K*+
*33 0.00100   pi0   pi+               *34 0.00060   pi0   rho+
*35 0.00660   eta   pi+               *36 0.00500   eta   rho+
*37 0.00300   eta'  pi+               *38 0.00300   eta'  rho+
*39 0.00060   rho0  pi+               *40 0.00060   rho0  rho+
*41 0.00100   omega pi+               *42 0.00100   omega rho+
*43 0.00600   phi   pi+               *44 0.00500   phi   rho+
*45 0.01200   K~0   pi+   pi0         *46 0.00570   K*~0  pi+   rho0
*47 0.06700   K-    pi+   pi+         *48 0.00800   K-    rho+  pi+
*49 0.00220   pi+   pi+   pi-         *50 0.02700   K~0   K+    K~0
*51 0.00400   K-    K+    pi+         *51 0.01900   phi   pi+   pi0
*53 0.01200   K~0   pi+   pi+   pi-   *54 0.00200   K*~0  pi+   pi+ pi-
*55 0.00900   K-    pi+   pi+   pi0   *56 0.02180   pi+   pi+   pi- pi0
*57 0.00100   K-    pi+   pi+   pi+pi-*58 0.02200   K-    pi+   pi+ 2pi0
*59 0.08700   K~0   pi+   pi+   pi-pi0*60 0.00100   K~0   rho0  pi+ pi+0
*61 0.00190   K-    rho0  pi+   pi+pi0*62 0.00150   pi+   pi+   pi+ 2pi-
*63 0.00280   rho0  pi+   pi+   pi-pi0
* added
*64 0.        K*~0(1430) pi+
GADM 411 0 -10311 211 0  0  0
* semileptonic decay modes = 34.90 %
GMOB 411  .0744 .0445 .0043 .0025 .0057 .000  .0077 .0220 .0084 .0016
          .0034 .0744 .0445 .0043 .0025 .0057 .000  .0077 .0220 .0084
          .0016 .0034
* 2-body decay modes       = 40.37 %
          .0274 .0213 .0995 .0229 .0433 .0968 .0076 .0049 .0051 .0176
          .0026 .0007 .0085 .0120 .0090 .0072 .0012 .0006 .0070 .0019
          .0066 .0000
* 3-body decay modes       = 14.10 %
          .0276 .0078 .0496 .0084 .0025 .0257 .0044 .0150
* >3-body decay modes      =  7.30 %
          .0071 .010  .0013 .0028 .0014 .0005 .0431 .0008 .0022 .0019
          .0019
* added                    =  3.33 %
          .0333
*-------------------------------
* resultats du fit global du D0:  original BR's then fitted ones in GMOB
* ------------------------------
*1  0.03400  e+    nu_e    K-       *9  0.03400  mu+   nu_mu   K-
*2  0.02700  e+    nu_e    K*-      *10 0.02700  mu+   nu_mu   K*-
*3  0.00200  e+    nu_e    K~0  pi- *11 0.00200  mu+   nu_mu   K~0  pi-
*4  0.00200  e+    nu_e    K-   pi0 *12 0.00200  mu+   nu_mu   K-   pi0
*5  0.00400  e+    nu_e    K*~0 pi- *13 0.00400  mu+   nu_mu   K*~0 pi-
*6  0.00400  e+    nu_e    K*-  pi0 *14 0.00400  mu+   nu_mu   K*-  pi0
*7  0.00200  e+    nu_e    pi-      *15 0.00200  mu+   nu_mu   pi-
*8  0.00200  e+    nu_e    rho-     *16 0.00200  mu+   nu_mu   rho-
*17 0.03650  K-    pi+              *18 0.04500  K*-   pi+
*19 0.07300  K-    rho+             *20 0.06200  K*-   rho+
*21 0.02100  K~0   pi0              *22 0.02100  K*~0  pi0
*23 0.02100  K*~0  eta              *24 0.00610  K~0   rho0
*25 0.01500  K*~0  rho0             *26 0.02500  K~0   omega
*27 0.00880  K~0   phi              *28 0.07400  K-    a_1+
*29 0.01090  K_1-  pi+              *30 0.00410  K-    K+
*31 0.00200  K*-   K+               *32 0.00350  K-    K*+
*33 0.00110  K~0   K0               *34 0.00100  K*~0  K0
*35 0.00270  K*~0  K*0              *36 0.00160  pi+   pi-
*37 0.00160  pi0   pi0              *38 0.00180  phi   rho0
*39 0.01100  K-    pi+    pi0       *40 0.00630  K-    pi+    rho0
*41 0.00520  K-    K+     K~0       *42 0.01800  K~0   pi+    pi-
*43 0.01600  K*~0  pi+    pi-       *44 0.00340  K-    K0     pi+
*45 0.00360  K*~0  K+     pi-       *46 0.00090  K_S0  K_S0   K_S0
*47 0.00060  phi   pi+    pi-       *48 0.01500  pi+   pi-    pi0
*49 0.09230  K-    pi+    pi0   pi0 *50 0.01800  K-    pi+    pi+   pi-
*51 0.02200  K~0   pi+    pi-   pi0 *52 0.00770  K*~0  pi+    pi-   pi0
*53 0.00900  K~0   K+     K-    pi0 *54 0.00750  pi+   pi+    pi-   pi-
*55 0.02400  K-    pi+    pi+   pi-  pi0
*56 0.00850  K~0   pi+    pi+   pi-  pi-
*57 0.06700  K~0   pi+    pi-   pi0  pi0
*58 0.05110  K~0   rho0   pi0   pi0  pi0
*59 0.01700  pi+   pi+    pi-   pi-  pi0
*60 0.00040  rho0  pi+    pi+   pi-  pi-
*61 0.00280  K+    K-     pi+   pi-  pi0
*62 0.00     K~0   f_0
*63 0.00     K~0   f'_0
*64 0.00     K~0   f_2
*65 0.00     K~0   pi0  pi0
GADM 421   0  -311 10221 0  0   0
GADM 421   0  -311 10331 0  0   0
GADM 421   0  -311   225 0  0   0
GADM 421   0  -311   111 111  0   0
* semileptonic decay modes = 14.96 %
GMOB 421  .0365 .0197 .0077 .0057 .0002 .0002 .0039 .0009 .0365 .0197
          .0077 .0057 .0002 .0002 .0039 .0009
* 2-body decay modes       =  44.01 %
          .0399 .0372 .0919 .0357 .0258 .0337 .0234 .0107 .0155 .0205
          .0085 .0743 .0036 .0055 .0019 .0034 .0011 .000  .0029 .0016
          .0011 .0019
* 3-body decay modes       =  5.96 %
          .0055 .0050 .0050 .0138 .0149 .0017 .0005 .0009 .0008 .0115
* >3-body decay modes      = 32.34 %
          .0372 .0187 .0032 .0159 .0098 .0083 .0356 .0067 .0568 .1068
          .0198 .0005 .0041
* Addendum                 =  2.73 %
          .0056 .0085 .0056 .0076
*-------------------------------
* resultats du fit global du Ds : original BR's then fitted ones in GMOB
* ------------------------------
*1   0.01000    tau+   nu_tau
*2   0.02000    e+     nu_e   eta     *7   0.02000    mu+    nu_mu  eta
*3   0.02000    e+     nu_e   eta'    *8   0.02000    mu+    nu_mu  eta'
*4   0.03000    e+     nu_e   phi     *9   0.03000    mu+    nu_mu  phi
*5   0.00500    e+     nu_e   K+      *10  0.00500    mu+    nu_mu  K+
*6   0.00500    e+     nu_e   K0      *11  0.00500    mu+    nu_mu  K0
*12  0.01500    eta    pi+            *13  0.03700    eta'   pi+
*14  0.02800    phi    pi+            *15  0.07900    eta    rho+
*16  0.09500    eta'   rho+           *17  0.05200    phi    rho+
*18  0.00780    f_0    pi+            *19  0.00100    pi+    pi0
*20  0.00100    rho+   pi0            *21  0.00100    pi+    rho0
*22  0.00100    rho+   rho0           *23  0.02800    K+     K~0
*24  0.03300    K*+    K~0            *25  0.02600    K+     K*~0
*26  0.05000    K*+    K*~0           *27  0.01000    p+     n~0
*28  0.00500    eta    K+             *29  0.00500    eta'   K+
*30  0.00500    phi    K+             *31  0.00500    eta    K*+
*32  0.25000    u      d~     s   s~  *33  0.09520    u      d~
*34  0.         mu+    nu_mu
*35  0.         omega  pi+            *36  0.         K0     pi+
*37  0.         K+     K-     pi+     *38  0.         phi    pi+    pi0
*39  0.         pi+    pi+    pi-     *40  0.         eta    pi+    pi0
*41  0.         eta'   pi+    pi0     *42  0.         K+     pi+    pi-
*43  0.         K+     K-     pi+    pi0
*44  0.         K+     K0~    pi+    pi-
*45  0.         K0     K-     pi+    pi+
*46  0.         phi    pi+    pi-    pi+
*47  0.         pi+    pi+    pi-    pi0
*48  0.         K+     K-     pi+    pi+   pi-
*49  0.         pi+    pi+    pi+    pi-   pi-
*50  0.         pi+    pi+    pi+    pi-   rho+
GADM 431   0  -13  14     0  0   0
GADM 431   0  223  211    0  0   0
GADM 431   0  311  211    0  0   0
GADM 431   0  321 -321  211  0   0
GADM 431   0  333  211  111  0   0
GADM 431   0  211  211 -211  0   0
GADM 431   0  221  211  111  0   0
GADM 431   0  331  211  111  0   0
GADM 431   0  321  211 -211  0   0
GADM 431   0  321 -321  211  111 0
GADM 431   0  321 -311  211 -211 0
GADM 431   0  311 -321  211  211 0
GADM 431   0  333  211 -211  211 0
GADM 431   0  211  211 -211  111 0
GADM 431   0  321 -321  211  211 -211
GADM 431   0  211  211  211 -211 -211
GADM 431   0  211  211  211 -211 -213
* -----------------------------------------------
* leptonic decay modes      =  1.28 %
GMOB 431  .0128
* semileptonic decay modes  = 19.26 %
          .0452 .0261 .0180 .0013 .0057 .0452 .0261 .0180 .0013 .0057
* 2-body decay modes       = 60.06 %
          .0194 .0469 .0345 .111  .118  .0561 .0099 .001  .0029 .0003
          .001  .0364 .0449 .0323 .0548 .0133 .0053 .0047 .0023 .0056
* spectator diagrams
          .0    .0
* modes added
* 2-body decay modes       =  1.41 %
          .0061 .0052 .0028
* 3-body decay modes       =  4.42 %
          .0081 .00   .0097 .0135 .0104 .0025
* >3-body decay modes      = 13.57 %
          .0001 .0108 .0159 .0184 .0011 .0031 .0034 .0829
*
*----------------------------------------------------------------------
*  UPDATED BRANCHING RATIOS OF THE J/PSI KF=443
*   941216   BY D. ROUSSEAU
*----------------------------------------------------------------------
*        1 = e+ e-      2 = mu+ mu-    3 = hadrons
GMOB 443  0.06           0.06           0.88
*----------------------------------------------------------------------
*   /\c  sector   old scheme then modifications from Fit results GMOB
*------------------------------------------------------------------
*1   0.01800   e+    nu_e   Lambda0  *8   0.01800   mu+   nu_mu  Lambda0
*2   0.00500   e+    nu_e   Sigma0   *9   0.00500   mu+   nu_mu  Sigma0
*3   0.00500   e+    nu_e   Sigma*0  *10  0.00500   mu+   nu_mu  Sigma*0
*4   0.00300   e+    nu_e   n0       *11  0.00300   mu+   nu_mu  n0
*5   0.00200   e+    nu_e   Delta0   *12  0.00200   mu+   nu_mu  Delta0
*6   0.00600   e+    nu_e   p+  pi-  *13  0.00600   mu+   nu_mu  p+  pi-
*7   0.00600   e+    nu_e   n0  pi0  *14  0.00600   mu+   nu_mu  n0  pi0
*15  0.00660   Delta++    K-         *16  0.02500   Delta++    K*-
*17  0.01600   p+         K~0        *18  0.00880   p+         K*~0
*19  0.00500   Delta+     K~0        *20  0.00500   Delta+     K*~0
*21  0.00580   Lambda0    pi+        *22  0.00500   Lambda0    rho+
*23  0.00550   Sigma0     pi+        *24  0.00400   Sigma0     rho+
*25  0.00400   Sigma*0    pi+        *26  0.00400   Sigma*0    rho+
*27  0.00400   Sigma+     pi0        *28  0.00200   Sigma+     eta
*29  0.00200   Sigma+     eta'       *30  0.00400   Sigma+     rho0
*31  0.00400   Sigma+     omega
*32  0.00300   Sigma*+    pi0        *33  0.00200   Sigma*+    eta
*34  0.00300   Sigma*+    rho0       *35  0.00300   Sigma*+    omega
*36  0.00200   Xi0        K+         *37  0.00200   Xi0        K*+
*38  0.00200   Xi*0       K+
*39  0.00100   Delta++    pi-        *40  0.00100   Delta++    rho-
*41  0.00200   p+         pi0        *42  0.00100   p+         eta
*43  0.00100   p+         eta'       *44  0.00200   p+         rho0
*45  0.00200   p+         omega      *46  0.00130   p+         phi
*47  0.00180   p+         f_0
*48  0.00100   Delta+     pi0        *49  0.00100   Delta+     eta
*50  0.00100   Delta+     eta'       *51  0.00100   Delta+     rho0
*52  0.00100   Delta+     omega
*53  0.00300   n0         pi+        *54  0.00300   n0         rho+
*55  0.00300   Delta0     pi+        *56  0.00300   Delta0     rho+
*57  0.00500   Lambda0    K+         *58  0.00500   Lambda0    K*+
*59  0.00200   Sigma0     K+         *60  0.00200   Sigma0     K*+
*61  0.00100   Sigma*0    K+         *62  0.00100   Sigma*0    K*+
*63  0.00200   Sigma+     K0         *64  0.00200   Sigma+     K*0
*65  0.00100   Sigma*+    K0         *66  0.00100   Sigma*+    K*0
*67  0.24320   u          d~      s  *68  0.05700   u          d~      s
*69  0.03500   u          s~      s  *70  0.03500   u          d~      d
*71  0.15000   s          uu_1       *72  0.07500   u          su_0
*73  0.07500   u          su_1       *74  0.03000   d          uu_1
*75  0.01500   u          ud_0       *76  0.01500   u          ud_1
*77  0.        Sigma-     pi+   pi+  *78  0.        Sigma+     phi
*----------------------------------------------------------------------
GADM   4122   0 3112 211 211 0  0
GADM   4122   0 3222 333   0 0  0
GMOB   4122
*   semi-leptonic          =  9 %
   .0120 .0010 .0010 .0060 .0070 .0060 .0120 .0120 .0010 .0010
   .0060 .0070 .0060 .0120
*   2-body decay modes     = 21.51 %
   .0070 .0070 .0210 .0160 .0050 .0050 .0079 .0040 .0087 .0040
   .0040 .0040 .0087 .0020 .0020 .0120 .0240 .0030 .0020 .0030
   .0040 .0034 .0020 .0023 .0010 .0010 .0020 .0010 .0010 .0020
   .0020 .0017 .0024 .0010 .0010 .0010 .0010 .0010 .0030 .0030
   .0030 .0030 .0050 .0050 .0020 .0020 .0010 .0010 .0020 .0020
   .0010 .0010
*   diagrams decays        = 69.03 %
   .2403 .0600 .0240 .0440 .0000 .1310 .1240 .0040 .0200  .0430
*   Sigma- pi_ pi+ & Sigma+ phi  0.46 %
   .0016 .0030
*----------------------------------------------------------------------
*    B   sector
*------------------------------------------------------------------
PMA1 511   / 5.2787  !  Set B0   mass   |
PMA1 521   / 5.2787  !  Set B+   mass   | Mofified B,B* and B** masses
PMA1 531   / 5.3830  !  Set Bs   mass   | and widthes
PMA1 513   / 5.3247  !  Set B*0  mass   | as provided by S. Schael
PMA1 523   / 5.3247  !  Set B*+  mass   | 2/12/94
PMA1 533   / 5.429   !  Set B*s  mass   |
PMA1 10513 / 5.7267  !  Set B_1 0 mass  |
PMA2 10513 / 0.0200  !  Set B_1 0 width |
PMA1 10523 / 5.7267  !  Set B_1 + mass  |
PMA2 10523 / 0.0200  !  Set B_1 + width |
PMA1 10533 / 5.8530  !  Set B_1s+ mass  |
PMA2 10533 / 0.0010  !  Set B_1s+ width |
PMA3 10533 / 0.0010  !  Set B_1s+ trunc.|   mod by G.Rudolph march 95
PMA1 10511 / 5.6587  !  Set B*_0 0 mass |
PMA2 10511 / 0.0720  !  Set B*_0 0 width|
PMA1 10521 / 5.6587  !  Set B*_0 + mass |
PMA2 10521 / 0.0720  !  Set B*_0 + width|
PMA1 10531 / 5.7730  !  Set B*_0s+ mass |
PMA2 10531 / 0.0010  !  Set B*_0s+ width|
PMA1 20513 / 5.6587  !  Set B*_1 0 mass |
PMA2 20513 / 0.0720  !  Set B*_1 0 width|
PMA1 20523 / 5.6587  !  Set B*_1 + mass |
PMA2 20523 / 0.0720  !  Set B*_1 + width|
PMA1 20533 / 5.7730  !  Set B*_1s+ mass |
PMA2 20533 / 0.0010  !  Set B*_1s+ width|
PMA1 515   / 5.7387  !  Set B*_2 0  mass|
PMA2 515   / 0.0240  !  Set B*_2 0 width|
PMA1 525   / 5.7387  !  Set B*_2 +  mass|
PMA2 525   / 0.0240  !  Set B*_2 + width|
PMA1 535   / 5.8650  !  Set B*_2s0  mass|
PMA2 535   / 0.0020  !  Set B*_2s0 width|
PMA3 535   / 0.0040  !  Set B*_2s0 trunc.| mod B.Bloch Jan 96
*------------------------------------------------------------------
*   Updated branching ratios of the B* and B**
*   set up  from S. Schael 2/12/94
*----------------------------------------------------------------------
*   B_1 0   -->   B*+ pi-    B*0  pi0
GMOB 10513           0.667       0.333
*   B_1 +   -->   B*0 pi+    B*+  pi0
GMOB 10523           0.667       0.333
*   B_1s 0  -->   B*+ K-     B*0  K0bar
GMOB 10533           0.667        0.333
*   B*_0 0  -->   B+ pi-     B0   pi0
GMOB 10511           0.667        0.333
*   B*_0 +  -->   B0 pi+     B+  pi0
GMOB 10521           0.667        0.333
*   B*_0s0  -->   B*s gamma
GRPL 10531 1 1 0 533 22 0 0 0
GMOB 10531           1.           0.
*   B*_1 0  -->   B*+ pi-    B*0  pi0
GMOB 20513           0.667        0.333
*   B*_1 +  -->   B*0 pi+    B*+  pi0
GMOB 20523           0.667        0.333
*   B*_1s0  -->   Bs gamma    B*s gamma
GRPL 20533 1 1 0 531 22 0 0 0
GRPL 20533 2 1 0 533 22 0 0 0
GMOB 20533    0.5    0.5
*   B*_2 0   -->  B+  pi-    B0  pi0  B*+ pi-  B*0  pi0  3-body modes
GMOB   515           0.3335   0.1665   0.3335   0.1665   0. 0. 0. 0.
*   B*_2 +   -->  B0  pi+    B+  pi0  B*0 pi+  B*+  pi0  3-body modes
GMOB   525           0.3335   0.1665   0.3335   0.1665   0. 0. 0. 0.
*   B*_2s 0  -->  B+  K-    B0  K0bar  B*+ K-  B*0  K0bar
GMOB   535           0.3335   0.1665   0.3335   0.1665
*------------------------------------------------------------------
*   Updated masses and branching ratios in the Bc sector
*   set up  from D. Rousseau 16/12/94
* width below 1 mev and mass below B+ D threshold
*----------------------------------------------------------------------
PMA1 541 / 6.264      ! set Bc+ mass
PMA1 543 / 6.337      ! set B*c+ mass
PMA1 10541 / 6.700    ! set B*_0c+ mass
PMA2 10541 / 0.
PMA3 10541 / 0.
PMA1 20543 / 6.736    ! set B*_1c+ mass
PMA2 20543 / 0.
PMA3 20543 / 0.
PMA1 10543 / 6.736    ! set B_1c+ mass
PMA2 10543 / 0.
PMA3 10543 / 0.
PMA1 545 / 6.736      ! set B*_2c+ mass
PMA2 545 / 0.
PMA3 545 / 0.
* P wave Bc state ---> S wave Bc + gamma
GRPL 10541 1 1 0 543 22 0 0 0
GMOB 10541 1.  0.
GRPL 20543 1 1 0 541 22 0 0 0
GMOB 20543 1.  0.
GRPL 10543 1 1 0 543 22 0 0 0
GMOB 10543 1.  0.
GRPL 545   1 1 0 543 22 0 0 0
GMOB 545   1.  0.  0.  0.
*------------------------------------------------------------------
*   Updated branching ratios of the B mesons
*   results from C. Goy , F. Saadi Nov-Dec  94
*   Modify the Decay Scheme of B meson in order to generate
*   2-body final state according to Bauer-Stech-Wirbel computation
* with fixed values  f_D  = 240 mev    and f_Ds = 270 mev
*----------------------------------------------------------------------
*   B0 meson   original Sjostrand values as given  , modified on GMOB
*   a1 = 1.23+-0.05   a2 = 0.29+-0.02
*----------------------------------------------------------------------
*1  0.02000  nu_e   e+   D-       *7  0.02000  nu_mu  mu+  D-
*2  0.05500  nu_e   e+   D*-      *8  0.05500  nu_mu  mu+  D*-
*3  0.00500  nu_e   e+   D_1-     *9  0.00500  nu_mu  mu+  D_1-
*4  0.00500  nu_e   e+   D*_0-    *10 0.00500  nu_mu  mu+  D*_0-
*5  0.00800  nu_e   e+   D*_1-    *11 0.00800  nu_mu  mu+  D*_1-
*6  0.01200  nu_e   e+   D*_2-    *12 0.01200  nu_mu  mu+  D*_2-
*13 0.01000  nu_tau tau+ D-       *14 0.03000  nu_tau tau+ D*-
*15 0.00350    D-    pi+          *18 0.00420    D*-   pi+
*16 0.01100    D-    rho+         *19 0.00900    D*-   rho+
*17 0.00550    D-    a_1+         *20 0.01800    D*-   a_1+
*21 0.01500    D-    D_s+         *23 0.01350    D*-   D_s+
*22 0.01850    D-    D*_s+        *24 0.02500    D*-   D*_s+
*25 0.00040    eta_c K0           *26 0.00070    eta_c K*0
*27 0.00080    J/psi K0           *28 0.00140    J/psi K*0
*29 0.00190    chi_1cK0           *30 0.00250    chi_1cK*0
*31 0.42910    u     d~  c~  d    *32 0.08000    u     c~  d~  d
*33 0.07000    c     s~  c~  d    *34 0.02000    c     c~  s~  d
*35 0.01500    u     d~  u~  d    *36 0.00500    c     s~  u~  d
* added
*37 0.00000    Psi'  K0           *38 0.00000    Psi'  K*0
*39 0.00       D-    D+           *43 0.00       D*-   D+
*40 0.00       D-    D*+          *44 0.00       D*-   D*+
*41 0.00       D-    K+           *45 0.00       D*-   K+
*42 0.00       D-    K*+          *46 0.00       D*-   K*+
*47 0.00       D0~   pi0          *51 0.00       D*0~  pi0
*48 0.0        D0~   eta          *52 0.00       D*0~  eta
*49 0.0        D0~   rho0         *53 0.0        D*0~  rho0
*50 0.0        D0~   omega        *54 0.0        D*0~  omega
*55 0.        Sigc~-- Delta++ Pi0 *56 0.        Sigc~-  Delta++ Pi-
*57 0.        Sigc~-  Delta+  Pi0 *58 0.        Sigc~0  Delta+  Pi-
*59 0.        Sigc~0  Delta0  Pi0
*60 0.        nu_e   e+   D*- pi0 *61 0.0      nu_mu  mu+  D*- pi0
*62 0.        nu_e   e+   D*0 pi- *63 0.0      nu_mu  mu+  D*0 pi-
*
*----------------------------------------------------------------------
GRPL  511 33 1  13  4    -3  -4      1     0
GRPL  511 34 1  48  1    -3  -4      4     0
GADM  511    0  30443   311   0      0     0
GADM  511    0  30443   313   0      0     0
GADM  511    0   -411   411   0      0     0
GADM  511    0   -411   413   0      0     0
GADM  511    0   -411   321   0      0     0
GADM  511    0   -411   323   0      0     0
GADM  511    0   -413   411   0      0     0
GADM  511    0   -413   413   0      0     0
GADM  511    0   -413   321   0      0     0
GADM  511    0   -413   323   0      0     0
GADM  511    0   -421   111   0      0     0
GADM  511    0   -421   221   0      0     0
GADM  511    0   -421   113   0      0     0
GADM  511    0   -421   223   0      0     0
GADM  511    0   -423   111   0      0     0
GADM  511    0   -423   221   0      0     0
GADM  511    0   -423   113   0      0     0
GADM  511    0   -423   223   0      0     0
GADM  511    0  -4222  2224   111    0     0
GADM  511    0  -4212  2224  -211    0     0
GADM  511    0  -4212  2214   111    0     0
GADM  511    0  -4112  2214  -211    0     0
GADM  511    0  -4112  2114   111    0     0
GADM  511    0     12   -11  -413   111    0
GADM  511    0     12   -11  -423  -211    0
GADM  511    0     14   -13  -413   111    0
GADM  511    0     14   -13  -423  -211    0
GMOB 511
* semileptonic  e and mu   = 19.06 %   with added modes :20.60 %
.0219  .0657  .00193 .00064 .00193 .0032  .0219  .0657 .00193 .00064
.00193 .00320
* semi lep tau             =  4    %
.01    .03
* 2 body                   = 10.172 %
.00262 .00677 .00677 .00262 .00895 .00895 .01165 .00739 .00818 .03050
.00160 .00070 .00094 .00138 .00100 .00170
* diag decays              = 59.608 %
.4326  .08    .07    .01348 .0     .0
* added 2 body             =  0.520 %
.00032 .00062 .00038 .00026 .00021 .00036 .00028 .00095 .00021 .00048
.00030 .00008 .00005 .00005 .00025 .00008 .00016 .00016
* 3 body baryonic          =  5.1 %
.004   .0085  .017   .0085  .013
* added semileptonic e ,mu = 1.54 %
.00385 .00385 .00385 .00385
*----------------------------------------------------------------------
*   B+ meson   original Sjostrand values as given  , modified on GMOB
*   a1 = 1.37+-0.06   a2 = 0.30+-0.02
*----------------------------------------------------------------------
*1  0.02000  nu_e   e+   D~0      *7  0.02000  nu_mu  mu+  D~0
*2  0.05500  nu_e   e+   D*~0     *8  0.05500  nu_mu  mu+  D*~0
*3  0.00500  nu_e   e+   D_1~0    *9  0.00500  nu_mu  mu+  D_1~0
*4  0.00500  nu_e   e+   D*_0~0   *10 0.00500  nu_mu  mu+  D*_0~0
*5  0.00800  nu_e   e+   D*_1~0   *11 0.00800  nu_mu  mu+  D*_1~0
*6  0.01200  nu_e   e+   D*_2~0   *12 0.01200  nu_mu  mu+  D*_2~0
*13 0.01000  nu_tau tau+ D~0      *14 0.03000  nu_tau tau+ D*~0
*15 0.00350    D~0   pi+          *18 0.00420    D*~0  pi+
*16 0.01100    D~0   rho+         *19 0.00900    D*~0  rho+
*17 0.00550    D~0   a_1+         *20 0.01800    D*~0  a_1+
*21 0.01500    D~0   D_s+         *23 0.01350    D*~0  D_s+
*22 0.01850    D~0   D*_s+        *24 0.02500    D*~0  D*_s+
*25 0.00040    eta_c K+           *26 0.00070    eta_c K*+
*27 0.00080    J/psi K+           *28 0.00140    J/psi K*+
*29 0.00190    chi_1cK+           *30 0.00250    chi_1cK*+
*31 0.42910    u     d~  c~  u    *32 0.08000    u     c~  d~  u
*33 0.07000    c     s~  c~  u    *34 0.02000    c     c~  s~  u
*35 0.01500    u     d~  u~  u    *36 0.00500    c     s~  u~  u
* added
*37 0.00000    Psi'  K+           *38 0.00000    Psi'  K*+
*39 0.00       D~0   D+           *43 0.00       D*~0  D+
*40 0.00       D~0   D*+          *44 0.00       D*~0  D*+
*41 0.00       D~0   K+           *45 0.00       D*~0  K+
*42 0.00       D~0   K*+          *46 0.00       D*~0  K*+
*47 0.        Sigc~-- Delta++ Pi+ *48 0.        Sigc~-  Delta++ Pi0
*49 0.        Sigc~-  Delta+  Pi+ *50 0.        Sigc~0  Delta+  Pi0
*51 0.        Sigc~0  Delta0  Pi+
*52 0.        nu_e   e+   D*- pi+ *54 0.02000  nu_mu  mu+  D*- pi+
*53 0.        nu_e   e+   D*0 pi0 *55 0.02000  nu_mu  mu+  D*0 pi0
*
*----------------------------------------------------------------------
GRPL  521 33 1  13  4    -3  -4      2     0
GRPL  521 34 1  48  2    -3  -4      4     0
GADM  521    0  30443   321   0      0     0
GADM  521    0  30443   323   0      0     0
GADM  521    0   -421   411   0      0     0
GADM  521    0   -421   413   0      0     0
GADM  521    0   -421   321   0      0     0
GADM  521    0   -421   323   0      0     0
GADM  521    0   -423   411   0      0     0
GADM  521    0   -423   413   0      0     0
GADM  521    0   -423   321   0      0     0
GADM  521    0   -423   323   0      0     0
GADM  521    0  -4222  2224   211    0     0
GADM  521    0  -4212  2224   111    0     0
GADM  521    0  -4212  2214   211    0     0
GADM  521    0  -4112  2214   111    0     0
GADM  521    0  -4112  2114   211    0     0
GADM  521    0     12   -11  -413   211    0
GADM  521    0     12   -11  -423   111    0
GADM  521    0     14   -13  -413   211    0
GADM  521    0     14   -13  -423   111    0
GMOB 521
* semileptonic  e and mu   = 19.06 %   with added modes :20.60 %
.0219  .0657  .00193 .00064 .00193 .0032 .0219  .0657 .00193 .00064
.00193 .00320
* semi lep tau             =  4    %
.01    .03
* 2 body                   = 14.165 %
.00526 .0103  .01030 .00641 .01490 .01490 .01440 .00982 .01013 .03770
.0016  .0007  .00103 .00150 .00100 .00170
* diag decays              = 54.517 %
.36869 .08    .07    .01348 .0    .0
* 2 body   added           =  1.618 %
.00035  0.00069 .00045 .00033 .00047 .00052 .00035 .01180 .00044 .00078
* 3 body baryonic          =  5.1 %
.004   .0085  .017   .0085  .013
* added semileptonic e ,mu = 1.54 %
.00385 .00385 .00385 .00385
*----------------------------------------------------------------------
*   Bs0 meson  Original values from JETSET , then fitted ones on GMOB
*   a1 = 1.23+-0.05   a2 = 0.29+-0.02
*----------------------------------------------------------------------
*1  0.02000  nu_e   e+   Ds~0      *7  0.02000  nu_mu  mu+  Ds~0
*2  0.05500  nu_e   e+   Ds*~0     *8  0.05500  nu_mu  mu+  Ds*~0
*3  0.00500  nu_e   e+   Ds_1~0    *9  0.00500  nu_mu  mu+  Ds_1~0
*4  0.00500  nu_e   e+   Ds*_0~0   *10 0.00500  nu_mu  mu+  Ds*_0~0
*5  0.00800  nu_e   e+   Ds*_1~0   *11 0.00800  nu_mu  mu+  Ds*_1~0
*6  0.01200  nu_e   e+   Ds*_2~0   *12 0.01200  nu_mu  mu+  Ds*_2~0
*13 0.01000  nu_tau tau+ Ds~0      *14 0.03000  nu_tau tau+ Ds*~0
*15 0.00350    Ds~-   pi+          *18 0.00420    Ds*~-  pi+
*16 0.01100    Ds~-   rho+         *19 0.00900    Ds*~-  rho+
*17 0.00550    Ds~-   a_1+         *20 0.01800    Ds*~-  a_1+
*21 0.01500    Ds~-   D_s+         *23 0.01350    Ds*~-  D_s+
*22 0.01850    Ds~-   D*_s+        *24 0.02500    Ds*~-  D*_s+
*25 0.00020    eta_c  eta          *28 0.00040    J/psi  eta
*26 0.00020    eta_c  eta'         *29 0.00040    J/psi  eta'
*27 0.00070    eta_c  phi          *30 0.00140    J/psi  phi
*31 0.00100    chi_1c eta
*32 0.00090    chi_1c eta'
*33 0.00250    chi_1c phi
*34 0.42910    u     d~  c~  s    *35 0.08000    u     c~  d~  s
*36 0.07000    c     s~  c~  s    *37 0.02000    c     c~  s~  s
*38 0.01500    u     d~  u~  s    *39 0.00500    c     s~  u~  s
* added
*40 0.00000    Psi'  eta
*41 0.00000    Psi'  eta'
*42 0.00000    Psi'  phi
*43 0.00       D~s-  D+           *47 0.00       D*~-  D+
*44 0.00       D~s-  D*+          *48 0.00       D*~-  D*+
*45 0.00       D~s-  K+           *49 0.00       D*~-  K+
*46 0.00       D~s-  K*+          *50 0.00       D*~-  K*+
*51 0.00       D~0   K0           *53 0.00       D*~0  K0
*52 0.00       D~0   K*0          *54 0.00       D*~0  K*0
*55 0.        Sigc~-- Delta++  K0 *56 0.        Sigc~-  Delta++  K-
*57 0.        Sigc~-  Delta+   K0 *58 0.        Sigc~0  Delta+   K-
*59 0.        Sigc~0  Delta0   K0
*60 0.        nu_e   e+   D*-  K0 *61 0.02000  nu_mu  mu+  D*-  K0
*62 0.        nu_e   e+   D*0  K- *63 0.02000  nu_mu  mu+  D*0  K-
*
*----------------------------------------------------------------------
GRPL  531 36 1  13  4    -3  -4      3     0
GRPL  531 37 1  48  3    -3  -4      4     0
GADM  531    0  30443   221   0      0     0
GADM  531    0  30443   331   0      0     0
GADM  531    0  30443   333   0      0     0
GADM  531    0   -431   411   0      0     0
GADM  531    0   -431   413   0      0     0
GADM  531    0   -431   321   0      0     0
GADM  531    0   -431   323   0      0     0
GADM  531    0   -433   411   0      0     0
GADM  531    0   -433   413   0      0     0
GADM  531    0   -433   321   0      0     0
GADM  531    0   -433   323   0      0     0
GADM  531    0   -421   311   0      0     0
GADM  531    0   -421   313   0      0     0
GADM  531    0   -423   311   0      0     0
GADM  531    0   -423   313   0      0     0
GADM  531    0  -4222  2224   311    0     0
GADM  531    0  -4212  2224  -321    0     0
GADM  531    0  -4212  2214   311    0     0
GADM  531    0  -4112  2214  -321    0     0
GADM  531    0  -4112  2114   311    0     0
GADM  531    0     12   -11  -413   311    0
GADM  531    0     12   -11  -423  -321    0
GADM  531    0     14   -13  -413   311    0
GADM  531    0     14   -13  -423  -321    0
GMOB 531
* semileptonic  e and mu   = 19.06 %   with added modes :20.60 %
 .0219  .0657  .00193 .00064 .00193 .00320   .0219  .0657 .00193 .00064
 .00193 .00320
* semi lep tau             =  4    %
 .01    .03
* 2 body                   = 10.926 %
 .00284 .00764 .00764 .00284 .00917 .00917 .0124  .00818 .00868 .0337
 .0008  .0008  .0007  .00041 .00041 .00118 .0005  .0005  .0017
* diag decays              = 58.807 %
 .41159 .08    .07      .01348 .0    .0
* 2 body   added           =  0.567 %
 .00016 .00016 .00062 .00042 .00028 .00023 .00040 .00030 .00093 .00022
 .00052 .00062 .00005 .00050 .00026
* 3 body baryonic          =  5.1 %
.004   .0085  .017   .0085  .013
* added semileptonic e ,mu = 1.54 %
 .00385 .00385 .00385  .00385
END$
ENDQ
"""

    cards = cards.replace('__NEVT__', '%d' % EVENTS_PER_JOB)
    cards = cards.replace('__INSEED__', '%d' % inseed)
    cards = cards.replace('__LOSEED__', '%d' % loseed)
    cards = cards.replace('__KINGAL_EPIO__', epio_out)
    return cards, epio_out


def make_galeph_cards(loseed, kingal_epio, workdir):
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
""" % {'fili': kingal_epio, 'filo': epio_out,
       'nevt': EVENTS_PER_JOB, 'date': DEFAULT_DATE}
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
    """Move src file to outdir, return destination path."""
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

def run_job(loseed, inseed_base, ecms, flavor, dbase, root_workdir, dry_run, last_step='miniprod', outdir=None):
    """
    Execute the chain up to last_step for one LOSEED value.
    last_step: kingal | galeph | julia | miniprod
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
    # Step 1 : KINGAL / HVFL05
    # ------------------------------------------------------------------
    # Both RANMAR seeds vary per job, keyed to the global job index:
    #   LOSEED = loseed              (global job index, 1-based)
    #   INSEED = inseed_base + loseed
    # This makes every job's (INSEED, LOSEED) pair unique, with both
    # numbers distinct from job to job and no collisions across campaigns
    # (the index is driven by --start).  RANMAR valid ranges:
    #   IJ (INSEED) in 0..31328 , KL (LOSEED) in 0..30081 (card says 1..30000)
    inseed = inseed_base + loseed
    if inseed > 31328 or loseed > 30000:
        msg = ('seed out of RANMAR range: INSEED=%d (max 31328), '
               'LOSEED=%d (max 30000)' % (inseed, loseed))
        log(msg)
        write_file(status_file, 'FAILED:SEED_RANGE')
        return (loseed, False, msg)
    log('Seeds: INSEED=%d LOSEED=%d' % (inseed, loseed))

    card_text, kingal_epio = make_kingal_cards(
        loseed, inseed, ecms, flavor, jobdir)
    card_path = os.path.join(jobdir, 'hvfl05_%05d.cards' % loseed)
    write_file(card_path, card_text)
    log('Wrote %s' % card_path)

    if not dry_run:
        env = os.environ.copy()
        env['KINGALCARDS'] = card_path
        rc = run_cmd(KINHVFL05, env, logfile)
        if rc != 0:
            msg = 'KINGAL failed (rc=%d)' % rc
            log(msg)
            write_file(status_file, 'FAILED:KINGAL')
            return (loseed, False, msg)
        if not os.path.exists(kingal_epio):
            msg = 'KINGAL produced no output: %s' % kingal_epio
            log(msg)
            write_file(status_file, 'FAILED:KINGAL_OUTPUT')
            return (loseed, False, msg)
        log('KINGAL OK -> %s' % kingal_epio)
    else:
        log('[DRY-RUN] KINGALCARDS=%s ; %s' % (card_path, KINHVFL05))

    if last_step == 'kingal':
        if outdir:
            move_to_outdir(kingal_epio, outdir, log)
        write_file(status_file, 'DONE')
        log('Stopping after KINGAL as requested.')
        return (loseed, True, 'success')

    # ------------------------------------------------------------------
    # Step 2 : GALEPH
    # ------------------------------------------------------------------
    gal_text, galeph_epio = make_galeph_cards(
        loseed, kingal_epio, jobdir)
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

    if last_step == 'julia':
        if outdir:
            move_to_outdir(julia_epio, outdir, log)
        write_file(status_file, 'DONE')
        log('Stopping after JULIA as requested.')
        return (loseed, True, 'success')

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
        for f in [kingal_epio, galeph_epio, julia_epio]:
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
                inseed_base  = self.opts.inseed,
                ecms         = self.opts.ecms,
                flavor       = self.opts.flavor,
                dbase        = self.opts.dbase,
                root_workdir = self.opts.workdir,
                dry_run      = self.opts.dry_run,
                last_step    = self.opts.last_step,
                outdir       = self.opts.outdir or None,
            )
        except Exception:
            import sys as _sys
            ei = _sys.exc_info()
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
    p.add_option('--ecms',    type='float', default=DEFAULT_ECMS)
    p.add_option('--flavor',  type='int',   default=DEFAULT_FLAVOR)
    p.add_option('--workdir', default='./mcchain_work')
    p.add_option('--dbase',   default=DEFAULT_DBASE)
    p.add_option('--last-step', dest='last_step', default='miniprod',
                 help='Last step: kingal, galeph, julia, miniprod')
    p.add_option('--outdir', dest='outdir', default='',
                 help='Output directory for final EPIO files (e.g. /eos/user/h/hfatehi/aleph/mc)')
    p.add_option('--dry-run', dest='dry_run', action='store_true', default=False)
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

    # LOSEED = global job index, 1-based to avoid seed=0
    loseeds = range(opts.start + 1, opts.start + opts.njobs + 1)

    print 'ALEPH MC chain orchestrator (KINGAL = HVFL05)'
    print '  Events per job : %d' % EVENTS_PER_JOB
    print '  Total jobs     : %d  (%d events)' % (
        opts.njobs, opts.njobs * EVENTS_PER_JOB)
    print '  LOSEED range   : %d .. %d' % (loseeds[0], loseeds[-1])
    print '  INSEED range   : %d .. %d  (base %d + LOSEED)' % (
        opts.inseed + loseeds[0], opts.inseed + loseeds[-1], opts.inseed)
    print '  Parallelism    : %d' % opts.par
    print '  Work dir       : %s' % opts.workdir
    print '  Last step      : %s' % opts.last_step
    _outdir_display = opts.outdir or '(same as workdir)'
    print '  Output dir     : %s' % _outdir_display
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
    sf.write('start=%d njobs=%d inseed_base=%d ecms=%s flavor=%d date=%d\n' % (
        opts.start, opts.njobs, opts.inseed, opts.ecms, opts.flavor, DEFAULT_DATE))
    sf.write('failed_loseeds=%s\n' % ','.join([str(ls) for ls, _ in failed]))
    sf.close()
    print '  Summary written: %s' % summary_path
    print '=' * 60

    if failed:
        sys.exit(1)


if __name__ == '__main__':
    main()
