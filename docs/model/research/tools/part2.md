
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
