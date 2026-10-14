# Real-time physical model of the Rhodes Electric Piano (Sønderbo, AAU MSc thesis, 2024)

## Source

| Field | Value |
|---|---|
| Title | *Real-time physical model of the Rhodes Electric Piano* |
| Author | Tobias Sønderbo (supervisor: Stefania Serafin) |
| Year / date | Completed 23 May 2024 (title page; the "Project period" field says "Fall Semester 2024") |
| Venue | Master's thesis, Architecture, Design and Media Technology, Aalborg University. Theme: "Physical Models for Sound Synthesis". 32 numbered pages plus appendices A to C (45 PDF pages) |
| URL | https://projekter.aau.dk/projekter/files/719175589/Master_Thesis_Real_time_physical_model_of_the_Rhodes_Electric_Piano_Tobias_Sonderbo.pdf (fetched OK, 805,721 bytes) |
| Licence | Title page: "The content of this report is freely available, but publication (with reference) may only be pursued due to agreement with the author." |
| Code repo | https://github.com/TSonderbo/EPiano (thesis ref. [26]). Cloned at HEAD `03fa04463ab1cf493f53ae7413d101a8ec5bc101` (4 Jun 2024). It contains a JUCE C++ VST/MPE plugin, Python/Jupyter derivations and prototypes, and a Matlab prototype. **The repo has no LICENSE file.** |
| Local copies | `docs/model/research/sources/02-sonderbo-thesis/thesis.pdf`, `thesis.txt` (pdftotext -layout), `repo/EPiano/` |

Provenance notation used below:
- "§x.y", "Eq. (n)" and "Tab. n" refer to the thesis.
- "p. N" is the printed page number.
- `code:File.cpp` refers to the repo.

**The code and the thesis disagree on several numbers.** Both values are given wherever they differ.

## Summary

- **Tine:** a single uniform Euler–Bernoulli cantilever (clamped/free), simulated with an explicit FDTD scheme (Bilbao-style). Losses come from σ0 (frequency-independent) and σ1 (frequency-dependent).
- **Tone bar and tuning spring:** not modeled. The tone bar's effect is folded into σ0/σ1. The tuning-spring mass is replaced by lengthening the tine, with length from the analytic cantilever formula (Eq. 3.8).
- **Pitch bend:** done with Willemsen's "dynamic grid" (the grid is split in two halves with a fractional inner boundary, and points are added or removed by cubic Lagrange interpolation). This is the vehicle for MPE per-note pitch bend of ±1 semitone.
- **Hammer:** a Hunt–Crossley nonlinear contact (penalty method, F = k_h x^α (1 + μ_h ẋ)) acting at a single grid point.
- **Damper:** a nonlinear damped spring that ties one tine grid point to equilibrium (implicit in only one scalar, so solved explicitly).
- **Pickup:** *not* physical. It is a copy of the Mike Moreno "EP-MK1" chain: resonant SVF low-pass → gain → tanh → exponential "symmetry" shaper → cubic "buzz" → resonant SVF high-pass at f0.
- **Implementation:** a JUCE MPE plugin with 5 voices by default (code: 1). It needs heavy temporal oversampling (4x to 32x, per note) to get ≥8 to 10 grid points per tine.
- **Results:** poor. Pitch is wrong (flat on all notes), overtone ratios differ from measurements (6.37/35.27 vs Rhodes 7.11/20.25), sustain is too long, and the pickup produces strong inharmonic content.
- **Evaluation:** no CPU figures are reported. The only "listening" evaluation is 2 informal user interviews about MPE pitch bend.

## Model architecture

| Block | Modeled? | How (provenance) |
|---|---|---|
| Hammer / excitation | Yes | A lumped mass with initial velocity and Hunt–Crossley contact force (Eqs. 3.19–3.21, Tab. 3.2). Contact is spread over **one** grid point. Velocity is mapped to initial hammer velocity (`code:Tine.cpp noteStarted`: v = MIDI_vel_norm × 6 m/s). |
| Tine | Yes, by FD | Euler–Bernoulli stiff bar, explicit FDTD with σ0/σ1 losses, clamped at the base and free at the tip (Eqs. 3.1–3.10). Assumed to be a uniform round rod. |
| Tuning spring | Indirectly | Not simulated. The tine is lengthened instead (§3.2.1). Varying cross-section (Pfeifle) was discussed and rejected. |
| Tone bar / coupled resonator | No | "simplified by using [σ0, σ1] to model the influence of the tone bar" (§3.2, p. 9). No beating, no energy exchange, no tone-bar partials. |
| Damper / release | Yes | A damped nonlinear spring (K1, K3, R) connecting one tine point to 0 while the key is released (Eqs. 3.22–3.23, Tab. 3.3). Collision models were rejected: mass-spring collision needs a matrix inversion, and rigid-barrier collision produces artifacts (Fig. 3.4). |
| Pickup (electromagnetic) | Non-physical | Filter + waveshaper chain after [23] Mike Moreno EP-MK1 (§3.5; `code:MagneticPickup.cpp`). Input is tip displacement × "tine gain" (default 10000). Physical alternatives are discussed but not implemented: Pfeifle FEM/integral model, Falaize–Hélie port-Hamiltonian (§3.5.1). |
| Preamp / amp | No | Only a gain and a hard limit to ±1 (`code:Tine.cpp limit`). |
| Tremolo | No | — |
| Speaker / cabinet | No | — |
| Mechanical noises | No | No key or damper thump. The damper only adds a force; it has no noise model. |
| MPE | Yes | Pitch bend maps to tine length via the dynamic grid (§4.1). Aftertouch → LP cutoff is proposed, not implemented (§6.3). |

Signal flow:

```
note-on(vel) -> hammer mass (Hunt-Crossley, 1 pt) -> EB-tine FDTD [dynamic grid, os x4..x32] -> tip displacement u_tip
  -> x tine_gain -> SVF LP(fc~1 kHz) -> gain(15 dB) -> tanh -> 2^(g*x)-1 asym shaper -> y - y^3/3 -> SVF HP(fc=f0) -> clip(+-1) -> out
note-off -> damper spring (K1,K3,R) attached to tine point while released
```

## Equations

The notation follows the thesis.
- u_l^n: transverse tine displacement (m) at grid index l and time step n.
- k = 1/(fs·j): time step (s), where j is the oversampling factor.
- h: grid spacing (m).
- N: number of grid intervals.

**Bar geometry (§3.2, p. 8)**

    A = π r²   [m²]    I = π r⁴ / 4   [m⁴]    κ = sqrt(E I / (ρ A))   [m²/s]  (Eq. 3.4)

**FD operators (§2.2, Eqs. 2.1–2.6)**

    δ_tt u = (u^{n+1} − 2u^n + u^{n−1})/k²
    δ_t· u = (u^{n+1} − u^{n−1})/(2k)
    δ_xx u = (u_{l+1} − 2u_l + u_{l−1})/h²
    δ_xxxx u = (u_{l+2} − 4u_{l+1} + 6u_l − 4u_{l−1} + u_{l−2})/h⁴
    δ_t− δ_xx u = [ (u_{l+1}−2u_l+u_{l−1})^n − (u_{l+1}−2u_l+u_{l−1})^{n−1} ]/(k h²)

**Lossy Euler–Bernoulli scheme (Eq. 3.2)**

    ρA δ_tt u = −EI δ_xxxx u − 2σ0 ρA δ_t· u + 2σ1 ρA δ_t− δ_xx u

- σ0 [s⁻¹]: frequency-independent loss.
- σ1 [m²/s]: frequency-dependent loss.

**Stability (Eq. 3.3, proof in App. A, von Neumann).** The printed formula has lost its operators. The form below is the corrected one, consistent with App. A's last lines and with `code:Tine.cpp calculateGridSpacing`:

    h ≥ sqrt( ( 4σ1 k + sqrt( (4σ1 k)² + 16 κ² k² ) ) / 2 )

The thesis sets h equal to this bound. N = floor(L/h) (Eq. 3.6), and the thesis then sets h = L/N (Eq. 3.7). **The code instead keeps h and uses the fractional remainder α as the dynamic-grid offset (Eq. 3.13).**

**Interior update (Eq. 3.5 / Eq. 4.1).** μ = κk/h² is a dimensionless Courant-like number; μ² ≤ 1/4 at the lossless limit.

    u_l^{n+1} = D·[ C0 u_l^n + C1 (u_{l+1}^n + u_{l−1}^n) − M0 (u_{l+2}^n + u_{l−2}^n)
                    + B0 u_l^{n−1} − S (u_{l+1}^{n−1} + u_{l−1}^{n−1}) ]
    C0 = 2 − 6μ² − 4σ1k/h²      C1 = 4μ² + 2σ1k/h²      M0 = μ²
    B0 = −1 + σ0k + 4σ1k/h²     S  = 2σ1k/h²            D  = 1/(1+σ0k)

**Boundaries**
- **Clamped (Eq. 2.7):** u_0 = u_1 = 0.
- **Free, virtual-point form (Eqs. 2.9, 2.10):** u_{N+1} = 2u_N − u_{N−1}, u_{N+2} = u_{N−2} − 2u_{N−1} + 2u_{N+1}. This form was found **unstable** together with the σ1 mixed term (§3.2.2).
- **Free, matrix-row form (Eqs. 3.9, 3.10; App. B, B.2 and B.4):**

      u_{N−1}^{n+1} = D·[ (2−5μ²−4σ1k/h²) u_{N−1} + (2σ1k/h² + 2μ²) u_N + (4μ²+2σ1k/h²) u_{N−2} − μ² u_{N−3}
                         + (−1+σ0k+4σ1k/h²) u_{N−1}^{n−1} − (2σ1k/h²)(u_{N−2}^{n−1}+u_N^{n−1}) ]
      u_N^{n+1}     = D·[ (2−2μ²−4σ1k/h²) u_N + (4μ²+4σ1k/h²) u_{N−1} − 2μ² u_{N−2}
                         + (−1+σ0k+4σ1k/h²) u_N^{n−1} − (4σ1k/h²) u_{N−1}^{n−1} ]

  The thesis' Eq. 3.9 prints the coefficient of u_N as "(2σ1k/h²)2μ²". App. B.2 and the code (`F_1 = S + 2μ²`) show it is a sum. In the code, the u_N^{n−1} term of Eq. B.4 uses B0.

**Dynamic grid (§3.2.3, Eqs. 3.11–3.18; App. C)**
- The grid is split into u (base half, M_u = ceil(N/2)) and w (tip half, M_w = floor(N/2)).
- The halves meet at inner boundaries u_{M_u} and w_0, separated by the fraction α = L/h − N (Eq. 3.13).
- **Adding a point** uses cubic Lagrange interpolation over [u_{M_u−1}, u_{M_u}, w_0, w_1] (Eq. 3.14):

      I = [ −α(α+1)/((α+2)(α+3)),  2α/(α+2),  2/(α+2),  −2α/((α+3)(α+2)) ]

- **Inner-boundary stencils (App. C)** use Iterm = (α−1)/(α+1) and J0 = I²−4I+6, J1 = I−4, J2 = −I²+4I+1, J3 = −I. These give coefficients A0..A5 and E1 (`code:Tine.cpp calculateInterpolation`).
- The w vector is index-flipped so both halves behave as stacks (Eqs. 4.2–4.4).

**Hammer: Hunt–Crossley (Eqs. 3.19–3.21, §3.3)**

    δ_tt u_h = −F                                           (3.19, as printed; no 1/M_h)
    F = k_h x^{α_h} (1 + μ_h δ_t− x)  for x > 0, else 0     (3.20)
    x = u_h − Σ_l ε_h,l u_l          (penetration: hammer minus tine at contact; code:Hammer.cpp)
    μ_h = λ / k_h  [s/m]  →  9e10 / 1.5e11 = 0.6 s/m  (code uses mu = 0.6)
    δ_tt u_l = −κ² δ_xxxx u − 2σ0 δ_t· u + 2σ1 δ_t− δ_xx u + ε_h M F,   M = M_h/(ρAL)   (3.21)

- ε_h is a one-point contact distribution.
- **Units are inconsistent here.** Eq. 3.19 has no 1/M_h, and "ε_h M F" is not an acceleration (a consistent form would be ε_h F/(ρA h) for the tine and −F/M_h for the hammer). The code does exactly what the thesis prints: `uNext = 2u − uPrev − F k²`, and the tine source term is `k²·(M_h/(ρAL))·F` at one point. Treat the hammer parameters as **tuned, not physical**.
- In code, the hammer starts at u_in = −1e−4 m with u^1 = u_in + k·v. It deactivates when u_h ≤ u_in, i.e. after it rebounds.
- In code, x is computed by a dot product over all M_u+1 points of the u-grid, every sub-step.

**Damper: damped nonlinear spring to equilibrium (Eqs. 3.22, 3.23)**

    δ_tt u_l = (scheme) − f^n/(h ρ A)  at the damper point
    r+ = K1/4 + K3 η²/2 + R/(2k),  r− = K1/4 + K3 η²/2 − R/(2k)
    f^n = ½ · ( u* + (K1/(2 r+)) η^n + (r−/r+) η^{n−1} ) / ( 1/r+ + k²/(hρA(1+σ0k)) )

- η is the tine displacement at the damper point.
- u* is the next-step value computed without the connection force.
- The code applies `w[d_loc] = u* − (1/h)·k² f/(ρA(1+σ0k))`, which is consistent with the formula above.

**Analytic tuning (Eq. 3.8)**

    f1 = 1.426 · π (r/2) / (8 L²) · sqrt(E/ρ)      →   L = sqrt( 1.426 π (r/2) sqrt(E/ρ) / (8 f1) )

1.426π/8 ≈ 0.560, which matches the standard cantilever value (1.875²/2π)·(r/2)·c. **Note that N = L/h is independent of r**, because both L and h scale as sqrt(r).

**Proposed, not implemented (Eq. 6.1).** An extra high-frequency loss term: −2σ2 ρA δ_t− δ_xxxx u.

**Pickup chain (code:MagneticPickup.cpp, after [23])**

    s = u_tip · G_tine                    (G_tine default 10000, range 1..20000)
    s = SVF_LP(s; fc=1000 Hz (200..2000), res=0.404061)
    s = tanh( s · 10^(15/20) )            (gain 15 dB, range 0.1..30 dB; JUCE fast tanh approx)
    g = 10^(sym_dB/20)  (sym default 15 dB → g ≈ 5.62)
    s = (2^(g·s) − 1) / 2^g               (asymmetric exponential shaper)
    s = s − s³/3                          ("buzz")
    s = SVF_HP(s; fc = f0 of note, res=0.404061)
    out = clamp(s, −1, 1)

"res" is the JUCE StateVariableTPTFilter resonance parameter (Q-like). With g = 5.62, the shaper maps s ∈ [−1, 1] to ≈ [−0.020, +0.98] (my calculation). This is **strongly asymmetric**: it rectifies the signal and generates even harmonics.

## Parameters

### Tine material (Tab. 3.1, p. 9, vs `code:Tine.h`)

| Name | Symbol (unit) | Thesis Tab. 3.1 | Code (`Tine.h`) | Notes |
|---|---|---|---|---|
| Radius | r (m) | 0.0005 | 1.524e-3 | Fig. 3.3's "Equation" curve (≈0.23 m at 41 Hz) matches r = 1.524e-3, so the plotted results used the code value. 1.524 mm = 0.060 in, which is plausibly the tine *diameter* (my inference, unverified). |
| Density | ρ (kg/m³) | 7850 | 7850 | steel |
| Young's modulus | E (Pa) | 2e11 | 2e11 | |
| Freq.-indep. damping | σ0 (s⁻¹) | 0.0001 | 0.0005 | `Python/ideal_bar.py` uses 0.001 |
| Freq.-dep. damping | σ1 (m²/s) | 0.005 | 0.001 | `ideal_bar.py` uses 0.005 |
| Length | L (m) | from Eq. 3.8 | from Eq. 3.8 (`calculateLength`) | `TineLengths.h` (the manual's cutting chart) is in the repo but **unused** |
| Min grid intervals | N | ≥ 8 (§4.1) | `jassert(N >= 10)` | |

### Hammer (Tab. 3.2, p. 14, vs `code:Hammer.h`)

| Name | Symbol (unit) | Thesis | Code | Notes |
|---|---|---|---|---|
| Hammer mass | M_h (kg) | 0.011 | 0.011 | |
| Impact exponent | α_h | 2.8 | 2.8 | code comment: "typically in range [1.5, 3.5]" |
| Stiffness | k_h (N/m^α) | 1.5e11 | 1.5e12 | Fig. 5.3 tests both values |
| Max initial velocity | v_in (m/s) | 4 | 6 (`config::mpe::maxInputVelocity`) | |
| Force damping weight | λ (N·s/m^{5/2}) | 9e10 | — | |
| μ_h = λ/k_h | (s/m) | 0.6 (derived) | 0.6 | |
| Initial hammer position | u_in (m) | — | −1e-4 | |
| Contact location | x_c | "varies per tine" (§3.3); evaluation uses 0.2L and 0.4L (Fig. 5.3) | grid index floor(0.33·M_u), min 4, on the base half → ≈0.165 L from the clamp (ESTIMATE from indexing) | single point |
| Evaluation velocity | — | 2 m/s (§5.1) | — | |

**Velocity mapping:** v_hammer = (MIDI velocity / 127) × v_max. It is linear (`code:Tine.cpp noteStarted`, `noteOnVelocity.asUnsignedFloat()`). There is no velocity-dependent stiffness or contact position. Velocity enters only through the Hunt–Crossley nonlinearity and the pickup nonlinearities.

### Damper (Tab. 3.3, p. 16)

| Name | Symbol (unit) | Value | Notes |
|---|---|---|---|
| Linear spring | K1 (N/m) | 100 | |
| Cubic spring | K3 (N/m³) | 100000 | |
| Damping | R (kg/s) | 0.5 | |
| Location | — | code: w-grid index floor(0.5·M_w), with w0 = tip → ≈0.25 L from the tip (ESTIMATE) | active whenever the note is released; no sustain-pedal handling in code |

### Pickup / output (`code:Configuration.h`, `PluginProcessor.cpp createParams`)

| Name | Default | Range | Notes |
|---|---|---|---|
| Tine gain (displacement → pickup input) | 10000 | 1–20000 | applied to u_tip in metres |
| LP cutoff ("Tone") | 1000 Hz | 200–2000 Hz | "controls brightness of attack" (§4.1) |
| LP resonance | 0.404061 | 0.1–1.0 | JUCE SVF-TPT |
| HP resonance | 0.404061 | 0.1–1.0 | |
| HP cutoff | f0 of note | — | §4.1 |
| Pickup gain | 15 dB | 0.1–30 dB | before tanh |
| Symmetry | 15 dB | 0.1–30 dB | exponent gain of the 2^(g·x) shaper |
| Master volume | 1.0 | 0.1–2.0 | |
| Param smoothing | 0.2 s | — | linear or multiplicative |
| Control-rate parameter polling | 60 Hz | — | §4.1 |

### Implementation constants

| Name | Value | Provenance |
|---|---|---|
| Host sample rate | 44.1 kHz assumed (§2.1, §4.1); prototypes use 48 kHz × 32 (`ideal_bar.py`) | |
| Oversampling | thesis: "minimum of 16 times" for the full range (§4.1); code: per note 4x (MIDI < 40), 8x (< 52), 16x (< 64), 32x (≥ 64) (`calculateOversampling`). `config::oversampling = 32` is unused. | §4.1, §4.2 "Sample-rate" |
| Voices | thesis: 5 by default (§4.1); code: `numVoices = 1` | |
| Note range | MIDI 28–100 (E1–E7, 73 keys) | `Configuration.h` |
| Pitch-bend range | ±1 semitone | §4.1 |
| Output read-out | tip grid point `w[1][0]` | `Tine.cpp processSample` |

### Per-key data

The only per-key measured data in the source is the **Rhodes service-manual tine cutting chart** (73-key). The thesis states its range as 0.1564 → 0.0226 m (§3.2.1). The full list is in `code:TineLengths.h`; the mapping of index to MIDI 28 + i is my inference from count and order. The other columns are **ESTIMATES** that I computed from the code's parameters (r = 1.524e-3, σ1 = 0.001, fs = 44.1 kHz, per-note oversampling):
- `L_eq38_m`: model length from Eq. 3.8.
- `N_intervals`: floor(L/h), with h from Eq. 3.3.
- `point_updates_per_out_sample`: N × oversampling.

No per-key hammer stiffness, contact position, decay or pickup geometry is given. The thesis only states qualitatively that contact moves toward the base and stiffness rises for higher notes (§3.3).

```csv
midi,note,f0_hz,L_manual_m,L_eq38_m_EST,oversampling_code,N_intervals_EST,point_updates_per_out_sample_EST
28,E1,41.20,0.1564,0.2286,4,34,136
29,F1,43.65,0.1524,0.2221,4,33,132
30,F#1,46.25,0.1484,0.2158,4,32,128
31,G1,49.00,0.1437,0.2097,4,31,124
32,G#1,51.91,0.1405,0.2037,4,30,120
33,A1,55.00,0.1357,0.1979,4,29,116
34,A#1,58.27,0.1315,0.1923,4,29,116
35,B1,61.74,0.1286,0.1868,4,28,112
36,C2,65.41,0.1258,0.1815,4,27,108
37,C#2,69.30,0.1214,0.1763,4,26,104
38,D2,73.42,0.1179,0.1713,4,25,100
39,D#2,77.78,0.1131,0.1664,4,25,100
40,E2,82.41,0.1107,0.1617,8,34,272
41,F2,87.31,0.1084,0.1571,8,33,264
42,F#2,92.50,0.1052,0.1526,8,32,256
43,G2,98.00,0.1032,0.1483,8,31,248
44,G#2,103.83,0.1008,0.1440,8,30,240
45,A2,110.00,0.0984,0.1399,8,29,232
46,A#2,116.54,0.0953,0.1359,8,29,232
47,B2,123.47,0.0929,0.1321,8,28,224
48,C3,130.81,0.0897,0.1283,8,27,216
49,C#3,138.59,0.0873,0.1247,8,26,208
50,D3,146.83,0.0849,0.1211,8,25,200
51,D#3,155.56,0.0818,0.1177,8,25,200
52,E3,164.81,0.0798,0.1143,16,34,544
53,F3,174.61,0.0778,0.1111,16,33,528
54,F#3,185.00,0.0762,0.1079,16,32,512
55,G3,196.00,0.0746,0.1048,16,31,496
56,G#3,207.65,0.0715,0.1018,16,30,480
57,A3,220.00,0.0703,0.0989,16,29,464
58,A#3,233.08,0.0673,0.0961,16,29,464
59,B3,246.94,0.0663,0.0934,16,28,448
60,C4,261.63,0.0647,0.0907,16,27,432
61,C#4,277.18,0.0635,0.0882,16,26,416
62,D4,293.66,0.0619,0.0856,16,25,400
63,D#4,311.13,0.0599,0.0832,16,25,400
64,E4,329.63,0.0579,0.0808,32,34,1088
65,F4,349.23,0.0564,0.0785,32,33,1056
66,F#4,369.99,0.0540,0.0763,32,32,1024
67,G4,392.00,0.0532,0.0741,32,31,992
68,G#4,415.30,0.0516,0.0720,32,30,960
69,A4,440.00,0.0508,0.0700,32,29,928
70,A#4,466.16,0.0500,0.0680,32,29,928
71,B4,493.88,0.0484,0.0660,32,28,896
72,C5,523.25,0.0464,0.0642,32,27,864
73,C#5,554.37,0.0452,0.0623,32,26,832
74,D5,587.33,0.0440,0.0606,32,25,800
75,D#5,622.25,0.0429,0.0588,32,25,800
76,E5,659.26,0.0417,0.0572,32,24,768
77,F5,698.46,0.0405,0.0555,32,23,736
78,F#5,739.99,0.0397,0.0540,32,23,736
79,G5,783.99,0.0381,0.0524,32,22,704
80,G#5,830.61,0.0373,0.0509,32,21,672
81,A5,880.00,0.0361,0.0495,32,21,672
82,A#5,932.33,0.0349,0.0481,32,20,640
83,B5,987.77,0.0341,0.0467,32,19,608
84,C6,1046.50,0.0335,0.0454,32,19,608
85,C#6,1108.73,0.0329,0.0441,32,18,576
86,D6,1174.66,0.0322,0.0428,32,18,576
87,D#6,1244.51,0.0310,0.0416,32,17,544
88,E6,1318.51,0.0298,0.0404,32,17,544
89,F6,1396.91,0.0294,0.0393,32,16,512
90,F#6,1479.98,0.0286,0.0381,32,16,512
91,G6,1567.98,0.0278,0.0371,32,15,480
92,G#6,1661.22,0.0270,0.0360,32,15,480
93,A6,1760.00,0.0262,0.0350,32,14,448
94,A#6,1864.66,0.0258,0.0340,32,14,448
95,B6,1975.53,0.0250,0.0330,32,14,448
96,C7,2093.00,0.0246,0.0321,32,13,416
97,C#7,2217.46,0.0242,0.0312,32,13,416
98,D7,2349.32,0.0238,0.0303,32,12,384
99,D#7,2489.02,0.0230,0.0294,32,12,384
100,E7,2637.02,0.0226,0.0286,32,12,384
```

The per-key `L_eq38/L_manual` ratio runs from about 1.46 (bass) to 1.27 (top). In other words, the model's tine is 27–46 % longer than the real one, because the tuning-spring mass is ignored. This matches Fig. 3.3.

## Discretization / algorithm

**Scheme and grid**
- **Scheme:** explicit, two-step (three time levels) FDTD for the damped EB bar (Eq. 4.1). Clamped base (2 fixed points). Free tip via matrix-row stencils (Eqs. 3.9, 3.10). Dynamic-grid inner boundary with 4 special stencils (App. C).
- **Sample rate:** the host rate (44.1 kHz), with internal oversampling factor j, so k = 1/(fs·j) (§4.1).
  - The thesis says ≥16x is needed for the full key range.
  - The code uses 4/8/16/32x per note range, to keep N roughly constant (§4.2 "Sample-rate").
- **Stability:** h ≥ h_min(k, κ, σ1) from Eq. 3.3, and the thesis runs at equality. Since N = floor(L/h_min), the short treble tines get very few points unless k is small. That is the reason for the oversampling.
- **Grid size (ESTIMATE, my calculation from code parameters):**
  - N ≈ 12–34 intervals per note (table above).
  - Without oversampling, N would be 17 (E1) down to 2 (E7). This is why oversampling is mandatory: the thesis/code need N ≥ 8–10.

**State per voice**
- 3 time levels × (M_u+1 + M_w+1) floats ≈ 3 × (N+2) ≤ ~108 floats.
- Plus the hammer (4 floats), the 1-point contact vector (M_u+1 floats in code), 2 SVFs and gains.
- The code reserves 100 floats per vector.

**Precomputation (§4.2 "Pre-computed coefficients")**
- C0, C1, M0, B0, S, D are computed per note and per parameter change, outside the sample loop.
- So are the boundary coefficients F0..F2 and the inner-boundary coefficients A0..A5, E1.
- Pointer-swap of 3 state buffers (no copying). Memory is reserved so the dynamic grid never reallocates.
- The w-vector is index-reversed so both halves are push/pop stacks (§4.2).

**Operation count (ESTIMATE, mine; none is reported in the thesis)**
- **Interior point update:** 6 multiplies + 8 adds ≈ 14 flops. Boundary and inner points are similar (≈9–11 terms).
- **Hammer, while active:** a dot product over the u-grid (M_u+1 ≈ N/2 MACs) + a `powf` + a few ops, per sub-step.
- **Worst case per output sample per voice (E4–A4 region):** N × j = 34 × 32 ≈ 1088 point updates.
  - That is ≈ 15k flops, plus ≈ 600 hammer MACs while in contact.
  - **≈ 0.7 GFLOP/s per voice at 44.1 kHz.**
- **Key-averaged:** ≈ 475 point updates/sample → ≈ 6.6k flops/sample → ≈ 0.29 GFLOP/s per voice.
- **Pickup:** 2 SVF-TPT filters + tanh + 2 `powf` + a cubic ≈ 40–60 flops/sample (2 `powf`/sample in float).

**Reported CPU cost: none.** The thesis gives no timing, CPU %, voice-count benchmarks or hardware specs. It only says that 5 voices is "a balance between playability and computational requirements" (§4.1) and that the bottleneck is the CPU (§4.2). The code ships with 1 voice.

**Artifacts / known numerical issues**
- The virtual-point free boundary is unstable with σ1 (§3.2.2).
- Removing grid points causes high-frequency artifacts (§6.3, citing [5, 6]).
- The rigid-barrier damper clicks (Fig. 3.4).
- Too-soft or too-low hammer contact on short tines gives "no output": the long contact time damps the tine (§5.1, p. 25).

## Measured / reference behaviour

**Section 5.1 (sound production), tip displacement, hammer at 2 m/s, notes F1 (43.65 Hz) and C4**
- **Reference Rhodes data quoted from other papers (validation targets):**
  - Tine output is "approximately sinusoidal shortly after excitation" (Muenster & Pfeifle 2014 [28]).
  - Two overtones at partial ratios **7.11 and 20.25** for F1, measured by SLDV (Gabrielli et al. 2020 [25]).
- **Model:** two overtones at **6.37 and 35.27** that last the whole duration. For C4 the second overtone is "significantly reduced". Both notes are "significantly out of tune" (flat).
- **My reading of Figs. 5.2 and 5.3 (ESTIMATE, from images):**
  - The plotted model partials match an ideal EB cantilever: mode ratios 1 : 6.27 : 17.55 : 34.39 : 56.8 : 84.9. Lines at ≈8, 52, 285, 470, 700 Hz for C4 match modes 1, 2, 4, 5, 6; mode 3 is not visible.
  - The plotted fundamentals (≈1.4 Hz for F1, ≈8 Hz for C4) are ≈ f0/32. This suggests either a sample-rate/oversampling bookkeeping error in the analysis or the reported mistuning. It cannot be resolved from the thesis.
  - Either way: a **uniform EB cantilever's mode-2 ratio (~6.27) is lower than the real Rhodes 7.11, and the real second overtone (~20) does not exist in a uniform beam.** The real tine is not a uniform cantilever: tuning-spring mass, swaged base, tone-bar coupling.
- **Fig. 5.1:** F1 tip displacement ≈ ±2e-5 m peak, with essentially no visible decay over 5 s (ESTIMATE from figure).
- **Fig. 5.3 (C4, contact at 0.2L vs 0.4L, k_h = 1.5e11 vs 1.5e12):** a contact closer to the base gives more and stronger overtones. Higher stiffness acts similarly but more weakly. Contact location is the dominant timbre control (§5.1, p. 25).

**Section 5.2 (tone production), A4 at MIDI velocity 100, compared with the Rhodes V8 plugin (MK8 Factory Default)**
- The model was manually re-tuned for this note.
- Model waveform period pattern repeats every 3 periods. Peak amplitude ≈ 0.2 vs V8 ≈ 0.05 (Fig. 5.4).
- Spectrum (Fig. 5.5): V8 shows a strong f0 with harmonics at 0.88, 1.32 and 1.76 kHz that decay faster as they go higher. The model has the same harmonics, sustained longer, plus many inharmonic lines (≈0.15, 0.58, 1.02, 1.43, 1.88 kHz; ESTIMATE from figure).
- The thesis attributes the harshness to the pickup chain, which assumes a near-sinusoidal input (§6.2).

**Section 5.3 (user interviews)**
- Only 2 users, informal. Setup: Roli Lumi Keys, laptop speakers.
- Users found the pitch bend smooth and natural, but the base note and max bend were out of tune.
- The ±1-semitone range was inadequate for one user. One user suggested mapping tone to aftertouch.
- **There is no formal listening test or MUSHRA.**

**Discussion (§6):**
- Sustain is too long. Fix with more σ1, a new σ2 term (Eq. 6.1) or a better contact location.
- Tuning needs modal analysis of the scheme instead of Eq. 3.8.
- The pickup should be physically modeled (Pfeifle [15]).
- The thesis cites [28] for the claim that the pickup is the most important element of the Rhodes sound.

## FM-1 implementation notes

My assessment, for 8 voices on the AC791N: no FPU, fixed point, < 2.9 ms per 256-frame block.

1. **The FDTD approach as published is infeasible.**
   - Even the key-averaged cost (≈475 point updates ≈ 6–7k ops per output sample per voice, ESTIMATE) × 8 voices × 44.1 kHz ≈ 2.3 G ops/s. The worst case (E4–A4, ≈15k ops/sample/voice) is ≈ 5.3 G ops/s.
   - That is one to two orders of magnitude beyond the budget. The exact budget depends on the AC791N clock, which I did not verify, but it is a few hundred MHz class.
   - The oversampling (up to 32x) is the killer. It is forced by the explicit-scheme CFL bound (Eq. 3.3) on short, stiff tines.
   - Do **not** port the FD tine. The dynamic grid (pitch bend through grid surgery) is irrelevant for FM-1. Pitch bend is trivial in a modal or oscillator model.
2. **Replace FD with a modal tine.** Use the same physics, diagonalised, with modes precomputed on the host.
   - Each mode is a 2-pole resonator: y[n] = a1·y[n−1] − a2·y[n−2] + b·x[n], or a coupled-form/phasor oscillator for numerical robustness at low f/fs.
   - About 3–4 modes per voice (fundamental + 2–3 overtones) costs roughly 15–25 MACs per sample per voice.
   - **Do not use the uniform-EB ratios** (6.27, 17.55, 34.39). The thesis itself shows they are wrong for the Rhodes. Take per-key partial ratios and decays from measurements (Gabrielli et al. [25]: 7.11, 20.25 for F1) or from other agents' sources, and store them as Q-format tables per key.
   - The per-key table in this file is useful mainly for the **manual tine lengths** (input to any host-side beam or modal analysis that includes a tip mass for the tuning spring).
3. **Hammer.**
   - The Hunt–Crossley contact (x^2.8 with a 1e11–1e12 stiffness) is extremely stiff. It needs a tiny time step, so it is a stability hazard in fixed point.
   - Option A: drive the modes with a host-precomputed force pulse per velocity layer (a raised-cosine or half-sine of duration T_c(v)). Set mode excitation weights from the mode shape at the contact position, φ_n(x_c).
   - Option B: compute the contact force once per sample, in the modal domain, using a LUT for x^α. That still needs care with stiffness scaling.
   - The thesis' main qualitative result is worth keeping as a per-key parameter: contact position near the base gives more overtones (Fig. 5.3). This means modal excitation weights φ_n(x_c) per key and velocity-dependent brightness.
4. **Damper.**
   - Do not use the K1/K3/R spring. On note-off, crossfade each mode's per-sample decay coefficient to a "damped" value (a table per key) over a few ms, to avoid clicks.
   - Fig. 3.4 confirms that abrupt damping clicks.
5. **Pickup.**
   - The EP-MK1-style chain is cheap and can be implemented in fixed point:
     - 2 SVFs (Chamberlin/TPT in Q1.31 with 64-bit accumulators).
     - A tanh LUT (e.g. 1024 entries + linear interpolation).
     - The exponential shaper (2^(g·x) − 1)/2^g as one combined LUT, since it is a static function of x for a fixed "symmetry". **Fold tanh → exp-shaper → cubic into a single 1-D waveshaper LUT** per preset.
   - The thesis' conclusion is that this chain sounds harsh when its input has overtones. On FM-1, feed it a mostly sinusoidal tine signal, or use a physically motivated pickup nonlinearity (displacement → flux LUT, Pfeifle/Falaize) instead.
   - A static 1-D LUT on tip displacement plus a differentiator (the EMF is dΦ/dt) is the cheapest physically motivated option.
6. **Q-format concerns.**
   - Displacements here are ~1e-5 m, so normalise the state to full scale and never use SI units in fixed point.
   - The "tine gain" of 10000 shows how badly scaled the signal is.
   - The modal resonator coefficients for 41 Hz at 44.1 kHz are a1 ≈ 2cos(ω) ≈ 1.99965. This needs Q2.30 or better, or the coupled-form/Chamberlin structure, to keep pitch accuracy and decay (decay times of tens of seconds mean r ≈ 1 − 1e-6).
   - Use a 32×32→64 multiply and a shift. 64-bit multiply is OK on target; avoid 64-bit divide entirely (all divisions are precomputed on the host).
7. **Risks.**
   - **Tuning:** this source shows how easily a physical tine model ends up mistuned. Make f0 an explicit table value, not derived from geometry.
   - **Over-sustained overtones:** the thesis model's overtones never decayed. The per-mode decay tables must have overtones decaying much faster than the fundamental.
   - **Weak source data:** there is no quantitative per-key data on decay, attack or velocity → timbre. Other sources must provide it.

## Gaps & open questions

- **No CPU or performance numbers at all.** It is unknown whether 5 voices actually ran in real time, or on what hardware.
- **Unit inconsistency in the hammer coupling.** Eq. 3.19 lacks 1/M_h, and Eq. 3.21 uses M = M_h/(ρAL) as a scale on F. Hammer parameters are therefore effectively tuned constants, not physical ones.
- **Tab. 3.1 vs code disagreements:** r, σ0, σ1, k_h, v_max, number of voices, oversampling. It is unclear which set produced which figure. Fig. 3.3 implies r = 1.524 mm.
- **Root cause of the mistuning was not identified.** Possible causes:
  - inaccurate Eq. 3.8;
  - numerical dispersion at the CFL limit;
  - the dynamic-grid fractional point;
  - an analysis/plot sample-rate bug. The ≈ f0/32 fundamentals in Figs. 5.2/5.3 point to this (my inference).
- **Reference data is only quoted, never measured.** The 7.11/20.25 ratios are cited from Gabrielli et al. [25], for F1 only. There are no decay times, T60s, attack times, contact durations or velocity → spectrum data.
- **No tone-bar or tuning-spring model,** so beating, double decay and the "bark" partials from tone-bar coupling are absent.
- **The pickup is non-physical.** Its parameters come from a commercial plugin's documentation [23] and are not measured.
- **Per-key hammer contact positions and stiffnesses** are said to vary (§3.3) but are not tabulated. The code uses a fixed 0.33·M_u.
- **The index-to-MIDI mapping of `TineLengths.h`** (73 entries mapped to MIDI 28–100) is inferred.
- **Repo licence:** none (all rights reserved by default). The thesis text has a "publication requires agreement with author" clause. Use the ideas, but do not copy code.

## Machine-readable

```json
{
  "source": {
    "id": "02-sonderbo-thesis",
    "title": "Real-time physical model of the Rhodes Electric Piano",
    "authors": ["Tobias Sønderbo"],
    "supervisor": "Stefania Serafin",
    "year": 2024,
    "venue": "MSc thesis, Aalborg University (Architecture, Design and Media Technology)",
    "url": "https://projekter.aau.dk/projekter/files/719175589/Master_Thesis_Real_time_physical_model_of_the_Rhodes_Electric_Piano_Tobias_Sonderbo.pdf",
    "code_repo": "https://github.com/TSonderbo/EPiano",
    "code_commit": "03fa04463ab1cf493f53ae7413d101a8ec5bc101",
    "licence": "thesis: freely available, publication requires author agreement; repo: no licence file",
    "fetched": true
  },
  "blocks": {
    "hammer": {"modeled": true, "method": "Hunt-Crossley penalty contact, lumped mass, single-point contact", "provenance": "Sec 3.3, Eq 3.19-3.21, Tab 3.2"},
    "tine": {"modeled": true, "method": "explicit FDTD Euler-Bernoulli bar, clamped-free, sigma0/sigma1 losses, dynamic grid", "provenance": "Sec 3.2, Eq 3.2-3.18, App A-C"},
    "tuning_spring": {"modeled": false, "method": "approximated by lengthening tine via Eq 3.8", "provenance": "Sec 3.2.1"},
    "tonebar": {"modeled": false, "method": "folded into sigma0/sigma1", "provenance": "Sec 3.2 p9"},
    "damper": {"modeled": true, "method": "damped nonlinear spring (K1,K3,R) from one tine point to equilibrium", "provenance": "Sec 3.4, Eq 3.22-3.23, Tab 3.3"},
    "pickup": {"modeled": true, "physical": false, "method": "SVF LP -> gain -> tanh -> exp asym shaper -> cubic -> SVF HP at f0 (after Mike Moreno EP-MK1)", "provenance": "Sec 3.5, code MagneticPickup.cpp"},
    "preamp": {"modeled": false},
    "tremolo": {"modeled": false},
    "speaker_cabinet": {"modeled": false},
    "mechanical_noise": {"modeled": false},
    "mpe": {"modeled": true, "method": "per-note pitch bend +-1 semitone via dynamic grid tine length", "provenance": "Sec 4.1"}
  },
  "params": {
    "tine": {
      "rho_kg_m3": 7850,
      "E_Pa": 2e11,
      "radius_m": {"thesis_tab3_1": 0.0005, "code": 0.001524},
      "sigma0_per_s": {"thesis_tab3_1": 0.0001, "code": 0.0005},
      "sigma1_m2_per_s": {"thesis_tab3_1": 0.005, "code": 0.001},
      "length_formula": "L = sqrt(1.426*pi*(r/2)*sqrt(E/rho)/(8*f0))",
      "stability": "h >= sqrt((4*sigma1*k + sqrt((4*sigma1*k)^2 + 16*kappa^2*k^2))/2)",
      "min_grid_intervals": {"thesis": 8, "code": 10},
      "output_point": "tip"
    },
    "hammer": {
      "mass_kg": 0.011,
      "alpha": 2.8,
      "stiffness_N_per_m_alpha": {"thesis_tab3_2": 1.5e11, "code": 1.5e12},
      "lambda_Ns_per_m2_5": 9e10,
      "mu_h_s_per_m": 0.6,
      "v_max_m_s": {"thesis_tab3_2": 4, "code": 6},
      "initial_position_m": -1e-4,
      "contact_position_fraction_from_base": {"code_estimate": 0.165, "evaluated": [0.2, 0.4]},
      "velocity_mapping": "v = (midi_vel/127) * v_max, linear"
    },
    "damper": {"K1_N_per_m": 100, "K3_N_per_m3": 100000, "R_kg_per_s": 0.5, "position_fraction_from_tip_code_estimate": 0.25},
    "pickup": {
      "tine_gain": 10000,
      "lp_cutoff_hz": 1000, "lp_cutoff_range_hz": [200, 2000],
      "svf_resonance": 0.404061,
      "pre_gain_db": 15, "symmetry_db": 15,
      "hp_cutoff": "f0",
      "nonlinearity": "tanh(g*x) -> (2^(gs*x)-1)/2^gs -> y - y^3/3"
    },
    "implementation": {
      "host_fs_hz": 44100,
      "oversampling": {"thesis": "min 16", "code_by_midi": {"<40": 4, "<52": 8, "<64": 16, ">=64": 32}},
      "voices": {"thesis": 5, "code": 1},
      "midi_range": [28, 100],
      "pitch_bend_semitones": 1,
      "reported_cpu_cost": null,
      "estimated_point_updates_per_output_sample": {"max": 1088, "mean": 474, "provenance": "ESTIMATE"}
    },
    "reference_targets": {
      "rhodes_F1_partial_ratios_cited": [7.11, 20.25],
      "model_F1_partial_ratios": [6.37, 35.27],
      "ideal_eb_cantilever_ratios": [1, 6.267, 17.55, 34.39],
      "tip_displacement_peak_m_F1_v2mps_ESTIMATE": 2e-5
    }
  },
  "per_key": [
    {"midi": 28, "note": "E1", "f0_hz": 41.2, "tine_length_manual_m": 0.1564, "model_length_eq3_8_m": 0.2286, "oversampling": 4, "grid_intervals_N": 34, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 29, "note": "F1", "f0_hz": 43.65, "tine_length_manual_m": 0.1524, "model_length_eq3_8_m": 0.2221, "oversampling": 4, "grid_intervals_N": 33, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 30, "note": "F#1", "f0_hz": 46.25, "tine_length_manual_m": 0.1484, "model_length_eq3_8_m": 0.2158, "oversampling": 4, "grid_intervals_N": 32, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 31, "note": "G1", "f0_hz": 49.0, "tine_length_manual_m": 0.1437, "model_length_eq3_8_m": 0.2097, "oversampling": 4, "grid_intervals_N": 31, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 32, "note": "G#1", "f0_hz": 51.91, "tine_length_manual_m": 0.1405, "model_length_eq3_8_m": 0.2037, "oversampling": 4, "grid_intervals_N": 30, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 33, "note": "A1", "f0_hz": 55.0, "tine_length_manual_m": 0.1357, "model_length_eq3_8_m": 0.1979, "oversampling": 4, "grid_intervals_N": 29, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 34, "note": "A#1", "f0_hz": 58.27, "tine_length_manual_m": 0.1315, "model_length_eq3_8_m": 0.1923, "oversampling": 4, "grid_intervals_N": 29, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 35, "note": "B1", "f0_hz": 61.74, "tine_length_manual_m": 0.1286, "model_length_eq3_8_m": 0.1868, "oversampling": 4, "grid_intervals_N": 28, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 36, "note": "C2", "f0_hz": 65.41, "tine_length_manual_m": 0.1258, "model_length_eq3_8_m": 0.1815, "oversampling": 4, "grid_intervals_N": 27, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 37, "note": "C#2", "f0_hz": 69.3, "tine_length_manual_m": 0.1214, "model_length_eq3_8_m": 0.1763, "oversampling": 4, "grid_intervals_N": 26, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 38, "note": "D2", "f0_hz": 73.42, "tine_length_manual_m": 0.1179, "model_length_eq3_8_m": 0.1713, "oversampling": 4, "grid_intervals_N": 25, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 39, "note": "D#2", "f0_hz": 77.78, "tine_length_manual_m": 0.1131, "model_length_eq3_8_m": 0.1664, "oversampling": 4, "grid_intervals_N": 25, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 40, "note": "E2", "f0_hz": 82.41, "tine_length_manual_m": 0.1107, "model_length_eq3_8_m": 0.1617, "oversampling": 8, "grid_intervals_N": 34, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 41, "note": "F2", "f0_hz": 87.31, "tine_length_manual_m": 0.1084, "model_length_eq3_8_m": 0.1571, "oversampling": 8, "grid_intervals_N": 33, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 42, "note": "F#2", "f0_hz": 92.5, "tine_length_manual_m": 0.1052, "model_length_eq3_8_m": 0.1526, "oversampling": 8, "grid_intervals_N": 32, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 43, "note": "G2", "f0_hz": 98.0, "tine_length_manual_m": 0.1032, "model_length_eq3_8_m": 0.1483, "oversampling": 8, "grid_intervals_N": 31, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 44, "note": "G#2", "f0_hz": 103.83, "tine_length_manual_m": 0.1008, "model_length_eq3_8_m": 0.144, "oversampling": 8, "grid_intervals_N": 30, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 45, "note": "A2", "f0_hz": 110.0, "tine_length_manual_m": 0.0984, "model_length_eq3_8_m": 0.1399, "oversampling": 8, "grid_intervals_N": 29, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 46, "note": "A#2", "f0_hz": 116.54, "tine_length_manual_m": 0.0953, "model_length_eq3_8_m": 0.1359, "oversampling": 8, "grid_intervals_N": 29, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 47, "note": "B2", "f0_hz": 123.47, "tine_length_manual_m": 0.0929, "model_length_eq3_8_m": 0.1321, "oversampling": 8, "grid_intervals_N": 28, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 48, "note": "C3", "f0_hz": 130.81, "tine_length_manual_m": 0.0897, "model_length_eq3_8_m": 0.1283, "oversampling": 8, "grid_intervals_N": 27, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 49, "note": "C#3", "f0_hz": 138.59, "tine_length_manual_m": 0.0873, "model_length_eq3_8_m": 0.1247, "oversampling": 8, "grid_intervals_N": 26, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 50, "note": "D3", "f0_hz": 146.83, "tine_length_manual_m": 0.0849, "model_length_eq3_8_m": 0.1211, "oversampling": 8, "grid_intervals_N": 25, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 51, "note": "D#3", "f0_hz": 155.56, "tine_length_manual_m": 0.0818, "model_length_eq3_8_m": 0.1177, "oversampling": 8, "grid_intervals_N": 25, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 52, "note": "E3", "f0_hz": 164.81, "tine_length_manual_m": 0.0798, "model_length_eq3_8_m": 0.1143, "oversampling": 16, "grid_intervals_N": 34, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 53, "note": "F3", "f0_hz": 174.61, "tine_length_manual_m": 0.0778, "model_length_eq3_8_m": 0.1111, "oversampling": 16, "grid_intervals_N": 33, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 54, "note": "F#3", "f0_hz": 185.0, "tine_length_manual_m": 0.0762, "model_length_eq3_8_m": 0.1079, "oversampling": 16, "grid_intervals_N": 32, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 55, "note": "G3", "f0_hz": 196.0, "tine_length_manual_m": 0.0746, "model_length_eq3_8_m": 0.1048, "oversampling": 16, "grid_intervals_N": 31, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 56, "note": "G#3", "f0_hz": 207.65, "tine_length_manual_m": 0.0715, "model_length_eq3_8_m": 0.1018, "oversampling": 16, "grid_intervals_N": 30, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 57, "note": "A3", "f0_hz": 220.0, "tine_length_manual_m": 0.0703, "model_length_eq3_8_m": 0.0989, "oversampling": 16, "grid_intervals_N": 29, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 58, "note": "A#3", "f0_hz": 233.08, "tine_length_manual_m": 0.0673, "model_length_eq3_8_m": 0.0961, "oversampling": 16, "grid_intervals_N": 29, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 59, "note": "B3", "f0_hz": 246.94, "tine_length_manual_m": 0.0663, "model_length_eq3_8_m": 0.0934, "oversampling": 16, "grid_intervals_N": 28, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 60, "note": "C4", "f0_hz": 261.63, "tine_length_manual_m": 0.0647, "model_length_eq3_8_m": 0.0907, "oversampling": 16, "grid_intervals_N": 27, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 61, "note": "C#4", "f0_hz": 277.18, "tine_length_manual_m": 0.0635, "model_length_eq3_8_m": 0.0882, "oversampling": 16, "grid_intervals_N": 26, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 62, "note": "D4", "f0_hz": 293.66, "tine_length_manual_m": 0.0619, "model_length_eq3_8_m": 0.0856, "oversampling": 16, "grid_intervals_N": 25, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 63, "note": "D#4", "f0_hz": 311.13, "tine_length_manual_m": 0.0599, "model_length_eq3_8_m": 0.0832, "oversampling": 16, "grid_intervals_N": 25, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 64, "note": "E4", "f0_hz": 329.63, "tine_length_manual_m": 0.0579, "model_length_eq3_8_m": 0.0808, "oversampling": 32, "grid_intervals_N": 34, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 65, "note": "F4", "f0_hz": 349.23, "tine_length_manual_m": 0.0564, "model_length_eq3_8_m": 0.0785, "oversampling": 32, "grid_intervals_N": 33, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 66, "note": "F#4", "f0_hz": 369.99, "tine_length_manual_m": 0.054, "model_length_eq3_8_m": 0.0763, "oversampling": 32, "grid_intervals_N": 32, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 67, "note": "G4", "f0_hz": 392.0, "tine_length_manual_m": 0.0532, "model_length_eq3_8_m": 0.0741, "oversampling": 32, "grid_intervals_N": 31, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 68, "note": "G#4", "f0_hz": 415.3, "tine_length_manual_m": 0.0516, "model_length_eq3_8_m": 0.072, "oversampling": 32, "grid_intervals_N": 30, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 69, "note": "A4", "f0_hz": 440.0, "tine_length_manual_m": 0.0508, "model_length_eq3_8_m": 0.07, "oversampling": 32, "grid_intervals_N": 29, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 70, "note": "A#4", "f0_hz": 466.16, "tine_length_manual_m": 0.05, "model_length_eq3_8_m": 0.068, "oversampling": 32, "grid_intervals_N": 29, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 71, "note": "B4", "f0_hz": 493.88, "tine_length_manual_m": 0.0484, "model_length_eq3_8_m": 0.066, "oversampling": 32, "grid_intervals_N": 28, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 72, "note": "C5", "f0_hz": 523.25, "tine_length_manual_m": 0.0464, "model_length_eq3_8_m": 0.0642, "oversampling": 32, "grid_intervals_N": 27, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 73, "note": "C#5", "f0_hz": 554.37, "tine_length_manual_m": 0.0452, "model_length_eq3_8_m": 0.0623, "oversampling": 32, "grid_intervals_N": 26, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 74, "note": "D5", "f0_hz": 587.33, "tine_length_manual_m": 0.044, "model_length_eq3_8_m": 0.0606, "oversampling": 32, "grid_intervals_N": 25, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 75, "note": "D#5", "f0_hz": 622.25, "tine_length_manual_m": 0.0429, "model_length_eq3_8_m": 0.0588, "oversampling": 32, "grid_intervals_N": 25, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 76, "note": "E5", "f0_hz": 659.26, "tine_length_manual_m": 0.0417, "model_length_eq3_8_m": 0.0572, "oversampling": 32, "grid_intervals_N": 24, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 77, "note": "F5", "f0_hz": 698.46, "tine_length_manual_m": 0.0405, "model_length_eq3_8_m": 0.0555, "oversampling": 32, "grid_intervals_N": 23, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 78, "note": "F#5", "f0_hz": 739.99, "tine_length_manual_m": 0.0397, "model_length_eq3_8_m": 0.054, "oversampling": 32, "grid_intervals_N": 23, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 79, "note": "G5", "f0_hz": 783.99, "tine_length_manual_m": 0.0381, "model_length_eq3_8_m": 0.0524, "oversampling": 32, "grid_intervals_N": 22, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 80, "note": "G#5", "f0_hz": 830.61, "tine_length_manual_m": 0.0373, "model_length_eq3_8_m": 0.0509, "oversampling": 32, "grid_intervals_N": 21, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 81, "note": "A5", "f0_hz": 880.0, "tine_length_manual_m": 0.0361, "model_length_eq3_8_m": 0.0495, "oversampling": 32, "grid_intervals_N": 21, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 82, "note": "A#5", "f0_hz": 932.33, "tine_length_manual_m": 0.0349, "model_length_eq3_8_m": 0.0481, "oversampling": 32, "grid_intervals_N": 20, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 83, "note": "B5", "f0_hz": 987.77, "tine_length_manual_m": 0.0341, "model_length_eq3_8_m": 0.0467, "oversampling": 32, "grid_intervals_N": 19, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 84, "note": "C6", "f0_hz": 1046.5, "tine_length_manual_m": 0.0335, "model_length_eq3_8_m": 0.0454, "oversampling": 32, "grid_intervals_N": 19, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 85, "note": "C#6", "f0_hz": 1108.73, "tine_length_manual_m": 0.0329, "model_length_eq3_8_m": 0.0441, "oversampling": 32, "grid_intervals_N": 18, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 86, "note": "D6", "f0_hz": 1174.66, "tine_length_manual_m": 0.0322, "model_length_eq3_8_m": 0.0428, "oversampling": 32, "grid_intervals_N": 18, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 87, "note": "D#6", "f0_hz": 1244.51, "tine_length_manual_m": 0.031, "model_length_eq3_8_m": 0.0416, "oversampling": 32, "grid_intervals_N": 17, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 88, "note": "E6", "f0_hz": 1318.51, "tine_length_manual_m": 0.0298, "model_length_eq3_8_m": 0.0404, "oversampling": 32, "grid_intervals_N": 17, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 89, "note": "F6", "f0_hz": 1396.91, "tine_length_manual_m": 0.0294, "model_length_eq3_8_m": 0.0393, "oversampling": 32, "grid_intervals_N": 16, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 90, "note": "F#6", "f0_hz": 1479.98, "tine_length_manual_m": 0.0286, "model_length_eq3_8_m": 0.0381, "oversampling": 32, "grid_intervals_N": 16, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 91, "note": "G6", "f0_hz": 1567.98, "tine_length_manual_m": 0.0278, "model_length_eq3_8_m": 0.0371, "oversampling": 32, "grid_intervals_N": 15, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 92, "note": "G#6", "f0_hz": 1661.22, "tine_length_manual_m": 0.027, "model_length_eq3_8_m": 0.036, "oversampling": 32, "grid_intervals_N": 15, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 93, "note": "A6", "f0_hz": 1760.0, "tine_length_manual_m": 0.0262, "model_length_eq3_8_m": 0.035, "oversampling": 32, "grid_intervals_N": 14, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 94, "note": "A#6", "f0_hz": 1864.66, "tine_length_manual_m": 0.0258, "model_length_eq3_8_m": 0.034, "oversampling": 32, "grid_intervals_N": 14, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 95, "note": "B6", "f0_hz": 1975.53, "tine_length_manual_m": 0.025, "model_length_eq3_8_m": 0.033, "oversampling": 32, "grid_intervals_N": 14, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 96, "note": "C7", "f0_hz": 2093.0, "tine_length_manual_m": 0.0246, "model_length_eq3_8_m": 0.0321, "oversampling": 32, "grid_intervals_N": 13, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 97, "note": "C#7", "f0_hz": 2217.46, "tine_length_manual_m": 0.0242, "model_length_eq3_8_m": 0.0312, "oversampling": 32, "grid_intervals_N": 13, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 98, "note": "D7", "f0_hz": 2349.32, "tine_length_manual_m": 0.0238, "model_length_eq3_8_m": 0.0303, "oversampling": 32, "grid_intervals_N": 12, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 99, "note": "D#7", "f0_hz": 2489.02, "tine_length_manual_m": 0.023, "model_length_eq3_8_m": 0.0294, "oversampling": 32, "grid_intervals_N": 12, "hammer_contact": null, "hammer_stiffness": null, "decay": null},
    {"midi": 100, "note": "E7", "f0_hz": 2637.02, "tine_length_manual_m": 0.0226, "model_length_eq3_8_m": 0.0286, "oversampling": 32, "grid_intervals_N": 12, "hammer_contact": null, "hammer_stiffness": null, "decay": null}

  ]
}
```
