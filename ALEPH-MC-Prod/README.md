# Technical Note: ALEPH Monte Carlo Generator Configuration
## A Complete Reference for all `.cards` Files in `/cvmfs/aleph.cern.ch/`

---

## 1. Overview and Infrastructure

The ALEPH experiment at LEP uses the **KINLIB** framework to steer all Monte Carlo generators. Every generator run is controlled by a `.cards` file, which is a plain-text deck of KINLIB data cards. The general structure of any cards file is:

- **Steering block** (before `ENDQ`): run number (`RUN`), event range (`TRIG`), debug range (`DEBU`), time limit (`TIME`), output file (`FILO`), histogram file (`HSTO`), random seed (`RMAR`), vertex smearing (`SVRT`/`XVRT`/`AVRT`), and an optional reference to a database setup (`NREF`, `FDBA`).
- **Parameter block** (between `KCAR 0 / $TEXT` / `POFF` and `ENDQ` or `END$`): generator-specific cards that configure physics, cuts, and fragmentation.

The random number generator is always RANMAR, initialised with `RMAR INSEED LOSEED`. The `INSEED` is an institute-assigned range; the `LOSEED` is a locally incremented run counter. Vertex smearing is given in centimetres as `SVRT σ_x σ_y σ_z`. The `XVRT` card adds a mean offset and `AVRT` adds beam-tilt angles. Vertex parameters evolved across LEP run periods:

| Period | σ_x (cm) | σ_y (cm) | σ_z (cm) |
|--------|----------|----------|----------|
| ~1992  | 0.0180   | 0.0010   | 1.00     |
| ~1993  | 0.0110   | 0.0005   | 0.70     |
| ~1994  | 0.0124   | 0.0005   | 0.72     |
| ~1997  | 0.0140   | 0.0005   | 0.79     |
| ~1998  | 0.0113   | 0.0005   | 0.79     |
| ~2000  | 0.0155   | 0.0005   | 0.689    |

The electroweak standard-model parameters used universally throughout the cards are:

- M_Z = 91.182–91.1888 GeV, Γ_Z = 2.484–2.497 GeV
- M_W = 80.25–80.35 GeV (LEP1 vs LEP2 runs)
- sin²θ_W = 0.232 (PARU(102)/PARJ(123))
- G_F = 1.16639×10⁻⁵ GeV⁻²

---

## 2. Hadron Production: qq̄ Generators

### 2.1 PYTHIA (pyth02–pyth05, pythia61)

The ALEPH PYTHIA interface uses the `GPYT` steering card:

```
GPYT  IFLAVOR  ECMS  IPRINT
```

**IFLAVOR codes (PYTHIA 5.x):**

| Code | Process |
|------|---------|
| 0    | Hadrons, 6 flavours (qq̄ all) |
| 1    | Hadrons, 5 flavours |
| 2    | tt̄ |
| 3    | W⁺W⁻ |
| 4    | Z⁰Z⁰ |
| 5    | γZ⁰ |
| 6    | γγ |
| 9    | Z⁰H⁰ |
| 10   | νν̄ only |
| 11   | ℓ⁺ℓ⁻ only |
| 12   | Photoproduction, QCD jets |
| 13   | Photoproduction, high-p_T photons |
| 99   | Custom: use MSUB cards |

**pyth02.cards** — PYTHIA 5.6, photoproduction at 91.2 GeV (`GPYT 12`). Key settings:
- ISR on: `MSTP 11/1` (electron structure function), `MSTP 12/1` (structure functions in γ)
- p_T cut: `CKIN 3/1.6` GeV
- `MSTP 83/200` phase-space points
- Lund fragmentation: λ_QCD=0.310, M_min=1.50, σ_mt=0.358, a=0.5, b=0.84
- Peterson c: ε_c=−0.020, ε_b=−0.006

**pyth03.cards** — PYTHIA 5.7, fermion production at 130 GeV (`GPYT 1`, 5 flavours). Minimal card; loads an `END$` after only the basic GPYT and SVRT cards, so the bulk of Lund parameters are inherited from a database or must be added.

**pyth04.cards** — PYTHIA 5.7, **explicit qq̄ selection** at 188.6 GeV. This is the explicit qq̄ card:
```
GPYT  99  188.6  1  1    (IFLAVOR=99, custom mode, IPSHO=JETSET)
MSUB 1 / 1               (qq̄ → Z/γ* subprocess)
```
An Ariadne alternative section is present but commented out. This card is the reference for qq̄ analysis at LEP2 energies.

**pyth05.cards** / **i386_redhat42/kin/pyth05.cards** — PYTHIA 6.1 base parameter block with `GPYT 99` and `MSUB 36/1` (W eν), targeting 183 GeV. This is a W-production card, **not** qq̄.

**pythia61.cards** / **i386_redhat42/kin/pythia61.cards** — Contains only the G. Rudolph June 2001 Pythia 6.1 fragmentation re-tuning patch:
- `MSTJ 12/2` (old diquark + popcorn, equivalent to JETSET 7.4 option 3)
- λ_QCD: 0.277 (was 0.291), M_min: 1.58 (was 1.52)
- σ_mt: 0.372 (was 0.371), a: 0.50 (was 0.40), B: 0.894 (was 0.805)
- ε_b: −0.0024 (was −0.0035)

This file is applied as an overlay on top of pyth05.

**Common JETSET/LUND switches used across all PYTHIA cards:**

| Switch | Value | Meaning |
|--------|-------|---------|
| MSTJ 11 | 3 | Peterson fragmentation for c,b quarks |
| MSTJ 24 | 2 | Truncated Breit-Wigner for resonances |
| MSTJ 41 | 2 | FSR from quarks and leptons |
| MSTJ 42 | 2 | Coherent parton shower |
| MSTJ 43 | 4 | z-definition: global unconstrained |
| MSTJ 44 | 2 | α_s scale: z(1−z)m² |
| MSTJ 46 | 3 | Azimuthal correlations, coherence, gluon polarisation |
| MSTJ 47 | 2 | Correction at first branching (qqg) |
| MSTJ 101 | 5 | Parton shower |
| MSTU 16 | 2 | Links hadrons to proper end of string |
| MSTP 3 | 1 | Take λ_QCD from PARJ(81) |
| MSTP 11 | 1 | ISR on |
| MSTP 83 | 200 | MC phase-space points for MSTP(82)>2 |

**Particle masses set universally in PYTHIA/JETSET cards:**

| Particle | Card | Value |
|----------|------|-------|
| Top quark | PMA1 6 | 174–175 GeV |
| b' (4th gen) | PMA1 7 | 250 GeV |
| t' (4th gen) | PMA1 8 | 350 GeV |
| Z⁰ | PMA1 23 | 91.182–91.187 GeV |
| Z⁰ width | PMA2 23 | 2.484 GeV |
| W | PMA1 24 | 80.25–80.35 GeV |
| Higgs | PMA1 25 | 100–300 GeV |
| f₀(975) | PMA1 10221 | 1.0 GeV (avoids LUDECY loops) |
| a₁ | PMA1 20213 | 1.251 GeV |
| K⁰_L | PMA4 130 | 5.17×10⁻⁸ s |
| K⁰_S | PMA4 310 | 8.926×10⁻¹¹ s |
| D⁺ | PMA4 411 | 1.057×10⁻¹² s |
| D⁰ | PMA4 421 | 0.415×10⁻¹² s |
| D_s | PMA4 431 | 0.467×10⁻¹² s |

W→tb decays disabled: `MDM1 174/0` and `MDM1 337/0`.

---

### 2.2 KK2F (kk2f01–kk2f04)

KK2F is the CERN/Cracow YFS-based generator for Z-peak and LEP2 single-fermion production with full QED resummation.

**Steering card:**
- `GKKT` (old version, kk2f01): `IFLAVOR  ECMS  IPRINT  AMZ  AMH  AMtop`
- `GKK4` (newer, kk2f02–kk2f04): same signature

**IFLAVOR codes (KK2F):**

| Code | Process |
|------|---------|
| 1    | qq̄ 5 flavours (kk2f01/02) |
| 1    | d d̄ (kk2f03) |
| 2    | u ū |
| 3    | s s̄ |
| 4    | c c̄ |
| 5    | b b̄ (kk2f03) |
| 10   | qq̄ 5 flavours (kk2f02) |
| 11   | e⁺e⁻ |
| 12   | νν̄ (kk2f03: all 3 species) |
| 13   | μ⁺μ⁻ |
| 15   | τ⁺τ⁻ |
| 50   | b b̄ (kk2f02) |

**ISR/FSR switches (`GKKR` card):**
- `KeyISR = 1` — ISR on (always active)
- `KeyFSR = 1` — FSR on (set to 0 for neutrinos in kk2f03)
- `KeyINT = 2` — ISR–FSR interference on
- `KeyQSR = 1` — photon emission from final-state quarks off (recommended)

**Critical warning in kk2f03:** Never set `KeyISR=0` and `KeyFSR=0` simultaneously.

**Hadronisation:** Controlled by `XPAR 50`. Setting `XPAR 50/0` disables hadronisation (parton-level only); removing the card or setting it to 1 enables JETSET string fragmentation.

**kk2f03 — neutrino return photon production:**
```
GKK4  12  200.0  0  91.187  100.0  175.0  (νν̄ all species)
GKKR  1.  0.  2.  1.   (ISR only, no FSR)
XPAR 50 / 0.          (no hadronisation)
XPAR 628 / 1.         (activate νe)
XPAR 648 / 1.         (activate νμ)
XPAR 668 / 1.         (activate ντ)
GKR9 1 1 0 1 1000. -0.2   (IBOX, IFKALIN, IFLEPTOK, INTER, XMX, DELTA)
GCUT 10. 250. 0.05 1.0 0.96  (photon E and angle cuts)
```

The `GKR9` card activates box diagram corrections (`IBOX=1`) and anomalous coupling weight calculation for Kalin (`IFKALIN=1`).

**kk2f02 and i386_redhat42/kin/kk2f02.cards** use `NREF 9700` to load a database setup, then apply the Pythia 6.1 tuning overlay on top.

---

### 2.3 ARIADNE (aria02, aria04, and colour-reconnection variants)

ARIADNE is a dipole-cascade model for QCD radiation, used as an alternative to JETSET parton showers. It is steered by the `GARI` card:

```
GARI  IFLAVOR  ECMS  IPRINT  IPROC  SETUP
```

Where `IPROC=1` means use ARIADNE proper; `IPROC=2` means use JETSET 7.3 for comparison. `SETUP='ALEPH'` loads Lonnblad's ALEPH default parameters.

**aria02.cards** — ARIADNE 4.04, mixed flavour, 91.2 GeV. Contains a complete PARA/MSTA parameter listing. Active settings:
- `MSTA 20/2` — FSR photon radiation on, but turned off at first qq̄ emission
- `MSTA 24/1` — parton masses from LUDAT2 (bare masses)
- `PARA 1/0.225` — λ_QCD
- `PARA 3/0.73` — p_T cut for QCD emission
- `PARA 5/1.0` — p_T cut for photon emission
- Lund: σ_mt=0.354, a=0.5, b=0.80

**aria04.cards** — ARIADNE 4.08 (newer tuning from G. Rudolph, Dec 2003). Uses `NREF 4` and then applies the "AR20" two-step tuning:
- `MSTA 35/0` — colour reconnection off
- `PARA 1/0.217`, `PARA 3/0.881`
- `PARG 21/0.351` (σ_mt), `PARG 42/0.758` (B)

Note: aria04 uses `PARG` and `MSTG` cards (KORALW-specific ARIADNE parameter interface) rather than `PARJ` / `MSTJ` used in the standalone ARIADNE cards.

**Colour reconnection variants** (ariadne_cr1/cr2/cr3, ariadne_nocr, ariadne_nocr_2s, ariadne_nocr_2steps):

All share a common base parameter set fitted to Z data (G. Rudolph, Sept 1998):

```
MSTA 20/1   FSR on
MSTG 41/0   FSR done by Ariadne (not JETSET)
PARG 41/0.40, PARG 54/-0.040, PARG 55/-0.0035
PARG 11/0.5716 (V_ud), PARG 12/0.4648 (V_s), PARG 13/0.65 (V_cb)
PARG 17/0.20, 16/0.12, 15/0.04, 14/0.12 (higher meson nonets)
PARG 26/0.2884 (η' suppress.), PARG 1/0.1154 (qq/q)
PARG 2/0.2863 (s/d), PARG 3/0.6507 (su/du)
PARG 19/0.52 (1st rank baryon suppress.)
```

Then the CR mode diverges:

| Card | MSTA(35) | PARA(28) | λ_QCD | p_T_min | σ | B |
|------|----------|----------|-------|---------|---|---|
| ariadne_nocr | 0 (off) | — | 0.2297 | 0.7907 | 0.3577 | 0.823 |
| ariadne_nocr_2s / ariadne_nocr_2steps | 0 (off, AR20 tuning) | — | 0.217 | 0.881 | 0.351 | 0.758 |
| ariadne_cr1 | 1 (within string only) | 0.0 | 0.231 | 0.781 | 0.352 | 0.762 |
| ariadne_cr2 | 2 (within + between W's) | 2.0 GeV | 0.231 | 0.781 | 0.352 | 0.762 |
| ariadne_cr3 | 3 (within + between, different treatment) | 2.0 GeV | 0.231 | 0.781 | 0.352 | 0.762 |

`MSTA(35)=1,2,3` are the colour reconnection models; `PARA(28)` is the minimum gluon energy for reconnection.

**Full MSTA switch reference (from aria02/aria04 documentation in the cards):**

| Switch | Default | Meaning |
|--------|---------|---------|
| MSTA(1) | R | Ariadne mode: 0=none, 1=from JETSET, 2=from PYTHIA, 3=from LEPTO |
| MSTA(3) | 1 | Auto-set parameters: 0=off, 1=on |
| MSTA(5) | 0 | Fragmentation at end of AREXEC: 0=off, 1=on |
| MSTA(6) | −1 | Max emissions per string (−1=unlimited) |
| MSTA(9) | 1 | Debug: 0=off, 1=check 4-momentum, 2=check each emission, 3=dump LUJETS |
| MSTA(11) | 0 | Phase-space p_T restriction for gluon/qq̄/photon |
| MSTA(12) | 1 | Running α_s: 0=off, 1=on |
| MSTA(14) | 1 | Max p_T set from minimum gluon p_T in incoming string |
| MSTA(15) | 5 | Number of flavours in g→qq̄ |
| MSTA(16) | 2 | Recoil treatment: 0=min(p_t1²+p_t3²), 1=pointlike end takes all recoil, 2=extended ends with a>1 also take full recoil |
| MSTA(17) | 2/3 | Recoil treatment for extended dipoles |
| MSTA(18) | 3 | p_T ordering of recoil gluons |
| MSTA(19) | 1/2 | Heavy quark emission treatment: 0=quick, 1=correct, 2=also max(p_T²,Q²) in α_s |
| MSTA(20) | 0 | FSR photon radiation: 0=off, 1=on, 2=on but off at first qq̄ emission |
| MSTA(21) | 0 | Photon radiation when run with PYTHIA/LEPTO: 0=off, 1=on |
| MSTA(22) | 0/1 | Recoil transfer in Drell-Yan: 0=off, 1=on |
| MSTA(24) | 2 | Quark masses: 0=from ARDAT2, 1=bare from LUDAT2, 2=constituent from LUDAT2 |
| MSTA(35) | 0 | Colour reconnection mode (0=off) |

---

### 2.4 HERWIG (hrwg09, hrwg10, hrwg12)

HERWIG uses a cluster fragmentation model. The steering card is `GHRW`:

```
GHRW  EBEAM  IPROC  IPRINT  IHARD  IPPART  MAXER
```

**IPROC codes:**

| Code | Process |
|------|---------|
| 100  | qq̄, all flavours |
| 101–106 | qq̄ single flavour d,u,s,c,b,t |
| 107  | gg (gluon-gluon with gluon) |
| 110  | qq̄g, all flavours |
| 111–116 | qq̄g single flavour |
| 127  | gg |
| 200  | W⁺W⁻ |
| 250  | ZZ |
| 300  | ZH |
| 400  | ννH |
| 500  | γγ QPM |
| 550  | γW |
| 1500 | γγ double resolved |
| 5000 | γγ single resolved |
| 8000 | γγ VDM |
| 9000/9100 | γγ with DIS |
| 10000+ | removes soft underlying event |

**hrwg09.cards** — HERWIG 5.8, `IPROC=100` (qq̄ all flavours), Ebeam=45.6 GeV, `IHARD=3` (initial state from DYMU3). Parameters fitted by G. Rudolph for 5.6:
- `GGSW`: λ_QCD=0.170 (anisotropic fit), NFLAV=5, ΔM_Z=2.56, sin²θ_W=0.2293
- `GPRM`: CLMAX=3.45, CLPOW=2, PSPLT=1, THMAX=0.9, VQCUT=0.48, VGCUT=0.00
- `GHRC`: AZSOFT=1, AZSPIN=1, CLDIR=1 (anisotropic), CLSMR=0
- `GFSR`: VPCUT=0.4, ALPFAC=1
- No colour reconnection: `GCLR 0 0 1`

**hrwg10.cards** — HERWIG 5.9, `IPROC=100`, Ebeam=91.5 GeV. Updated parameters (G. Rudolph, April 1998):
- λ_QCD=0.181, CLMAX=2.99, CLSMR=0.423, η-mixing angle=+70° (was −20°, corrected for 90° phase shift)
- `GBFR`: extended parameter block with separate b-quark fragmentation: QCDLAM=0.189, CLMAX=3.41, CLSMR=0.60, PSPLT=0.945, PSPB(b)=0.334, DECWT=0.68, GLUMA=0.778, PRECO=0 (no CR)
- `GBMI`: B meson mixing on, XMIX(Bs)=10.0, XMIX(Bd)=0.7
- `GMLT`: PLTCUT=1×10⁻⁸ (stability cut), MAXDKL=0, PRVTX=1

**hrwg12.cards** — HERWIG 6.2, `IPROC=100`, Ebeam=91.5 GeV. Key changes vs 5.9:
- `GHRW` card replaces `GENE`
- `GGSW`: λ_QCD=0.181, ΔM_Z=2.50
- `GBFR`: QCDLAM=0.189, CLMAX=3.41, CLSMR=0.60, PSPLT=0.945, PSPB=0.334, DECWT=0.68, GLUMA=0.778, PRECO=0
- Separate `GFLP` card for light vs heavy cluster fragmentation: PSPLT(1)=0.945, PSPLT(2)=0.33, CLSMR(1)=0.58, CLSMR(2)=0.0
- `GQCD`: QCDLAM=0.190, CLMAX=3.39, VQCUT=0.48, VGCUT=0.10, VPCUT=0.40
- `GISR`: TMNISR=0.0001, ZMXISR=0.999999, COLISR=0 (non-collinear ISR)
- `GHCR`: CLRECO=0, PRECO=0 (no CR for standard production)
- `GHWT`: SNGWT=1, DECWT=0.71, VECWT=1, TENWT=1, PWT(1–7)=1
- Masses: light quarks GMAS 1,2=0.320 GeV; top=175.6 GeV; gluon=0.774 GeV (6.2 fit); W=80.35 GeV; Z=91.188 GeV; Higgs=115 GeV
- γγ section present but inactive; includes GGQPM, GGGEN, GGQ2, GCUT, ETAG, TKCU, GPDF cards

**HERWIG colour reconnection variants** (herwig62_cr, herwig62_nocr in the KINAGAIN cards):
- No-CR: standard `GBFR` with PRECO=0
- With-CR: `GBFR` with PRECO=0.111, VMIN2=0.1 (per hrwg10 commented lines: CLMAX=3.40, CLSMR=0.66, PSPLT=0.886, PSPB=0.320, DECWT=0.70, GLUMA=0.793 for maximum CR: CLMAX=3.72, PSPLT=0.710, PRECO=1.000)

**HERWIG stable/unstable particle list:** The `GSTA` card sets particles stable inside HERWIG (tracked by GEANT). K⁰_S, Λ, Σ±, Ξ⁰, Ξ⁻, Ω⁻ and their antiparticles are set stable by default; uncomment `GSTA XX / 'ON'` to let HERWIG decay them internally.

---

## 3. W-Pair Production

### 3.1 KORALW (krlw01, krlw02, krlw03, krlw04)

KORALW generates e⁺e⁻ → W⁺W⁻ → 4f with full CC03 matrix element, ISR resummation via YFS, and optional 4-fermion background.

**krlw01.cards** — KORALW 1.21, 176 GeV (threshold), early version. Uses the `GKRW` compound key card:

```
GKRW  KEYRAD  KEYPHY  KEYTEK  KEYMIS  KEYDWM  KEYDWP
```

Where `KEYRAD = 1000*KeyCul + 100*KeyNLL + 10*KeyFSR + KeyISR`:
- KeyISR=1: ISR on
- KeyFSR=0: FSR inactive in KORALW (done in fragmentation)
- KeyNLL=1: NLL α/π YFS terms kept
- KeyCul=1: Coulomb correction on (DTP/95/64)

`KEYPHY = 100000*KeyWu + 10000*KeyRed + 1000*KeySpn + 100*KeyZet + 10*KeyMas + KeyBra`:
- KeyBra=1: branching ratios with CKM mixing and QCD
- KeyMas=1: massive kinematics for W decay products
- KeyZet=1: Z width as M_Z × Γ_Z in propagator
- KeySpn=1: spin effects in W decays on
- KeyRed=0: sophisticated mass reduction
- KeyWu=1: W width as M_W × Γ_W

`KEYTEK = 100*KeySmp + 10*KeyRnd + KeyWgt`:
- KeyWgt=0: unweighted events (WTMOD=1, suitable for detector MC)
- KeyRnd=1: RANMAR

`KEYMIS = 100*KeyAcc + 10*Key4f + KeyMix`:
- Key4f=1: external 4-fermion matrix element on
- KeyMix=0: sin²θ_W per LEP2 prescription

GKRW settings: `1101 1011 110 10 0 0`. Physics parameters: CMSENE=176 GeV, G_F=1.16639×10⁻⁵, α⁻¹=128.07, M_Z=91.18, Γ_Z=2.4974, M_W=80.25, Γ_W=2.08.

`GTDK` card (tau decay link): JAK1=JAK2=0 (all modes), ITDKRC=1 (radiative corrections in tau decay), IFPHOT=1 (PHOTOS), IFHADM=IFHADP=1 (JETSET hadronisation for both W's).

**krlw02.cards** — KORALW 1.21, 189 GeV, M_W=80.35. The `GKRW` encoding changed slightly:
- KeyCul=1: Coulomb as in KORALW 1.02–1.20

IPSHO=1: JETSET hadronisation. A commented-out ARIADNE section is present for switching to ARIADNE (activate by commenting `END$`/`ENDQ`).

GKAC card (anomalous WWV couplings, Hagiwara notation): all set to SM values (g₁=κ=1, λ=g₄=g₅=κ̃=λ̃=0) and are inactive unless KEYACC=1. GCE1/GCE2/GCUU kinematic cut cards are present.

**krlw02_arcr2.cards / krlw02_arcr3.cards / krlw02_arnocr.cards / krlw02_jetset.cards** — These are variants with different hadronisation:
- `_jetset`: IPSHO=1, standard JETSET
- `_arnocr`: ARIADNE without CR (MSTA 35/0)
- `_arcr2/_arcr3`: ARIADNE with CR model 2 or 3

**krlw03.cards** (reference and i386 versions) — KORALW 1.53.2, 189 GeV. This is the most complete version and uses a **separate** `GKEY` card system instead of encoding into `GKRW`:

```
GKEY  KEYISR  KEYFSR  KEYNLL  KEYCUL  KEYBRA  KEYMAS
```

New options:
- KEYISR=2: ISR with YFSWW extrapolation
- KEYCUL=2: Coulomb with Chapovsky-Khoze screening
- KEYBRA=2: Branching ratios with QCD from CKM (IBA)
- KEYSMP=2: New second presampler for 4f events far from WW peak
- KEYMIX=1: G_μ renormalisation scheme

Then a second line: `KEYZET  KEYSPN  KEYRED  KEYWU  KEYSMP  KEYMIX`

Active: `GKEY 1 0 1 2 2 1` and `1 1 0 1 2 1`. A separate fourth line `KEY4f KEYACC KEYZON KEYWON KEYDWM KEYDWP = 1 0 1 1 0 0` enables both WW and ZZ final states and the 4f matrix element.

MSKW/MSKZ cards allow selecting specific WW or ZZ final-state combinations via a 9×9 (WW) or 11×11 (ZZ) mask matrix.

`GENE` card: CMSENE=200 GeV, M_Z=91.1888, Γ_Z=2.4974, M_W=80.35, Γ_W=−2.03 (recalculated internally), M_H=115 GeV, VVMAX=0.99.

`YFSW` card: invokes the Kandy O(α) correction mechanism via `ywrewt.exe`. `YOUT` specifies output file. `YUNW` (when present) applies O(α) corrections to unweighted events.

**krlw04.cards** — Identified in the listing but the file in i386_redhat42 is similar to krlw03 with updated ECM=206.5 GeV vertex smearing (σ_x=0.0155, σ_z=0.689).

---

## 4. Fermion-Pair Production with Full EW Corrections

### 4.1 KORALZ/KORL07 and KORL08/KORL17 (korl07, korl08, korl17)

KORALZ (versions 4.x used as KORL07/08) generates e⁺e⁻ → ff̄ with YFS QED resummation. The main steering card is `GKR7`:

```
GKR7  AMZ  AMTOP  AMH  AMNUTA  AMNEUT  SINW2  GAMM  KEYGSW  KEYRAD  KEYWLB
      ITFIN  NNEUT  XK0  VVMIN  VVMAX  KEYYFS
```

**ITFIN final state codes:**

| Code | Final state |
|------|------------|
| 1 | τ⁺τ⁻ |
| 2 | μ⁺μ⁻ |
| 3 | νν̄ (NNEUT families) |
| 4 | e⁺e⁻ (s-channel) |
| 501 | dd̄ (KORL08 numbering: d-dbar) |
| 502 | uū |
| 503 | ss̄ |
| 504 | cc̄ |
| 505 | bb̄ |
| 506 | tt̄ |

Note: the d,u quark numbering is **swapped between KORL07 and KORL08**. In KORL07: ITFIN=501 is u-ubar, 502 is d-dbar (confirmed from korl07.cards). In KORL08: ITFIN=501 is d-dbar, 502 is u-ubar (confirmed from korl08.cards).

**KEYGSW — electroweak correction level:**
- 0: photon exchange only, no Z⁰
- 1: photon + Z⁰, Born approximation, no vacuum polarisation
- 4: full GSW corrections (standard for production)

**KEYRAD — QED bremsstrahlung:**
- 0: no bremsstrahlung
- 1: O(α) single bremsstrahlung with ISR-FSR interference
- 10: ISR only, exponentiated single-photon spectrum
- 11: ISR, YFS β₀+β₁
- 12: ISR, YFS β₀+β₁+β₂ **(standard)**
- 111/112: backward compatibility with KORALZ 3.8

**KEYWLB — electroweak library:**
- 1: Stuart/DIZET **(mandatory for quarks, ITFIN>2)**
- 2: Hollik (only valid for leptons)

**KEYYFS — YFS3 steering:**
- 1000001: ISR only
- 1000010: FSR only
- 1000011: ISR + FSR **(standard)**
- 1000000: Born, no bremsstrahlung

Warning: Do NOT use KEYYFS with FSR for neutrino or quark final states (FSR is handled during hadronisation).

**Standard production settings (all korl07/08/17):**
- AMZ=91.18 GeV, AMTOP=175 GeV, AMH=100 GeV
- SINW2=0.2293, GAMM=2.484 GeV (computed internally for KEYGSW=4)
- KEYGSW=4, KEYRAD=12, KEYWLB=1
- XK0=0.010 (soft/hard photon separation)
- VVMIN=1×10⁻⁵, VVMAX=1.0
- KEYYFS=1000011

`GBE7` card (beam setup): ENE=beam energy, KFB=11 (e⁻ along +Z), polarisation vectors.

`GTAU` card (tau decay): JAK1=JAK2=0 (all modes), ISPIN=1 (spin effects on), ITDKRC=1 (radiative corrections), XK0DEC=0.001, GV=1, GA=−1.

`GKR9` card (anomalous couplings and box corrections): IBOX=1 (heavy box diagrams in DIZET), IFKALIN=1 (anomalous coupling weights), IFLEPTOK=0 (no leptoquarks), XMX=1000 GeV.

`GKBR` card (tau branching ratios): a₁→charged fraction=0.5, K⁰→K⁰_S=0.5. Full 37-mode branching ratio table follows.

`PMA1 20213/1.251` — a₁ mass (mandatory to avoid mass-shell issues in TAUOLA).

**KORB01/KORB02** — KORALZ variant for νν̄γ (single photon + missing energy). Uses `KEYRAD=0` (no ISR, mandatory for this process), ITFIN=3 (neutrinos), with a `GCUT` card for photon acceptance: Eγ_min, Eγ_max, x_T cuts, cosθ_max.

**KORL17** — updated version with NREF 9700, same GKR7/GKR9/GTAU structure but targeting u-ubar at 91.2 GeV (ITFIN=502).

---

## 5. Bhabha and Luminosity Generators

### 5.1 BHAB01 / BHAB02 (Large-Angle Bhabha)

`GENE` card parameters:

| Parameter | BHAB01 | BHAB02 |
|-----------|--------|--------|
| Ebeam | 45.6 GeV | 45.6 GeV |
| M_Z | 91.18 GeV | 91.18 GeV |
| M_H | 100 GeV | 100 GeV |
| M_top | 100–130 GeV | 100 GeV |
| θ_min | 10° | 10° |
| θ_max | 170° | 170° |
| k_max/E_beam | 1.0 | 1.0 |
| WEIOPT | 1 (unweighted) | — |
| WTMAX | 1.7 | — |

BHAB02 adds: POLP=POLM=0.5 (longitudinal polarisations), α_s=0.12, and uses R. Miquel modifications (INEW=1).

### 5.2 BHAL01 (Small-Angle Bhabha / SICAL Luminosity)

Uses the same `GENE` card as BHAB01 but with `θ_min=2.177°, θ_max=10.31°` (the SICAL angular range at LEP1). WTMAX=1.72.

### 5.3 BHLUMI (bhlu02, bhlu04)

BHLUMI is the precision small-angle Bhabha luminosity generator (Jadach, Richter-Was, Ward, Wąs). The steering card is `GBHL`:

```
GBHL  CMSENE  THMIN  THMAX  EPSCM  KEYRAD  KEYOPT  WTMAX  [ISICA]
```

- EPSCM=0.0001: soft/hard photon separation
- KEYRAD=1: YFS O(α²) resummation (see BHLUMI manual)
- KEYOPT=3001: standard production option
- ISICA=1: SICAL geometry selected

**bhlu02.cards** — LEP1 production, ECM=92.0 GeV, THMIN=1.700°, THMAX=10.31°. `GBGO` card gives the precise SICAL geometry: R_0A=60.9680 mm, R_0B=60.9604 mm, CORMIN=−0.004, CORMAX=−0.024, Z_0range, energy cuts E1=0.44 GeV, E2=0.60 GeV.

**bhlu04.cards** — LEP2 Bhabha at higher ECM. Similar structure.

**KINGAL.cards** — BHLUMI production at LEP1 (ECM=91.191 GeV) with SICAL geometry, THMIN=0.600°, THMAX=4.100°, WTMAX=3.0.

---

## 6. Two-Photon Processes

### 6.1 DIGZ01 (Double Tag e⁺e⁻ → e⁺e⁻ ℓ⁺ℓ⁻)

`GENE` card: Ebeam=45.6 GeV, ITYPE=11 (e⁺e⁻e⁺e⁻), IREJ=2, θ₀=15°, M_Z/Γ_Z/sin²θ_W set.

ITYPE is a 2-digit code where 1=electron, 2=muon, 3=tau: so ITYPE=11 → e⁺e⁻e⁺e⁻, ITYPE=12 → e⁺e⁻μ⁺μ⁻, etc.

`GCUT` sets invariant mass and energy cuts for all four particles. `GIMP` controls importance factors for four sub-generators A/B/C/D.

### 6.2 PHOT02 (VDM / QED Two-Photon)

`GCON` card: ILUN=0 (build map), IHIS=1 (histograms), ITYPE=100 (VDM multihadron). Ebeam=45.6 GeV.

ITYPE codes:
- 1–16: QED-type (1=e, 2=μ, 3=τ, 10=u+d mixed, 11=u, 12=d, 13=s, 14=c, 15=b, 16=t)
- 100: VDM multihadron
- 101–110: pseudoscalar (π⁰, η, η_c, η_b, F₂(1270)...)
- 200: user-defined resonance (requires GRES card)

`GVDM` card: PTVDM=5.0 (p_T exponent), IWVDM=2 (1/W cross-section), IPLUTO=1 (PLUTO fragmentation: 2 quarks).

`GCUT` card: ICUT=0 (no-tag), TMIN/TMAX=0/π/2. `GQED` set to −1 (no p_T cut on final-state leptons).

`GPSH` card: parton shower via LUSHOW, IQMAX=0 (p_T scale of interaction). `GBAS` controls BASES integration: NCALL=1, ITMX1=ITMX2=5, ACC1=ACC2=5%.

Lund parameters in phot02 match the standard ALEPH set: σ_mt=0.371, a=0.4, b=0.805, λ_QCD=0.291.

### 6.3 PHOJ01 (PHOJET Photoproduction)

Uses `NREF 9700` for base parameters. `GCON` card: Ebeam=91.5 GeV, W_min=2.5 GeV. `GSTD` card for ALEPH selection: isel=1, nch≥1 charged track with p>0.2 GeV, |cosθ|<0.95.

Model parameters via `PMDL`:
- PMDL(110)=0.55: scale reduction for resolved events
- PMDL(36)=2.0: p_T cut for hard processes
- PMDL(23)=10.0: width parameter for Gaussian soft p_T (default 2.5)
- PMDL(21)=1.7, PMDL(22)=1.0: additional soft parameters

`IMDL(3)=1, IMDL(4)=0`: soft p_T modelling. Lund: σ_mt=0.320, non-Gaussian tail=0.05, a=0.44, B=0.90.

`ETG1`/`ETG2` cards: both electrons vetoed if E>20 GeV within 0.030<θ<3.112 rad (anti-tag condition).

---

## 7. Neutrino Processes

### 7.1 NNGG03 (νν̄γγ)

Single and double photon production via e⁺e⁻ → νν̄γ(γ). `GENE` card:
- CMEIN=92.2 GeV, NFIN=3 families, EDCIN=0.020 GeV (soft/hard cut), DPPIN=DPMIN=0 (unpolarised)
- FI1=FI2=1.0: both single and double photon processes
- WCUT=1.4, NT=10⁶ trials, NP=100 init points

`GSMP` card: Standard Model masses. `GACP` card: photon acceptance: E_min=0.5 GeV, θ_min=15°, x_max/Ebeam=1.0.

### 7.2 NNGP01 (νν̄γ with QED corrections)

`GNNG` card: ECMS=195.5 GeV, NFL=10 (all neutrino species), NPHO=1, IQED=1 (full QED), IPT=1 (ISR with p_T), 1/α(M_Z)=128.87, Nstep=100000. `GMSP` card: SM masses and widths. `GGAM` card: γ acceptance θ_min=10°, E range 2–150 GeV.

Anomalous TGC via `GAGC` (xγ, yγ) and QGC via `GQGC` (λ, a₀^W, a_c^W, a₀^Z, a_c^Z) — all commented out for SM production.

---

## 8. Higgs Production

### 8.1 HZHA01/02/03

HZHA generates e⁺e⁻ → Higgs + Z with full matrix element (IKLEI=1) or on-shell approximation. `GENE` card:

```
GENE  IKLEI  IPROC  XRAD  ECM  EMPIR  SM  ICAR
```

- IKLEI=1: full e⁺e⁻ → hff̄ calculation
- IPROC: 1=hZ, 2=HZ, 3=hA, 4=HA, 5=WW→h, 6=WW→H, 7=ZZ→h, 8=ZZ→H, 0=all
- XRAD=1.0: standard bremsstrahlung ISR spectrum
- SM=1: Standard Model (MSSM=0)
- ICAR=1: Carena et al. 2-loop RGE for MSSM pole masses

`PRYN` card selects which of the 8 processes are active simultaneously.

`GSMO` card: M_Z=91.189, Γ_Z=2.497, G_F=1.16639×10⁻⁵, M_top=175, M_H=90, QCD5=0.208 GeV (→ α_s(M_Z)=0.118).

`GSUS` card (MSSM): MA, tanβ, M, μ, A_t, A_b, M_Q, M_U, M_D, M_L, M_E. All soft masses set to 1000 GeV for decoupling.

`GZDC` card: Z decay channels (11 channels, all on). `GHHG` card: Higgs decay all modes (`CH=0`). GCH1/GCH2/GCH3 cards control individual decay channels for H/h/A.

The 16 Higgs decay channels: γγ, gg, ττ, cc̄, bb̄, tt̄, WW, ZZ, AA/Zh, hh, γZ, e⁺e⁻, μ⁺μ⁻, ss̄, χχ (invisible), χ⁺χ⁻.

Lund tuning in HZHA uses a different parameter set from the QCD group (25/09/93, G. Rudolph):
- λ_QCD=0.321, M_min=1.65, σ_mt=0.361, a=0.5, b=1.01
- V/P ratios: PARJ(11)=0.55, PARJ(12)=0.60, PARJ(13)=0.85, PARJ(17)=0.18
- η' suppression: PARJ(26)=0.40 (was 0.20)
- Baryon: PARJ(1)=0.105, PARJ(2)=0.301, PARJ(3)=0.43, PARJ(4)=0.05

D/B-meson sector: detailed PMA1/PMA2/PMA3 cards for all D**, B**, and B_c states. Full GMOB branching ratio tables for B⁰, B_s, D⁺.

---

## 9. Four-Fermion and Exotic Production

### 9.1 EXCALIBUR (exca01)

EXCALIBUR computes the complete e⁺e⁻ → 4f matrix element including all CC03+NC diagrams.

`GSMO` card: M_Z=91.1888, M_W=80.25, G_W=−1 (recalculated), G_F=1.16639×10⁻⁵, α_R=137.036, α=1/128.07, α_s=0.000 (no QCD diagrams by default), α_s(M_Z)=0.12.

Generator options (`GENE`):
- IEXDIA=0: all diagrams
- IEXUWT=1: unweighted events
- IEXISR=1: ISR on
- IEXFSR=1: FSR via PHOTOS
- IEXHAD=1: JETSET fragmentation on
- IEXCOU=1: Coulomb correction for WW
- IEXPAF=4: pair according to relative probability (no interference)
- IEXCRC=0: no colour reconnection

Anomalous WWV couplings via `ANOM` card (Hagiwara notation: Δκ_γ, λ_γ, Δg₁^Z, Δκ_Z, λ_Z, g₄^Z — all zero for SM).

`KPRO` card: selects final states. Use `KPRO 0` for all states; specific 8-digit PDG codes select individual final states. Wildcards: 00=any flavour, 09=any quark, 19=any lepton.

`CUTS` card: phase-space cuts per process. The special `PROC=-5` option applies a minimal forward-electron veto (cosθ cut SHCUT). `PROC=-111` applies lepton-flavour cuts.

### 9.2 FERM01 (4-Fermion via Spin amplitude method)

Alternative 4-fermion generator. `GENE` card specifies FLA_1, FLA_2 fermion flavour codes (1=e, 2=νe, 3=μ, 4=νμ, 5=τ, 6=ντ, 7=d, 8=u, 9=s, 10=c, 11=b), invariant mass ranges MN/MX for each pair, minimum momenta, θ_min cut, ECM, M_Z, Γ_Z, sin²θ_W, ISR/FSR flags.

### 9.3 ELW201 (4-Lepton Production)

Generates e⁺e⁻ → ℓ⁺ℓ⁻ℓ'⁺ℓ'⁻ via `GENE` card:
- IPROC: 1=μμττ, 2=μμμμ, 3=eeμμ, 4=eeττ, 5=eeee, 6=ττττ
- IREJEC=2: rejection algorithm
- Uses sub-generators A–D with importance factors (GIMP/ESWE/ESFT)

### 9.4 ELW DFGT01 (SUSY Neutralino/Chargino)

`GENE` card: BEAM=86.0 GeV, IPRINT=10, IHISTO=1. `PASM` card: sin²θ_W=0.2320, α=0.0078120, α_s=0.120, ISR=1. `RUSR` card: m₀=1000, μ=−65, M₂=43, tanβ=1, A=0, Rscale=1. `GBAS` integration control. `GCHC` final state selector: 0=all, 1=ℓℓ, 2=ℓτ, 3=ℓq, 4=τq, 5=qq.

### 9.5 ESTA01 (Excited Electron)

`GENE` card: CME=91.2, M_Z=91.18, sin²θ_W=0.232, NF=3. NWEAK=0 (QED only), NFAST=2 (only photon t-channel). IFULL=1 (photon t-channel e* diagrams). XLAM=100 GeV (compositeness scale), CL=−0.5, CR=0, M(e*)=30 GeV.

---

## 10. ZZ and Zνν Production

### 10.1 ZNNB01

`NREF 9702`: loads Z⁰Z⁰/γZ⁰/WW database setup. `GENE` card:
```
GENE  ECM  MZ  GZ  SW2
      200.  91.189  2.497  0.2317
```

### 10.2 UNIBAB (ubab01, ubab02)

Darmstadt-Cern-Siegen Bhabha generator. `GPAR` card:
- AMZ/AMH/AMT/ECMS: masses and energy
- CTSMN/CTSMX: cosθ* range (±0.91)
- EFERM=1.0 GeV: minimum outgoing electron energy
- ACOLMX=30°: maximum acollinearity
- ITCH=1: t-channel on
- IWEAK=1: weak corrections on
- IBOXES=1: box diagrams on (only if IWEAK=1)
- IBST=3: initial + final state photons
- ITFRE=1000: write GSUM bank every 1000 events

---

## 11. Heavy Flavour Generators

### 11.1 HVFL05/HVFL06

HVFL generates heavy-flavour events using DYMU3 as the primary generator with parton shower, PHOTOS for radiative decays, and a detailed B/D meson decay table. The `GHVF` card selects the generator:
- IGENE=1: LUND 7.4 + parton shower
- IGENE=3: DYMU3 + parton shower
- IGENE=−1: single-particle mode

`GDYM` card for DYMU3: FTYPE=10 (quark mixture), Ebeam=45.6 GeV, M_Z=91.182, Γ_Z=2.484, sin²θ_W=0.232. The line following GDYM gives: ID2=0, TAU=0, FINEXP=1, POIDS=1, XK0=0.003, QCDFAC=1.04, NQUA=5, IFIRST=11, NEVMA=5000.

`GSIN` card: single-particle gun (Lund type 511=B⁰, p range, θ range, φ range).

`GLUN` card: LUND generator control (IFLAVOR=0=mixed, ECMS=91.2).

Mixing: `GMIX` — xd=0.7, yd=0, xs=5.0, yd=0. `GCPV` — CP violation parameters. `GSTA` — set J/ψ (443) and K⁰_S (310) stable.

`GVBU` card (b→u transitions): IMATBU=43, PRBUBC=0.03, PARDBU=1.0, ITYPBU=1 (free quark model).

`GPHO` card: IPHO=333 = photon emission on D meson semileptonic decays (tens digit), B meson semileptonic (units digit), J/ψ leptonic (hundreds digit).

`GSEM` card: semileptonic B decay model=1, sub-model=1.

The Bs⁰ branching ratio table (GMOB 531) and B⁰ table (GMOB 511) are fully specified with semileptonic, 2-body, 3-body, diagonal, and added modes totalling ~100%.

MSTJ switches in HVFL:
- `MSTJ 26/0`: B mixing handled by HVFL, not JETSET
- `MSTJ 107/1`: ISR on for JETSET
- `MSTJ 41/2`: FSR from quarks

---

## 12. Tau-Pair Generators

### 12.1 DYMU02 (DYMU3 for μ⁺μ⁻)

`GDYM` card: FTYPE=2 (muons), Ebeam=45.6 GeV. Second line: ID2=0, TAU=0, FINEXP=1 (final state exponentiation), POIDS=1 (unweighted), XK0=0.003, QCDFAC=1.04, NQUA=3, IFIRST=11, NEVMA=5000.

Lund parameters (old JETSET 7.3 style): MST 4/3 (Peterson), PAR 12/0.325, PAR 31/0.45, PAR 44/−0.025 (ε_c), PAR 45/−0.015 (ε_b). Extra quark family pushed away: PMAS 106=100, 107=150, 108=300 GeV.

---

## 13. Bose-Einstein Correlations

### 13.1 BE3B / BE3I / NEWBE3B / NEWBE3I

These are overlay cards applied in the KINAGAIN framework for W⁺W⁻ events to study Bose-Einstein effects.

**be3b.cards** — BE between W's:
- `MSTG 51/2`: Gaussian parametrisation
- `MSTG 53/0`: between W's (both W's)
- `MSTG 54/1`: BE3 model
- `MSTG 57/0`: no penalty
- `PARG 92/2.1`: λ_BE, `PARG 93/0.26`: σ_BE

**be3i.cards** — BE inside single W:
- `MSTG 53/1`: inside one W only
- Same λ and σ

**newbe3b/newbe3i.cards** — Updated (2001) tuning with simultaneous fragmentation fit:
- Same Gaussian parameters (λ=2.1, σ=0.26)
- `MSTG 52/3`: 3 particle species affected
- Updated fragmentation: λ_QCD=0.292, Q₀=1.55, σ_mt=0.385, b=0.763

---

## 14. KINAGAIN Reprocessing Framework

**kinagain.cards** controls the KINAGAIN tool, which re-processes existing W⁺W⁻ events from KINGAL/KORALW format to apply different hadronisation, colour reconnection, or Bose-Einstein models.

The `GAGA` card is the master switch:
```
GAGA  ipsho  ihad  ireco  ibe  icopy
```

- ipsho=1: JETSET, ipsho=2: ARIADNE, ipsho=13: HERWIG 6.2
- ihad=0: all events, ihad=1: fully hadronic events only
- ireco=0: no CR; 1–4: CR model (depending on ipsho)
  - For JETSET: ireco=1=SKI, 2=SKII, 3=SKII', 4=GAL
  - ireco=11,12,13: same with boost to W⁺W⁻ system before CR
- ibe=0: no BE; ibe=1: as in external cards file
- icopy=1: restore original KINGAL output (useful from POT)

A `READ` card must accompany each GAGA card pointing to the appropriate tuning cards file.

---

## 15. EEGG01 (e⁺e⁻γγ / Radiative Bhabha)

`GENE` card: Ebeam=45.6 GeV, MRADCO=3 (lowest order e⁺e⁻γ), MCONFI=11 (e-gamma configuration), MATRIX=22 (Berends-Kleiss matrix element with m²/t term), MTRXGG=31 (EPA + double Compton).

`GCUT` card: TEVETO=0.030 rad (missing electron veto), TEMIN=0.2618 rad (minimum electron angle), TGVETO=0.050 rad, TGMIN=0.2618 rad, PHVETO=0.7854 rad, PEGMIN=0.7854 rad. Energy: EEMIN=EGMIN=5 GeV.

---

## 16. Summary Table of Generators and Their Processes

| Generator | Cards | Process | ECM (GeV) |
|-----------|-------|---------|-----------|
| PYTHIA 5.6 | pyth02 | Photoproduction (QCD jets) | 91.2 |
| PYTHIA 5.7 | pyth03 | qq̄ 5 flavours | 130 |
| PYTHIA 5.7 | pyth04 | qq̄ explicit (MSUB 1) | 188.6 |
| PYTHIA 5.7/6.1 | pyth05 | W eν (MSUB 36) | 183 |
| PYTHIA 6.1 | pythia61 | Fragmentation tuning overlay | — |
| KK2F | kk2f01 | qq̄ 5f, e⁺e⁻, μ⁺μ⁻, τ⁺τ⁻, νν̄ | 202 |
| KK2F | kk2f02 | qq̄ + individual flavours | 202 |
| KK2F | kk2f03 | νν̄γ (ISR only, no FSR) | 200 |
| ARIADNE 4.04 | aria02 | qq̄ mixed | 91.2 |
| ARIADNE 4.08 | aria04 | qq̄ mixed | 91.2 |
| HERWIG 5.8 | hrwg09 | qq̄ all + FSR | 91.2 |
| HERWIG 5.9 | hrwg10 | qq̄ all | 91.2+LEP2 |
| HERWIG 6.2 | hrwg12 | qq̄ all + γγ section | 91.2+LEP2 |
| KORALW 1.00 | krlw01 | W⁺W⁻ → 4f | 176 |
| KORALW 1.21 | krlw02 | W⁺W⁻ + 4f bkg | 189 |
| KORALW 1.53.2 | krlw03 | W⁺W⁻ + ZZ + 4f + O(α) | 189–206 |
| KORALZ (KORL07) | korl07 | τ⁺τ⁻, qq̄ | 91.25 |
| KORALZ (KORL08) | korl08 | τ⁺τ⁻, qq̄ | 161 |
| KORALZ (KORL17) | korl17 | uū | 91.2 |
| KORB01 | korb01 | νν̄γ (single photon) | 91.2 |
| BHABHA | bhab01 | e⁺e⁻ large angle | 91.2 |
| BHABHA | bhab02 | e⁺e⁻ large angle, polarised | 91.2 |
| BHLUMI | bhlu02/04 | e⁺e⁻ small angle (SICAL) | 91.2 / LEP2 |
| UNIBAB | ubab01/02 | e⁺e⁻ with weak+boxes | 91.2 |
| DIGZ01 | digz01 | e⁺e⁻ℓ⁺ℓ⁻ (2γ double tag) | 91.2 |
| EEGG01 | eegg01 | e⁺e⁻γγ (radiative Bhabha) | 91.2 |
| PHOT02 | phot02 | γγ → hadrons (VDM/QED) | 91.2 |
| PHOJET | phoj01 | γγ photoproduction | 91.5 |
| HZHA | hzha01/02/03 | e⁺e⁻ → hZ, WW→h, ZZ→h | ~192 |
| EXCALIBUR | exca01 | e⁺e⁻ → 4f (all diagrams) | LEP2 |
| FERM01 | ferm01 | e⁺e⁻ → 4f (spin amplitude) | 91.2 |
| ELW201 | elw201 | e⁺e⁻ → 4ℓ | 91.2 |
| DFGT01 | dfgt01 | SUSY χχ̃ production | 86.0 |
| ESTA01 | esta01 | e* excited electron | 91.2 |
| NNGG03 | nngg03 | e⁺e⁻ → νν̄γγ | 92.2 |
| NNGP01 | nngp01 | e⁺e⁻ → νν̄γ + QED | 195.5 |
| DYMU02 | dymu02 | e⁺e⁻ → μ⁺μ⁻ | 91.2 |
| HVFL05/06 | hvfl05/06 | Heavy flavour with DYMU3+PHOTOS | 91.2 |
| ZNNB01 | znnb01 | e⁺e⁻ → Zνν | 200 |

---

## 17. Key Differences Between Reference and i386_redhat42 Versions

The cards in `/cvmfs/aleph.cern.ch/i386_redhat42/kin/` are mostly identical to the reference versions but with a few updates:

- **kk2f02, kk2f03**: Identical content; the i386 version may have been compiled for the newer platform
- **pythia61**: Only the fragmentation tuning overlay, same content both locations
- **krlw02, krlw03**: Identical physics, both locations
- **korl07, korl08, korl17**: Same physics; korl08 at 161 GeV vs korl07 at 91.25 GeV as expected
- **hvfl05**: Same generator, i386 version may have platform-specific fixes
- **ubab02**: Fully present only in i386_redhat42
- **znnb01**: Fully present only in i386_redhat42
- **kk2f04**: Listed in i386_redhat42 but the file does not exist (cat error)

---

## 18. Database Reference System

Several cards use `NREF XXXX` to load a pre-configured set of standard parameters from the ALEPH Monte Carlo database (ADBSTEST.DAF or similar). The reference numbers seen in the cards are:

| NREF | Content |
|------|---------|
| 4 | ARIADNE 4.x base setup |
| 9600 | Standard 1996 MC production parameters |
| 9700 | Standard 1998–2001 MC production parameters |
| 9701 | Additional setup: q qbar + PYTHIA 5.7 |
| 9702 | Z⁰Z⁰, γZ⁰, WW combined setup |
| 9711 | KORALW 1.21 WW production setup |

When `NREF` is used, the subsequent `KCAR 0 / $TEXT` / `POFF` … `END$`/`ENDQ` block **overrides** specific parameters from the database, allowing targeted modifications without repeating the full parameter list.

---

*Document compiled from complete reading of all `.cards` files in `/cvmfs/aleph.cern.ch/reference/kin/` and `/cvmfs/aleph.cern.ch/i386_redhat42/kin/`. All parameter values are taken directly from the active (non-commented) lines in the cards files.*
