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
