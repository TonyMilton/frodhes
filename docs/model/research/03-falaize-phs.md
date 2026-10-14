# Falaize & Hélie: port-Hamiltonian Rhodes (hammer, modal cantilever tine, nonlinear pickup)

## Source

Local copies of all fetched material are in `docs/model/research/sources/03-falaize-phs/`. They are stored as data only, and no downloaded code was executed.

| # | URL | Fetched? | What it is |
|---|-----|----------|-----------|
| S1 | https://hal.science/hal-01390534/ (PDF: `hal-01390534v1/file/JSV_Rhodes_manuscript_round_2.pdf`) | yes, as `paper.pdf` / `paper.txt` (32 pp.) | **A. Falaize, T. Hélie, "Passive simulation of the nonlinear port-Hamiltonian modeling of a Rhodes Piano"**. Preprint deposited on HAL on 2 Nov 2016, manuscript dated 17 Sep 2016 ("round 2" revision). IRCAM-CNRS-UPMC (UMR 9912), funded by ANR HAMECMOPSYS (ANR-11-BS03-0002). HAL licence: "HAL Authorization", which is a deposit authorization and not Creative Commons. |
| S1' | https://hal.science/hal-01470949/ (metadata only) | metadata only | Published version: **Journal of Sound and Vibration 390 (2017) 289–309, doi:10.1016/j.jsv.2016.11.008** (online 2017-02-18). Not downloaded. All equations and numbers below come from the S1 preprint, so page and equation numbers refer to S1. |
| S2 | http://recherche.ircam.fr/anasyn/falaize/fr/applis/rhodes/ | yes (`ircam.html`) | Companion page "Simulation of the Fender Rhodes" (A. Falaize, 2015-10-13). It hosts the code zip, audio examples (A1/A2/A3/A4 force sweeps, pickup-position sweeps) and a comparison against UVI measurements. The site footer links CeCILL-B as its licence. |
| S3 | https://afalaize.github.io/posts/rhodes/ | yes (`blog.html`) | Same content as S2 (mirror on the author's blog, © 2021). Links the PDF and the code zip. |
| C1 | http://recherche.ircam.fr/anasyn/falaize/codes/code_rhodes_falaize.zip | yes (`code/code.zip`, 12.6 MB, extracted to `code/extracted/code_for_webpage/`) | **"Simulation code (Python 2.7) ... MAIN.py. All the results presented in the paper and [on the web page] were obtained from this code."** Contains `MAIN.py` (parameters and netlist), `pypHs.py` (an early pyPHS: discrete gradient plus Newton–Raphson), `utils/phs2cpp.py` (a C++ exporter), and `REF/REF1..8.wav` plus `REF.wav`/`allsigs.wav` (UVI measurements of A4 at 8 forces; 48 kHz, 16-bit mono, 5 s each). Licence header in `pypHs.py`: **CeCILL-B**. |
| C2 | https://github.com/pyphs/pyphs (master, last push 2022-02-11) | selected files (`pyphs/`) | Later PyPHS library. It ships **`pyphs/examples/rhodes/rhodes.net`** plus `rhodes.py`, and the components `dictionary/beams/_cantilever.py`, `dictionary/transducers/_pickup.py` and `dictionary/mechanics/_felt.py`. Licence: CeCILL-B ("PyPHS Licence", © Antoine Falaize, per `LICENSE.rst`). |

Not fetched: the published JSV PDF (paywalled), the DAFx-15 precursor paper [16], and the audio and image files on S2/S3. Those audio and image files were only listed (URLs below).

## Summary

- The paper models one Rhodes note as **hammer (nonlinear hysteretic felt, Hunt–Crossley/Stulov-type power law) → linear damped Euler–Bernoulli cantilever (the tine), truncated to M modes → nonlinear magnetic pickup (McDonald's guitar-pickup flux model) → RC (or RLC in the code) load**. It is written as one port-Hamiltonian system (PHS).
- The **tone bar, tuning spring/mass, damper, key action, preamp, tremolo, cabinet and noises are not modeled**. The tine length is used for tuning instead of a tuning mass.
- The tine has **analytic cantilever modes**. Modes below Nyquist are kept, which gives M = 4 for A4 at 48 kHz (440, 2757.49, 7721.07, 15130.22 Hz). Damping is either constant per mode (paper) or rises steeply with mode index (code).
- **The pickup is geometrically coupled but not energetically coupled.** It does not act back on the tine. Its output is `v ∝ g(q_tip)·dq_tip/dt` followed by a passive RC/RLC network. The paper says this pickup term "is the only one that is responsible for the characteristic Rhodes piano tones" because the beam is linear.
- **Discretization:** a discrete-gradient (energy-preserving) scheme at fs = 48 kHz. It is the midpoint/trapezoidal rule for the quadratic (linear) parts. The one nonlinear storage element (the felt) is solved implicitly by Newton–Raphson. The paper says this "allows real-time applications" but gives no timings.
- **Validation:** spectrograms and normalized waveforms compared with UVI recordings of A4 at 8 hammer forces. Agreement is qualitative ("perceptively relevant"). The recordings show extra 1–2 kHz content and different partial decays that the model misses.
- **For the FM-1:** running the full implicit PHS solver for 8 voices is not sensible. The model does factor into pieces that are cheap in fixed point: (a) a short nonlinear hammer–tine contact (a few ms, which could even be precomputed into a table), (b) M decoupled 2-pole modal resonators, (c) a static pickup nonlinearity `g(q)` (a LUT) multiplied by the velocity, and (d) a 2-pole RC/RLC filter.

## Model architecture

| Block | Modeled? | How (provenance) |
|---|---|---|
| Hammer | **Yes** | Rigid core mass `Mh` plus massless felt with a nonlinear elastic force `Fh·c^Bh` and a nonlinear damper (hysteresis). Driven by an external force on the core for about 1 ms, with a simple "exhaust": `f_ext = 0 if q_h > −0.5 cm` (S1 §3.1, §6). Contact force is spread over width `Dh` (= `wh` = 15 mm in the code) at position `zh` on the tine. |
| Tine | **Yes** | Linear damped Euler–Bernoulli cantilever (clamped–free, cylindrical steel). Projected onto analytic eigenmodes, keeping all modes below Nyquist (S1 §3.2, App. A). Damping is a single viscous coefficient `Ab` in the paper; the code makes it mode dependent. |
| Tuning spring / mass | **No** | Assumption (A4): tuning is done by changing the tine length `Lb`. The screws and springs (elements 7–9) are treated as a rigid clamp (A3). |
| Tone bar | **No** | Assumption (A2), flagged by the authors as "the most critical one". The tone bar stores and restores energy, enhancing sustain and shaping the attack. Listed first in their future work. |
| Damper | **No** | Ignored; the tine rings until it dies out (S1 §1.1). The authors suggest reusing the felt model for it. |
| Pickup | **Yes (nonlinear)** | Magnet plus coil (gyrator–capacitor approach). The flux comes from a magnetised sphere of radius ≈ tine radius moving near the coil (McDonald 2007, ref [26]). There is no back-action on the tine; the Maxwell force is neglected (§7). Position is adjustable by `Lhor` and `Lver`. |
| Preamp / amp | **Partly** | Only a passive RC load (`R_RC` = 1 kΩ, `C_RC` = 330 nF) in the paper. The 2016 code uses an R + C plus coil-inductance RLC tuned to `fRLC` = 5 kHz. No active preamp. |
| Tremolo | **No** | Not mentioned. |
| Cabinet / speaker | **No** | Not mentioned. |
| Noises (key thump, release, hum) | **No** | Not mentioned. The measured references contain low-frequency external noise, according to the Fig. 11 caption. |
| Polarisation / 3-D motion | **No** | Future work (§7). Planar motion only. |

Signal flow: `F_ext(t) → [hammer mass + nonlinear felt] ⇄ (contact force / velocity at z_h) ⇄ [M-mode cantilever] → (q_tip, dq_tip/dt at z=L_b) → [pickup: dφ/dt = f_p(q,dq/dt)] → [coil + RC/RLC] → v_0`

## Equations

The notation follows S1. Equation numbers refer to S1 unless marked "code".

### General PHS (S1 eq. 5–6)
`[dx/dt ; −y] = (J(x) − R(x)) · [∇H(x) ; u]`. Here J is skew-symmetric and R is positive semidefinite. Power balance: `dE/dt = P_ext − Q` with `P_ext = uᵀy` and `Q ≥ 0` (eq. 1–4).

### Hammer (S1 §3.1, eq. 9–15, Table 2–3)
- Felt compression `q_h = q_core + L_h − q_cont` [m]. Crush rate `c_h(q_h) = max(q_h,0)/L_h` [-] (eq. 9–10).
- Elastic force `f_elast = F_h · c_h^{B_h}` [N]. Damping force `f_damp = A_h L_h · d(c_h^{B_h})/dt` [N] (eq. 11).
- Core: `M_h d²q_core/dt² = −f_elast − f_damp + f_ext^core` (eq. 12).
- States: `x_h1 = M_h dq_core/dt` [N·s] with `H_h1 = x_h1²/(2M_h)` (eq. 13), and `x_h2 = q_h` [m] with **`H_h2 = L_h F_h/(B_h+1) · c_h(q_h)^{B_h+1}`** [J] (eq. 14). This energy is not even and not quadratic, which makes it the only nonlinear storage element.
- Nonlinear damping coefficient `r_h(q_h) = (A_h L_h / B_h) · c_h^{B_h−1}` (eq. 15).
- Equivalent power law (Table 2 caption): `f_elast = K e^p` and `f_damp = R d(e^p)/dt` with `e = L_h c_h`, `p = B_h`, **`K = L_h^{−B_h} F_h = 5×10⁵ N·m^−2.5`**, `R = L_h^{1−B_h} A_h = 100 N·s·m^−2.5`. My check gives K = 5.008×10⁵ and R = 100.16.
- The 2016 code (`MAIN.py` lines ~431–444) uses `H = kh/(β+1)·q_h^{β+1}` with `kh = 5e5` and β = 2.5, plus damping `Z_h = alphah·(1/β)·q_h^{β−1}·w` with `alphah = 0.184`. **Inconsistency:** the damping term there uses `A_h`, not `R` = 100, and is not normalised by `L_h`. PyPHS `_felt.py` uses `H = L F/(B+1)·(q/L)^{B+1}` and `r = (A L/B)(q/L)^{B−1}`, which matches eq. 14–15.

### Beam / tine (S1 §3.2, eq. 16–20, App. A)
- PDE: `M_b ∂²_t q + A_b ∂_t q + K_b ∂⁴_z q = f_b` on z∈(0,L_b), with `M_b = π R_b² ρ_steel` [kg/m] and `K_b = E_steel · π R_b⁴/4` [N·m²] (eq. 16, Table 4).
- Clamped–free boundary conditions: `q(0)=∂_z q(0)=0` and `∂²_z q(L)=∂³_z q(L)=0`.
- Wavenumbers: **`cosh(κ_m L_b) cos(κ_m L_b) + 1 = 0`** (eq. 18). Frequencies: `ω_m = κ_m² √(K_b/M_b)`. Tuning: pick `L_b` so that ω₁ = 2π·F_b.
- Modes (A.1): `ψ_m(z) = γ_m[θ_m(sin κ_m z − sinh κ_m z) + cos κ_m z − cosh κ_m z]` with `θ_m = (sin κL − sinh κL)/(cos κL + cosh κL)`. `γ_m` is the normalisation in eq. (A.2), chosen so that `⟨ψ_m,ψ_p⟩ = δ_mp`. At the free end, `|ψ_m(L_b)| = 2/√L_b` (my numeric check: 8.50 m^−½ for L_b = 55.36 mm, alternating sign).
- Modal ODE (eq. 19): **`M_b q̈_m + A_b q̇_m + K_b κ_m⁴ q_m = Ω_m f_b^ext`**, m=1..M. The modes are decoupled except through the hammer port. `Ω_m = ⟨σ_h, ψ_m⟩` is the projection of the contact distribution σ_h (a box of width D_h at z_h), given by (A.3).
- Pickup reads the tip: `q_p = Σ ψ_m(L_b) q_m` and `dq_p/dt = Σ ψ_m(L_b) p_m / M_b`, where `p_m = M_b q̇_m`.
- Energy: `H_b = ½ x_bᵀ W x_b` with `W = diag(K_b L, M_b⁻¹ I)` and `L = diag(κ_m⁴)` (eq. 20).
- Mode selection: keep the M lowest modes with `ν_M < fs/2 < ν_{M+1}`.

### Pickup (S1 §3.3, eq. 21–28, Table 6–7)
- Coil as magnetic capacitor: `x_coil = φ_coil` and `H_coil = φ_coil²/(2C_coil)`. Gyrator to the electrical side, ratio `1/N_coil` (Ampère `h = N i`, Faraday `v = N dφ/dt`) (eq. 21).
- Flux from the moving magnetised sphere (eq. 22–23):
  `φ_p = 4 B_p^mag R_p (4 R_p³ ΔU [f_φ(−(q_p+L_ver)) + f_φ(q_p+L_ver)] − 1)` (the layout in the PDF is partly garbled), with `f_φ(q) = (q+R_p)/√(L_hor² + (q+R_p)²)` and `ΔU = (U_rel − 1)/(U_rel + 1)`.
- **Flux rate, the key nonlinearity (eq. 24–27):**
  `dφ_p/dt = f_p(q_p, dq_p/dt) · H_p^mag` with
  **`f_p = 2 a_b² U_0 ΔU R_p · [ (f_1 − 2L_hor²)/f_1² − (f_2 − 2L_hor²)/f_2² ] · dq_p/dt`**,
  `f_1(q) = (q − R_p + L_ver)² + L_hor²` and `f_2(q) = (q + R_p + L_ver)² + L_hor²`.
  Here `a_b` is the sphere (tine) radius, `R_p` the coil radius, `L_hor` the gap between coil and tine, `L_ver` the offset of the tine axis from the coil centre, and `q_p` the tip displacement. `H_p^mag = B_p/U_0` is a constant magnetomotive force.
  The output therefore has the form **`dφ/dt = G(q)·q̇`, a static nonlinearity of position times velocity**. This is equivalent to `d/dt[Φ(q)]` with `Φ' = G`.
- In code: `f1 = 2 r² dmu ap ((a1−2lp²)/a1² − (a2−2lp²)/a2²)·dtxp`, with `a1 = (xp − ap + dlp)² + lp²` and `a2 = (xp + ap + dlp)² + lp²` (`MAIN.py` ~468). The code uses `mu0 = 1` and `h0 = 1` (normalised units), `murel = 700` and `ap = 1e-3`. PyPHS `_pickup.py` sets `dmu = 1` ("set dmu ... to 1").
- PHS of the pickup plus RC (Table 7): states `(φ_coil, q_C)` and `H_p = ½ xᵀ diag(C_coil⁻¹?, C_RC⁻¹) x`. Note: the paper writes `diag(C_coil, C_RC)`, which looks like a typo. Inputs are `(H_p^mag, i_0 = 0)`; the output is `v_0`. Dissipation `R_RC/N_coil²`. The nonlinearity enters only through `f_p` in the gain matrix G.

### Interconnection (S1 §4, eq. 29, Table 8)
Contact velocity = `Ωᵀ ∇_p H_b`. Beam force = `−f_cont`. Total state is `x = (x_h, x_b, x_p)` with dimension `2 + 2M + 2` (the code has `nx = 2nk + 4`). The pickup is coupled only geometrically, through `q_p` and `q̇_p` in `f_p`.

### Discretization (S1 §5, eq. 30–37)
- Discrete gradient (eq. 31): `[∇_d H]_n = (H_n(x_n+δx_n) − H_n(x_n))/δx_n`, falling back to `H_n'(x_n)` if `δx_n = 0`.
- Update (eq. 35–37): `x_{k+1} = x_k + δx_k` and `δx_k = T(J_x − R_x)∇_d H + T(G − R_xy)u_k`. Structure matrices are evaluated at `x_k`. The implicit equation is solved by a fixed number of Newton–Raphson iterations.
- For quadratic `H_n` this reduces to the midpoint rule (= trapezoidal/bilinear for constant J and R) (Remark 3). It is first-order consistent in general and second order for constant J and R (Remark 2).
- Discrete power balance: `(E_{k+1} − E_k)/T = −Q_k + P_ext,k` (eq. 30), which holds to machine epsilon in their plots (Fig. 8–9).

## Parameters

### Hammer (S1 Table 2, "typical values", note A4)
| Symbol | Meaning | Paper (S1 T2) | 2016 code (C1 `MAIN.py`) | PyPHS rhodes.net (C2) | Unit |
|---|---|---|---|---|---|
| M_h | hammer mass | 3×10⁻² | `mh = 30e-3` | `Mhammer = 3e-2` | kg |
| L_h | felt thickness at rest | 15×10⁻³ | `lh = 1.5e-2` | `L = 1e-2` | m |
| B_h | felt exponent | 2.5 | `beta = 2.5` | `B = 2.5` | – |
| F_h | elastic characteristic force | 13.8 | (uses `kh = 5e5` N/m^2.5) | `F = 1000` | N |
| A_h | felt damping coefficient | 0.184 | `alphah = 0.184` | `A = 1000` | N·s/m |
| K (=L_h^−B F_h) | power-law stiffness | 5×10⁵ | `kh = 5e5` | – | N·m^−2.5 |
| R (=L_h^{1−B} A_h) | power-law damping | 100 | – | – | N·s·m^−2.5 |
| D_h / wh | contact width | – | `wh = 1.5e-2` | `w1 = 0.015` | m |
| z_h | strike position | – | `zh = wh + 0.1·(L−2wh)` → 17.54 mm for A4 (my computation) | `z1 = 0.2` (relative) | m |
| q_h0 | initial hammer position | – | `qh0 = −0.2` | `−tinit·v`, `tinit = 2e-2 s` | m |
| f_ext^core | driving force | 0…10³ N for 1 ms (§6); 500 N in Fig. 7/10; 100…1000 N in Fig. 11 | `Fin = fin·1300`, fin ∈ linspace(0.3,0.9,8) → 390…1170 N, applied for `sqrt(0.15·mh/Fin)` = 3.4…1.96 ms starting at t = 10 ms | initial velocity 1…10 m/s (`list_v_hammer`) | N |
| exhaust | force cut | `f_ext = 0 if q_h > −0.5 cm` | `qhmax = −0.05 − qh0` | – | m |

My derived figure: the code's force pulses imply a hammer speed at release of `√(Fin·0.15/mh)` ≈ 44–76 m/s, and the paper's 500 N × 1 ms gives about 17 m/s. Both are physically unrealistic (real Rhodes hammers move at a few m/s). Treat the force amplitude as an abstract velocity knob. PyPHS's 1–10 m/s range is more physical.

### Tine / beam (S1 Table 4, A4)
| Symbol | Meaning | Value | Unit | Provenance |
|---|---|---|---|---|
| ρ_steel | density | 7750 | kg/m³ | S1 T4, code `m` |
| E_steel | Young's modulus | 180×10⁹ | N/m² | S1 T4, code `E` |
| R_b | tine radius | 10⁻³ | m | S1 T4, code `r` (PyPHS netlist: 2e-3) |
| A_b | damping coefficient | 5×10⁻² (constant over modes) | N·s/m² (paper writes N·s⁻¹) | S1 T4 |
| F_b | tuning frequency | 440 | Hz | S1 T4 |
| M_b | mass per length = πR_b²ρ | 0.024347 | kg/m | derived (my computation) |
| I_b | πR_b⁴/4 | 7.854×10⁻¹³ | m⁴ | derived |
| K_b | E·I_b | 0.14137 | N·m² | derived |
| L_b | length | 5.54×10⁻² (my computation: 55.36 mm) | m | S1 T4 |
| κ_m L_b | roots of cos·cosh = −1 | 1.87510, 4.69409, 7.85476, 10.99554, 14.13717, 17.27876 | – | derived |
| ν_m/ν_1 | mode ratios | 1, 6.2669, 17.5475, 34.3861, 56.8426, 84.9130 | – | derived |
| ν_1..4 (A4) | modal frequencies | 440, ≈2757.49, ≈7721.07, ≈15130.22 | Hz | S1 §6 (my recomputation: 440, 2757.4, 7720.9, 15129.9) |
| M | number of modes, A4 @ 48 kHz | 4 | – | S1 §6 |
| ψ_m(L_b) | tip mode shape | ±2/√L_b = ∓8.500 (sign alternates) | m^−½ | derived (code formula `Psi`) |
| Ω_m (A4, code geometry) | contact projection | −0.02001, −0.06820, −0.08012, −0.02863 | m^½ | derived from the code formula with zh = 17.54 mm, wh = 15 mm |
| σ_m (paper) | decay rate A_b/(2M_b) | 1.027 s⁻¹ for all modes → T60 ≈ 6.7 s | s⁻¹ | derived |
| alphab_m (code) | modal damping `alpha_b0·κ_m⁴/κ_1⁴`, `alpha_b0 = 4.5^F0·1e-2` = 0.045 for A4 | σ = 0.924, 36.3, 284.6, 1092.7 s⁻¹ → T60 = 7.47 s, 0.19 s, 24 ms, 6.3 ms | – | C1 `MAIN.py` ~258, 365; σ/T60 derived |
| PyPHS damping | `A·10^linspace(0,D,N)`, A = 2e-2, D = 2, N = 4, R = 2e-3 | σ = 0.103, 0.477, 2.21, 10.3 s⁻¹ (T60 67 s, 14.5 s, 3.1 s, 0.67 s) | – | C2 `_cantilever.py`/`rhodes.net`; σ derived |
| nkmax | max number of modes in code | 20 | – | C1 |

### Pickup (S1 Table 6, plus code and PyPHS)
| Symbol | Meaning | Paper (S1 T6) | 2016 code (C1) | PyPHS (C2) | Unit |
|---|---|---|---|---|---|
| B_p | magnet field | 4π×10⁻⁷ (as printed) | `h0 = 1` (normalised) | `H0 = 1` | T |
| U_0 | μ₀ | 4π×10⁻⁷ | `mu0 = 1` (normalised) | – | H/m |
| U_steel | μ_steel | 5×10⁻³ | – | – | H/m |
| U_rel | μ_steel/μ₀ | ≈3979 (derived) | `murel = 700` | `dmu = 1` | – |
| C_coil | magnetic capacitance | 3.07×10⁻⁵ | `Lc/N² = 3.07×10⁻⁷` (`Lc = 1/(Cp(2π·5000)²)` = 3.07 mH) | `Ccoil = 330e-7` (netlist); default 3e-5 | H |
| R_p | coil radius | 5×10⁻³ | `ap = 1e-3` | `Rp = 5e-3` | m |
| a_b | sphere (tine) radius | = R_b = 1e-3 | `r = 1e-3` | `Rb = 2e-3` | m |
| L_hor | coil–tine distance | 10⁻² | `lp = (1/F0)·1e-3` → 1.0 mm for A4 | `Lh = 1e-2` | m |
| L_ver | offset from axis | 10⁻³ | `dlp = −(2^(1/F0^0.7))·1e-4` → −0.2 mm for A4 | `Lv = 0.5e-3` | m |
| N_coil | turns | 100 | `Nturns = 100` | `Ncoil = 100` | – |
| R_RC | load resistance | 10³ | `R = 1000` | `Rrc = 1e3` | Ω |
| C_RC | load capacitance | 33×10⁻⁸ (= 330 nF) | `Cp = 330e-9` | `Crc = 33e-8` | F |
| f_RLC | coil+C resonance | – | `fRLC = 5000` | – | Hz |
| RC corner | 1/(2πRC) | 482 Hz (derived) | – | – | Hz |
| pickup sweet spot (website) | l_p (distance) | – | – | – | 0.5 mm "too close", **1.5 mm "ideal"**, 3 mm "low volume" (S2) |
| | l_δ (axis offset) | – | – | – | 0 mm "pure overtone", **0.5 mm "ideal"**, 1.5 mm "pure tone" (S2) |

**The geometry sets have very different nonlinearity (my evaluation of the bracket `g(q)` in eq. 25, normalised to |g(0)|, for q from −2 to +2 mm in 0.5 mm steps):**
- Paper T6 (`Lhor` = 10 mm, `Lver` = 1 mm, `Rp` = 5 mm): 1, 0.51, 0, −0.51, −1, −1.48, −1.93, −2.34, −2.71. This is almost linear, so it would give little "bark".
- Code A4 (`Lhor` = 1 mm, `Lver` = −0.2 mm, `Rp` = 1 mm): −0.004, 1.55, 4.81, 4.29, 1.00, −1.57, −4.87, −4.21, −1.07. This is strongly non-monotonic (the classic Rhodes waveshaper).

The sound examples use code-like geometry. The paper itself notes that "the tuning of physical parameters may differ from the parameters specified in the paper" (S2/S3).

### Per-key data
The paper only gives values for A4. The 2016 code has **per-key scaling laws in the variable `F0 = f0/440`** (`MAIN.py` lines ~251–291). The shipped loop runs only F0 = 1, so it is unconfirmed whether these laws produced the A1–A3 web audio. The table below is computed from the code formulas (mode counts and lengths from my modal calculation):

| Note | f0 (Hz) | F0 | L_b (mm) | M @44.1k | M @48k | modal freqs < 22.05 kHz (Hz) | alpha_b0 | lp = L_hor (mm) | dlp = L_ver (mm) | Fin scale (×fin) |
|---|---|---|---|---|---|---|---|---|---|---|
| A1 | 55 | 0.125 | 156.58 | 12 | 12 | 55, 344.7, 965.1, 1891.2, 3126.3, 4670.2, 6522.9, 8684.3, 11154.5, 13933.5, 17021.2, 20417.7 | 0.01207 | 8.0 | −2.0 | 640.4 |
| A2 | 110 | 0.25 | 110.72 | 8 | 9 | 110, 689.4, 1930.2, 3782.5, 6252.7, 9340.4, 13045.7, 17368.6 | 0.01456 | 4.0 | −0.6 | 804.3 |
| A3 | 220 | 0.5 | 78.29 | 6 | 6 | 220, 1378.7, 3860.4, 7564.9, 12505.4, 18680.9 | 0.02121 | 2.0 | −0.3 | 1018.3 |
| A4 | 440 | 1 | 55.36 | 4 | 4 | 440, 2757.4, 7720.9, 15129.9 | 0.045 | 1.0 | −0.2 | 1300 |
| A5 | 880 | 2 | 39.14 | 3 | 3 | 880, 5514.9, 15441.8 | (law) | – | – | – |
| A6 | 1760 | 4 | 27.68 | 2 | 2 | 1760, 11029.7 | – | – | – | – |

Caveat: the model makes tine length scale as 1/√f with a fixed 1 mm radius. That is not a real Rhodes tine set, where the tuning spring makes a large difference, so these lengths are a model artefact. The mode ratios (1 : 6.27 : 17.5 : …) are those of a bare cantilever and ignore the tuning spring mass.

## Discretization / algorithm

- **Scheme:** discrete gradient (Itoh–Abe type, per-component), which is the midpoint/trapezoidal rule on the quadratic parts. It is first-order accurate overall and second order when J and R are constant (S1 §5).
- **Sample rate:** 48 kHz (S1 §6; C1 `fs = 48000.`; C2 `fs: 48e3`).
- **State size:** `nx = 2M + 4`: 2 hammer, 2M beam, 2 pickup/RC (code: `q_C`, `phi_L`). For A4 that is 12. For A1 at 44.1 kHz it would be 28 (my computation). Dissipative variables `nw = M + 2`.
- **Nonlinear solve:** the paper says "a fixed number of Newton–Raphson iterations", and with one nonlinear storage (felt) "only requires the inversion of a scalar function". In the code the NR unknowns are **2** (`dq_h` and the felt damping velocity `w_h`), with a symbolic 2×2 Jacobian inverse. `pypHs.simulation` defaults are **`nbit_NR = 100` max iterations, tolerance `1e-12`** (C1 `pypHs.py` l.796, 891). The PyPHS rhodes example uses `maxit = 10`, `eps = 1e-16`. The NR runs every sample, even though `H_h2` and `r_h` are identically 0 when `q_h ≤ 0` (no contact).
- **Linear part:** the code precomputes `Dx = (fs·I − Ã₂Q/2)⁻¹` symbolically ("presolve") and evaluates dense matrix–vector products each sample (`Fl`). The pickup gain `f_p(q,q̇)` sits in G, so it is a state-dependent input coefficient and not part of the inverted matrix. A C++ exporter exists (`utils/phs2cpp.py`) and the paper mentions "a C++ code from symbolic calculation", but **no timings or operation counts are given anywhere**.
- **Operation count (ESTIMATE, mine, not from the sources):**
  - *Generic pyPHS form:* dense (2M+4)² linear update ≈ 144 MAC (A4) to ≈ 784 MAC (A1 at 12 modes), plus NR iterations, each needing `q^{1.5}` and `q^{2.5}` (pow) and a 2×2 solve. Several hundred to over a thousand flops per sample per voice, in double precision.
  - *Structure-exploiting form:* outside contact, the modes are decoupled 2×2 blocks, so the trapezoidal update costs about 4–6 MAC per mode. Tip reconstruction costs 2M MAC, the pickup nonlinearity is about 10 ops (rational function or LUT), and the RLC is about 5 MAC. That totals roughly 30–100 ops per sample per voice. During contact (≈1–3 ms ≈ 50–150 samples per strike) add the felt NR plus the coupling `Ω r_h Ωᵀ`, which adds a rank-1 coupling across all modes.
- **Frequency warping (derived, mine):** the midpoint/trapezoidal rule maps a mode at f to `(fs/π)·atan(πf/fs)`. At 48 kHz the A4 modes 2757/7721/15130 Hz land at about 2728/7149/11925 Hz. At 44.1 kHz they land at 2723/7059/11551 Hz. The paper does not prewarp, so its high modes are noticeably flat. Mode 3 at 48 kHz is about 7.4 % (≈ 1.3 semitones) low.

## Measured / reference behaviour

- **Reference data:** UVI recordings (company "specialised in sample-based synthesizers") of **A4 at 8 increasing hammer forces** (S1 §6.4, Fig. 11–12). The files ship as `REF/REF1..REF8.wav` (48 kHz/16-bit/mono, 240 000 samples = 5 s each) plus the concatenations `REF.wav` and `allsigs.wav`. The licence of the recordings is not stated.
- **Comparison (S1 Fig. 11):** spectrogram over 100 dB dynamics plus normalised waveforms for "force 1, 4, 7" (simulation forces 100…1000 N). The authors call it "rough"/qualitative. **Measured tones have extra content in 1–2 kHz**, which they attribute to tone-bar coupling or double polarisation. They also say the model "could benefit from an eigenmode dependent damping coefficient" to fit partial decays, which the code then does. Low-frequency content in the recordings is external noise.
- **Simulation behaviour (S1 Fig. 7–10):** with F = 500 N the hammer accelerates between 1 and 2 ms and hits at t_i ≈ 2.5 ms. Part of the energy is dissipated in the felt. The numerical energy balance error sits near machine epsilon. Pickup source power averages about 10⁻⁴ W and is locally negative. The higher beam modes are "not extensively excited", so **"the distinctive evolution of the tone is due to the pickup only"**.
- **Pickup positioning (S1 Fig. 13; S2 audio):** the timbre depends strongly on `L_hor` and `L_ver`. With the tine on the coil axis (l_δ = 0) the output is "pure overtone", meaning frequency doubling from the even-symmetric g. A large offset gives a "pure tone". The ideal is about 0.5 mm offset and 1.5 mm distance.
- **Audio examples (S2, not downloaded):** `sounds/rhodes_test_{55,110,220,440}.mp3/.ogg` (hammer hits of increasing force), `sounds/lp_{0.0005,0.0015,0.003}.mp3` and `sounds/dlp_0.mp3`, `dlp0.0005.mp3`, `dlp0.0015.mp3`, relative to `http://recherche.ircam.fr/anasyn/falaize/`. Figures: `images/rhodes/ALLspectrum100.png`, `test1/4/7.png`, `lh.png`, `dlh.png`.
- No objective metrics are reported (no decay times, spectral distances or listening tests).

## FM-1 implementation notes

**Verdict: the full PHS/discrete-gradient solver is not feasible or worthwhile on the AC791N at 8 voices.** The model's structure maps well onto a cheap fixed-point design, though, because the only strong nonlinearity at audio rate is a memoryless function of the tip position.

1. **Why the full PHS approach is a poor fit**
   - Every sample needs an implicit NR solve with fractional powers (`c^{1.5}`, `c^{2.5}`) and divided differences `(H(x+δ)−H(x))/δ`. As δ→0 this is a 0/0 form that needs a tolerance switch, and in fixed point it means a division per iteration plus catastrophic cancellation.
   - The dense (2M+4)-dimensional linear update is wasteful because the modes are decoupled outside contact.
   - The passivity guarantee (energy balance to machine epsilon) **does not survive quantization**. Rounding in Q-format breaks the exact discrete chain rule, so the main selling point is lost anyway. Stability in fixed point has to come from pole radius < 1 and rounding toward zero, not from the discrete gradient.

2. **What to keep** (from cheapest and most valuable to least)
   - **Pickup nonlinearity as a LUT:** `v_pick = g(q_tip)·q̇_tip`, with `g(q) = (f₁−2L_hor²)/f₁² − (f₂−2L_hor²)/f₂²` (eq. 25), or a per-key/per-voicing table from the host. An alternative is to tabulate the antiderivative `Φ(q)` and output `Φ(q_n) − Φ(q_{n−1})`. That is exact for `d/dt Φ(q)`, needs no separate velocity, and is mildly band-limiting (ESTIMATE suggestion). A 256–1024-entry Q15 table with linear interpolation over q ∈ [−q_max, q_max] costs about 6 cycles. `L_hor` and `L_ver` become the "voicing" controls (S2 audio shows they set bark vs. bell). Q-format concern: g has a large dynamic range (|g(0)| ≈ 2×10⁵ m⁻² for code geometry vs 2.8×10³ for paper geometry), so normalise on the host and keep a per-key scale factor.
   - **Modal tine:** M decoupled 2-pole resonators driven by the contact force through the weights `Ω_m`, with the tip read through `ψ_m(L_b) = ±2/√L_b`. Use exact pole placement (impulse-invariant `r = e^{−σ/fs}` and `θ = 2πf/fs`) instead of the paper's trapezoidal rule, to avoid the 7–25 % warping of the upper modes. Mode count: the "all modes < Nyquist" rule gives 12 modes for A1, but the upper modes decay in tens of ms (code damping law) and are "not extensively excited". Capping at 3–4 modes per voice is probably enough (ESTIMATE). Coefficients `2r·cosθ` and `−r²` in Q30 (or Q2.29). With r very close to 1 (σ ≈ 0.1–1 s⁻¹ → 1−r ≈ 2–20×10⁻⁶), Q15 is far too coarse. Use a 32-bit state with Q30 coefficients and a 32×32→64 multiply, keeping the high word. 64-bit multiply is allowed and no division is needed.
   - **Hammer:** contact lasts only about 1–3 ms (50–150 samples) per strike. Options:
     (a) A simplified explicit contact: `F = K·max(q_h,0)^{2.5}` from a LUT, plus hysteretic damping, integrated with semi-implicit Euler at fs or 2×fs over the contact window only. NR is not needed if the step is small (ESTIMATE; stability must be checked for stiff felts).
     (b) Precompute on the host the contact force pulse `F(t; v_hammer)` for a grid of velocities and play it into the resonators. That has zero runtime nonlinearity and is the cheapest choice. Its cost is ignoring the hammer–tine re-interaction, which is small because the tine is light compared with the 30 g hammer (ESTIMATE).
     With either option, map velocity to hammer speed, not to the code's abstract `Fin`.
   - **RC/RLC load:** one biquad (2-pole lowpass/resonance at about 5 kHz in the code; RC corner 482 Hz in the paper). This is essentially a fixed tone filter that can be merged with any later EQ.

3. **Cost (ESTIMATE):** 4 modes × ~5 MAC, plus tip reconstruction 8 MAC, LUT ~8 ops, and biquad 5 MAC, gives about 45–60 ops per sample per voice outside contact. That is ≈ 0.5 M ops/s per voice, or ≈ 4 M ops/s for 8 voices. It should fit comfortably within a 2.9 ms per 256-frame budget (I have not confirmed the AC791N clock; if it is ≥ 160 MHz this is under 10 % load). Per-block parameter updates (damper, voicing) are negligible.

4. **Q-format plan (ESTIMATE):**
   - Resonator states are int32 Q1.30 normalised to the max tip displacement, about 1–2 mm. The code's 1 mm gap implies a tip of ≲ 1 mm before contact with the pickup.
   - Coefficients are Q2.29 or Q1.30, with 64-bit products shifted down.
   - Tip velocity: either difference successive tip positions (scale ∝ fs) or use the antiderivative LUT form.
   - The pickup LUT index is a Q15 position, clamped to the table range so that a large tip excursion cannot overflow.
   - Output is Q15 after the RLC biquad.
   - All per-key tables are computed on the host: `f_m`, `σ_m`, `Ω_m`, `ψ_m(L)`, the g/Φ LUT and gain normalisation.

5. **Risks**
   - **Parameter provenance is weak.** The paper, the 2016 code and PyPHS disagree on felt constants, damping laws, pickup geometry, C_coil and tine radius. Only A4 is documented, the per-key laws in the code are ad hoc, and none of the sets is fitted to measurements. Expect to tune by ear and against reference recordings.
   - **The missing tone bar** is the authors' own top-ranked omission and affects attack and sustain (and probably the 1–2 kHz content). One cheap remedy is a second coupled resonator per key (ESTIMATE).
   - **No damper model:** we must add release damping (for example, raise σ_m on key-up). This is not from this source.
   - Mode ratios of a bare cantilever (6.27×) will differ from real Rhodes tines with tuning springs. Per-key measured partials would be better.
   - LUT aliasing: `g(q)·q̇` creates high harmonics when the geometry is strongly nonlinear. Consider 2× oversampling of the pickup stage only, or the antiderivative form with a gentle post-lowpass (ESTIMATE).
   - Fixed-point limit cycles or denormal-like stalls in very lightly damped resonators: use rounding with a small deadband, or let the voice end once its envelope falls below a threshold.

## Gaps & open questions

- The published JSV version was not read. Table values or typos (for example `B_p` = 4π×10⁻⁷ T, `H_p` = ½xᵀdiag(C_coil, C_RC)x, `C_coil` = 3.07×10⁻⁵ vs the code's 3.07×10⁻⁷) may have been corrected there.
- The exact eq. (22) flux expression is partly garbled in the PDF text extraction. Eq. (25), the one that matters for the output, is consistent with the code.
- The code's per-key laws (`alpha_b0`, `lp`, `dlp`, `Fin`) are present, but it is unconfirmed whether they produced the A1–A3 audio.
- No CPU timing or real-time factor is reported. "Real-time applications" is asserted, not measured.
- The licence of the UVI reference WAVs is unknown. Do not redistribute them.
- Units of the code's pickup output are normalised (`mu0 = h0 = 1`), so absolute output voltage is not meaningful. Normalise per key.
- Hammer drive values (hundreds of N, 44–76 m/s implied) are unphysical. A velocity-to-force mapping has to be designed.
- Hammer strike position: the code uses ~10 % of the free length from the clamp side (`zh` = 17.5 mm) while PyPHS uses relative 0.2. The paper gives no value.
- Not modeled at all: tone bar, tuning spring, damper, polarisation, Maxwell back-force, preamp, tremolo, cabinet, mechanical noises.

## Machine-readable

```json
{
  "source": {
    "id": "03-falaize-phs",
    "title": "Passive simulation of the nonlinear port-Hamiltonian modeling of a Rhodes Piano",
    "authors": ["Antoine Falaize", "Thomas Hélie"],
    "year": 2017,
    "venue": "Journal of Sound and Vibration 390:289-309 (preprint HAL hal-01390534v1, 2016)",
    "doi": "10.1016/j.jsv.2016.11.008",
    "urls": {
      "hal_preprint": "https://hal.science/hal-01390534/",
      "pdf": "https://hal.science/hal-01390534v1/file/JSV_Rhodes_manuscript_round_2.pdf",
      "hal_published_record": "https://hal.science/hal-01470949/",
      "companion_ircam": "http://recherche.ircam.fr/anasyn/falaize/fr/applis/rhodes/",
      "companion_blog": "https://afalaize.github.io/posts/rhodes/",
      "code_2016_zip": "http://recherche.ircam.fr/anasyn/falaize/codes/code_rhodes_falaize.zip",
      "pyphs_repo": "https://github.com/pyphs/pyphs",
      "pyphs_rhodes_example": "https://github.com/pyphs/pyphs/tree/master/pyphs/examples/rhodes"
    },
    "licence": {"paper_preprint": "HAL Authorization (no CC)", "code": "CeCILL-B", "reference_wavs": null},
    "local_copy": "docs/model/research/sources/03-falaize-phs/",
    "fetched_ok": {"hal_pdf": true, "ircam_page": true, "blog": true, "code_zip": true, "pyphs_files": true, "published_jsv_pdf": false, "audio_examples": false}
  },
  "blocks": {
    "hammer": {"modeled": true, "model": "core mass + nonlinear hysteretic felt f=F_h*c^B_h + (A_h L_h/B_h) c^(B_h-1) dq/dt, c=max(q,0)/L_h", "provenance": "S1 eq.9-15"},
    "tine": {"modeled": true, "model": "linear damped Euler-Bernoulli cantilever, analytic modes, M modes below Nyquist", "provenance": "S1 eq.16-20, App.A"},
    "tuning_spring": {"modeled": false, "note": "tuning by tine length (A4)"},
    "tonebar": {"modeled": false, "note": "assumption A2; authors' top-priority future work"},
    "damper": {"modeled": false},
    "pickup": {"modeled": true, "model": "dphi/dt = g(q_tip)*dq_tip/dt, g from McDonald magnetised-sphere model; no back-action", "provenance": "S1 eq.24-27"},
    "preamp_amp": {"modeled": "partial", "model": "passive RC load (paper) / RLC at 5 kHz (2016 code)"},
    "tremolo": {"modeled": false},
    "cabinet": {"modeled": false},
    "noises": {"modeled": false},
    "discretization": {"scheme": "discrete gradient (midpoint for quadratic parts)", "fs_hz": 48000, "nonlinear_solver": "Newton-Raphson on 2 unknowns (dq_h, w_h)", "nr_max_iter_code2016": 100, "nr_tol_code2016": 1e-12, "nr_max_iter_pyphs_example": 10, "state_size": "2M+4", "ops_per_sample_reported": null, "ops_per_sample_estimate_generic": "several hundred to >1000 flops (ESTIMATE)", "ops_per_sample_estimate_modal_fixedpoint": "45-60 (ESTIMATE)"}
  },
  "params": {
    "hammer": {
      "paper": {"M_h_kg": 0.03, "L_h_m": 0.015, "B_h": 2.5, "F_h_N": 13.8, "A_h_Nsm": 0.184, "K_Nm-2.5": 5e5, "R_Nsm-2.5": 100},
      "code2016": {"mh_kg": 0.03, "lh_m": 0.015, "beta": 2.5, "kh_Nm-2.5": 5e5, "alphah": 0.184, "wh_m": 0.015, "relative_zh": 0.1, "qh0_m": -0.2, "Fin_N": "fin*1300^(F0^0.05), fin in linspace(0.3,0.9,8)", "force_start_s": 0.01, "force_duration_s": "sqrt(0.15*mh/Fin)"},
      "pyphs": {"Mhammer_kg": 0.03, "L_m": 0.01, "F_N": 1000, "A_Nsm": 1000, "B": 2.5, "z1_rel": 0.2, "w1_m": 0.015, "v_hammer_mps": [1, 10], "tinit_s": 0.02},
      "exhaust": "f_ext=0 if q_h > -0.5 cm (S1 §6)"
    },
    "tine": {
      "rho_kgm3": 7750, "E_Pa": 1.8e11, "R_b_m": 0.001, "A_b_paper": 0.05, "F_b_Hz": 440, "L_b_m": 0.0554,
      "M_b_kgm_derived": 0.024347, "K_b_Nm2_derived": 0.14137,
      "kappaL_roots": [1.87510, 4.69409, 7.85476, 10.99554, 14.13717, 17.27876],
      "mode_ratios": [1, 6.2669, 17.5475, 34.3861, 56.8426, 84.9130],
      "A4_modal_freqs_hz_paper": [440, 2757.49, 7721.07, 15130.22],
      "A4_Omega_code_geometry_derived": [-0.02001, -0.06820, -0.08012, -0.02863],
      "psi_tip_abs": "2/sqrt(L_b)",
      "damping_code2016": "alphab_m = 4.5^F0*1e-2 * (kappa_m/kappa_1)^4",
      "A4_sigma_code2016_derived_per_s": [0.924, 36.3, 284.6, 1092.7],
      "A4_sigma_paper_derived_per_s": 1.027,
      "damping_pyphs": "A*10^linspace(0,D,N), A=0.02, D=2, N=4, R=0.002",
      "nkmax_code": 20
    },
    "pickup": {
      "paper": {"B_p_T": 1.2566e-6, "U0_Hm": 1.2566e-6, "U_steel_Hm": 0.005, "C_coil_H": 3.07e-5, "R_p_m": 0.005, "L_hor_m": 0.01, "L_ver_m": 0.001, "N_coil": 100, "R_RC_ohm": 1000, "C_RC_F": 3.3e-7},
      "code2016": {"mu0": 1, "h0": 1, "murel": 700, "ap_m": 0.001, "r_m": 0.001, "lp_m": "(1/F0)*1e-3", "dlp_m": "-(2^(1/F0^0.7))*1e-4", "Nturns": 100, "R_ohm": 1000, "Cp_F": 3.3e-7, "fRLC_Hz": 5000, "Lc_H_derived": 0.00307},
      "pyphs": {"Ccoil": 3.3e-5, "Ncoil": 100, "Rb_m": 0.002, "Rp_m": 0.005, "H0": 1, "Lh_m": 0.01, "Lv_m": 0.0005, "dmu": 1},
      "website_sweet_spot": {"l_p_m": 0.0015, "l_delta_m": 0.0005},
      "g_function": "g(q)=(f1-2Lh^2)/f1^2-(f2-2Lh^2)/f2^2, f1=(q-Rp+Lv)^2+Lh^2, f2=(q+Rp+Lv)^2+Lh^2; dphi/dt ∝ g(q)*dq/dt"
    },
    "sim": {"fs_hz": 48000, "duration_s": 5}
  },
  "per_key": [
    {"note": "A1", "f0_hz": 55, "F0": 0.125, "L_b_m_derived": 0.15658, "M_44k1": 12, "M_48k": 12, "freqs_hz_derived": [55, 344.7, 965.1, 1891.2, 3126.3, 4670.2, 6522.9, 8684.3, 11154.5, 13933.5, 17021.2, 20417.7], "alpha_b0_code": 0.01207, "lp_m_code": 0.008, "dlp_m_code": -0.0020, "Fin_scale_code": 640.4, "provenance": "code2016 laws (unconfirmed use) + derived modal calc"},
    {"note": "A2", "f0_hz": 110, "F0": 0.25, "L_b_m_derived": 0.11072, "M_44k1": 8, "M_48k": 9, "freqs_hz_derived": [110, 689.4, 1930.2, 3782.5, 6252.7, 9340.4, 13045.7, 17368.6], "alpha_b0_code": 0.01456, "lp_m_code": 0.004, "dlp_m_code": -0.0006, "Fin_scale_code": 804.3, "provenance": "code2016 laws (unconfirmed use) + derived"},
    {"note": "A3", "f0_hz": 220, "F0": 0.5, "L_b_m_derived": 0.07829, "M_44k1": 6, "M_48k": 6, "freqs_hz_derived": [220, 1378.7, 3860.4, 7564.9, 12505.4, 18680.9], "alpha_b0_code": 0.02121, "lp_m_code": 0.002, "dlp_m_code": -0.0003, "Fin_scale_code": 1018.3, "provenance": "code2016 laws (unconfirmed use) + derived"},
    {"note": "A4", "f0_hz": 440, "F0": 1, "L_b_m_derived": 0.05536, "M_44k1": 4, "M_48k": 4, "freqs_hz_derived": [440, 2757.4, 7720.9, 15129.9], "alpha_b0_code": 0.045, "lp_m_code": 0.001, "dlp_m_code": -0.0002, "Fin_scale_code": 1300, "provenance": "paper Table 4 + §6, code2016"}
  ]
}
```
