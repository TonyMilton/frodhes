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
