# Empirical references: jRhodes3d, EP-MK1, Rhodes facts

Research agent 5. These are practical, empirical references rather than academic papers. Every number below carries its provenance. Paths starting `sources/` are relative to `docs/model/research/sources/05-empirical-jrhodes-epmk1/`, where the downloaded text files live (no audio was downloaded). Values I computed or estimated myself are marked **DERIVED** (computed from cited numbers with a stated formula) or **ESTIMATE** (my judgement).

## Source

| # | URL | Title | Author | Date | Licence |
|---|-----|-------|--------|------|---------|
| S1 | https://github.com/sfzinstruments/jlearman.jRhodes3d | jlearman.jRhodes3d: "1977 Rhodes Mark I Stage 73, full-length samples, FLAC format" | Jeff Learman | samples recorded "around 2006" (README); repo current as of 2026-10 | Samples: CC BY-NC 4.0. Everything else (sfz, docs): CC0 (`sources/jlearman.jRhodes3d/LICENSE`). Note that the sfz headers say "CC-SA-BY" (`jRhodes3d-mono.sfz:3`), which conflicts with LICENSE; LICENSE governs. |
| S1h | (derived from S1) `sources/jlearman.jRhodes3d/flac-streaminfo-mono.txt` | FLAC STREAMINFO headers of all 65 mono samples, read with HTTP `Range: bytes=0-63` (headers only) | this agent | 2026-10-15 | n/a |
| S2 | https://mikemorenoaudio.wordpress.com/2019/01/10/ep-mk1-physical-modeled-electric-piano-vst/ | EP-MK1 // Physical Modeled Electric Piano VST | Mike (Miguel) Moreno | 2019-01-10 (updated 2019-01-29) | none stated on the post. Text copy: `sources/web/epmk1-post.txt`; patch screenshots: `sources/web/post-*.png` |
| S3 | https://patchstorage.com/ep-mk1/ | EP-MK1 (Patchstorage entry, rev 2.3) | mikemorenodsp | 2019 to 2020 (v2.3 zip dated 2020-01) | "BSD 3-Clause" according to Patchstorage. GUI image: `sources/web/EP-MK1-GUI-1.png` |
| S4 | https://github.com/MikeMorenoDSP/EP-MK1 (redirected from MikeMorenoAudio/EP-MK1) | EP-MK1 source: Pd patches, Camomile param list, tutorial PDF, EP-MK2 WIP | Miguel Moreno | created 2019-01-29, last push 2022-11-14 | **GPL-3.0** (`sources/MikeMorenoDSP.EP-MK1/License.txt`). This conflicts with S3's BSD-3 label. Treat it as GPL: we take ideas only, no code. |
| S4d | `sources/MikeMorenoDSP.EP-MK1/tutorial/EP-MK1-Documentation.pdf` | EP-MK1 Documentation (6 pp.) | Miguel Moreno | ~2019 | GPL-3.0 (repo) |
| W1 | https://www.fenderrhodes.com/org/manual/ch4.html | Rhodes Service Manual, Ch. 4 (action: escapement, hammer tips, strike line) | Rhodes / fenderrhodes.com | 1970s manual, web copy | unspecified |
| W2 | https://fenderrhodes.com/service/hammer-tips.html | Steve's Corner: Hammer tips | Steve Espinola (fenderrhodes.com) | n.d. | unspecified |
| W3 | https://www.fenderrhodes.com/service/tine-settings.html | Steve's Corner: Tine settings | fenderrhodes.com | n.d. | unspecified |
| W4 | https://www.fenderrhodes.com/history/effects.html | Rhodes effects history (Vibrato) | fenderrhodes.com | n.d. | unspecified |
| W5 | https://www.fenderrhodes.com/service/amp-diffs.html | Steve's Corner: Amplifier differences (Jordan / Peterson / Haigler) | fenderrhodes.com | n.d. | unspecified |
| W6 | https://soundgirls.org/the-fender-rhodes/ | The Fender Rhodes (article quoting the Rhodes Service Manual and others) | SoundGirls.org | n.d. | unspecified |
| W7 | https://www.soundonsound.com/reviews/scarbee-rsp-73 | Scarbee RSP 73 review ("E1 to E7") | Sound On Sound | n.d. | unspecified |
| W8 | https://www.kvraudio.com/forum/viewtopic.php?p=2035781 | KVR forum "Free Rhodes - Version 2" (posts by learjeff, the jRhodes author, and by toddyjoe) | forum | ~2006 | unspecified |
| W9 | https://en.wikipedia.org/wiki/Rhodes_piano | Rhodes piano | Wikipedia | 2026 | CC BY-SA |
| W10 | https://www.vintagevibe.com/blogs/news/how-tone-bar-clips-improve-sustain-on-rhodes-pianos | Tone bar clips and treble sustain | Vintage Vibe | n.d. | vendor page |
| W11 | https://www.fenderrhodes.com/org/manual/ch7.html | Rhodes Service Manual, Ch. 7 (tone source: tines) | Rhodes | n.d. | unspecified |
| W12 | https://sfzformat.com/opcodes/amp_veltrack/ and https://sfzformat.com/opcodes/xf_velcurve/ | SFZ opcode reference (needed to read the sfz velocity behaviour) | sfzformat.com | n.d. | unspecified |

## Summary

- **jRhodes3d (S1)** is a sampled **1977 Rhodes Mark I Stage 73**, bought new in 1978 and recorded "around 2006" **directly from the harp connector**. It was recorded **with EQ** ("treble boost and low-mid scoop, emphasizing the bell tones, and with substantial bark on the higher velocity layers") and has been **denoised** (README §Sampling Details). There are 15 sampled notes, F1 to C7, roughly every 4th white key, with **3 to 5 velocity layers** spaced to "peak at 3 dB difference per layer on the low notes". Every sample is mono, 44.1 kHz, 16-bit and unlooped, between **1.4 s (C7) and 25.0 s (A2)** long (S1h). The set contains **no release, key-up, damper or pedal noise samples**. Release is a plain `ampeg_release` of **0.5 / 0.4 / 0.3 / 0.2 s from bass to treble**. Tremolo is an sfz sine LFO on volume: 0 to 6 dB depth, 0.1 to 10 Hz, default 5 Hz, plus delay and fade. The author notes that "Rhodes low notes go a bit sharp when struck harder" (`package/info.yml`).
- **EP-MK1 (S2 to S4)** is a tiny "physical-ish" modal model: a **half-sine hammer pulse one fundamental period long** excites a **tone-bar resonator** (an RBJ constant-skirt band-pass at f0 with Q of about 1000) and **two tine resonators** at 7·f0 and 20·f0 behind a 2 kHz HPF. The sum goes through a **pickup waveshaper**: LPF, gain, Padé tanh, then an exponential asymmetry `(2^(s·y)-1)/2^s`, a "buzz" term y^4, and a HPF at f0. Note-off switches the tone-bar Q to a low "release" value (10) and **fires a second, quieter hammer pulse (−36 dB) as a damper thump**. A global tremolo multiplies the summed output. Its 28 user parameters are a good guide to what players want to control.
- In the shipped v2.3 code the **velocity curve is exponential in velocity (linear in dB)**: `g = 2^(-5·(1-(v-1)/126))`, which spans −30.1 dB to 0 dB. The blog version used `-4` (−24 dB). Velocity drives the **excitation**, not the output gain, so the pickup nonlinearity turns loudness into bark.
- **Hardware facts**: the 73-key range is E1 to E7, with fundamentals of about 41 Hz to 2.6 kHz (W6, W7). Hammer tips come in 5 hardness bands from 30 Shore up to wrapped maple (W1, W2). Tine-to-pickup horizontal gap is 1/32" in the midrange and 1/16" for the bass and wood-tip treble (W3). The Suitcase "Vibrato" was a square-wave tremolo that became stereo panning in 1969 (W4). **I found no published Hz range for the Peterson vibrato rate or depth, and no published per-register T60.**
- **For the FM-1**: EP-MK1's topology costs roughly 6 biquads, 1 LUT nonlinearity and a few multiplies per voice. That is a credible 8-voice integer budget, provided the very-high-Q resonators use Q31 coefficients with 64-bit accumulation. Mechanical noises can be synthesized almost for free (hammer pulse to output, note-off pulse to resonator). jRhodes provides calibration targets for decay length, release time per register and velocity-layer spacing.

## Model architecture

### EP-MK1 (v2.3 plugin, `sources/MikeMorenoDSP.EP-MK1/EP-MK1-Plugins/EP-MK1-Linux64/EP-MK1/EP-MK1.pd`, canvas `voice` at lines 519 to ~1430, plus the top-level canvas)

Signal flow per voice, reconstructed object by object from the patch. The tutorial PDF S4d describes the same four layers.

```
note-on(v,f) ─► [amp reset: line~ to 0 in 1 ms; after 2 ms jump to 1]   (voice obj 26-30, lines 697-698)
            └─► after 2 ms: clear all filter states, fire hammer         (obj 6,7,60,62,112)
HAMMER  h(t) = gv · cos(2π·(0.75 + 0.5·r(t))),  r: 1→0 linearly over T=1000/f ms   (obj 8,41,9,37,36,35,34; lines 810-811, 941)
        = half-sine lobe, length = one fundamental period, peak gv
        gv = 2^(-5·(1-(v-1)/126))                                       (obj 57,58,12,13,14,93,15,16; line 1396)
  ├─► TONE BAR: BPF_rbj(f, Q=ToneBarDecay[1000]) ← input h + noteoff_pulse   (obj 114→5)
  │      → ×0.707946 (−3 dB, line 812) = tb
  ├─► TINE: HPF2(TineHPF[2000 Hz], Q=0.404061) → ×ampReset → BPF(f·R1[7], Q=TineDecay[500]) + BPF(f·R2[20], same Q) = tn
  ├─► direct out: h · HammerLevel[−30 dB]                                (obj 85→71)
  └─► PICKUP input: h · PickupAttack[+3 dB]                              (obj 95→94)
PICKUP  x = LPF2(PickupLPF[1000 Hz], Q=0.404061)(tb + h·Atk) · PickupGain[15 dB] + tn · TineSend[−21 dB]
        y  = tanh_pade(x)                       y = x(27+x²)/(27+9x²), x clipped to ±3 (hv.tanh)
        y2 = (2^(s·y) − 1) / 2^s,  s = Symmetry[15 dB → 5.62]           (obj 17-25)
        p  = HPF2(f0, Q=0.404061)( y2·PickupLevel[−6 dB] + BuzzSign·BuzzLevel[−9 dB]·y2^4 )   (obj 102-105,108,31)
VOICE OUT = p + h·HamLvl + tb·ToneBarLevel[−6 dB] + tn·TineLevel[−30 dB], × ampReset   (obj 111,116,59,56)
note-off (pedal up): tone-bar Q ← ToneBarRelease[10]; fire second half-sine pulse ×NoteoffLevel[−36 dB] into tone bar (obj 47-52, 75, 69)
pedal up with notes held: Q ← Release (no thump)                         (obj 78-83, 89)
voice DSP is switched off when env~ reports silence                      (obj 117-124, lines 1420-1427)
GLOBAL  sum(32 voices)/2 · (1 − on·depth·lfo) · master → tanh_pade → L=R  (top canvas, lines 150-168)
        lfo = (1−shape)·(0.5 − 0.5·cos(2π·φ²)) + shape·2·min(φ, 1−φ),  φ = phasor(rate)
```

Notes on what the patch shows:
- The RBJ "constant skirt" BPF is `b0 = sin(w0)/2, b1 = 0, b2 = −b0, a0 = 1+α, a1 = −2cos w0, a2 = 1−α, α = sin w0/(2Q)`. It is quoted in the patch comments of `b.resonator~` (`sources/MikeMorenoDSP.EP-MK1/tutorial/b.resonator~.pd`). Peak gain equals Q, which is why the hammer amplitude is so small.
- "Decay" on the GUI **is literally the Q**, so decay time scales as 1/f. That reproduces "less decay on higher frequencies… just like a Rhodes" (S2 §1) only qualitatively; see the calibration section below.
- The tremolo "sine" is `0.5−0.5cos(2πφ²)`, because the phasor goes through `pow~ 2` (line 168). That is a warped, non-symmetric sine. It is probably unintended, but it is in the code. "Triangle" is `2·min(φ,1−φ)`.
- Tuning: `f = BaseFreq · Interval^((note − BaseNote)/Divisions)`, default 440·2^((n−69)/12), and Scala-like scale files are supported (top canvas, `sources/MikeMorenoDSP.EP-MK1/scales/`).
- Polyphony: `poly 32 1` (32 voices with voice stealing, line 517).
- Blog v1 (S2, `sources/web/post-18.41.46.png`) differs from v2.3 in four ways. Its hammer is a linear ramp 1→0 over T, mixed with an equal-length white-noise pulse (`noise~ → wrap~` × pulse, `/2`) and then a velocity-controlled `lop~`. Its velocity exponent is `-4` (−24 dB). It uses Q 1500. Its pickup is `*15 → −3.25 offset → lop~ 150 → tanh` with parallel branches `hip~ 250 ×0.25` and `pow~ 10 × −0.08 → hip~ 50` (`sources/web/post-18.42.30.png`). The velocity-LPF cutoff reads as `mtof(20 + 100·x)` with x derived from velocity. **ESTIMATE**: the wiring is not fully legible, but if x=(v−1)/126 the cutoff runs from about 26 Hz to 8.4 kHz.
- EP-MK2 (`sources/MikeMorenoDSP.EP-MK1/EP-MK2/`) is an unfinished rewrite: 8 cloned voices and exponential sliders such as decay = 2^(8·s/127+4), giving 16 to 4096 (Q units). It adds no new technique.

### jRhodes3d sampling structure (S1)

- 15 root notes (MIDI 29, 35, 40, 45, 50, 55, 59, 62, 65, 71, 76, 81, 86, 91, 96), each stretched over 3 to 15 keys. The main sfz maps A0 to C8 (`jRhodes3d-mono.sfz:82-96`). The per-folder sfz maps C1 to F7 (`jRhodes3d-mono/_jRhodes3d-mono-flac.sfz:19-33`).
- Velocity: 5 groups. File suffix `_5` is the **softest** and `_1` the **loudest** (`jRhodes3d-mono.sfz:81-82` maps lovel=1 to `_5`). Notes above F4 have fewer real layers, and missing layers reuse their neighbours (see the table below).
- There are 3 render variants: mono; "st" (2-cent mid-side pitch-shift doubling baked into the samples); "sv" (stereo vibrato baked per note). Each comes with and without velocity crossfade (README; `jRhodes3d-keyswitch.sfz:10-16`).
- Mapping onto Rhodes parts:

| Rhodes part | EP-MK1 block | jRhodes3d |
|---|---|---|
| Hammer (tip hardness, velocity) | half-sine pulse, length 1/f0, amp `gv(v)`; direct hammer leak to output (−30 dB) and into pickup (+3 dB) | velocity layers (3 to 5) baked into the recordings |
| Tine (bell partials) | 2 BPFs at 7·f0 and 20·f0, Q 500, fed through a 2 kHz HPF | baked in, emphasised by the recording EQ ("treble boost") |
| Tone bar (fundamental, long sustain) | BPF at f0, Q 1000 | baked in; unlooped full length (1.4 to 25 s) |
| Pickup (asymmetric nonlinearity, bark) | LPF2 → tanh → exp-asymmetry → y^4 buzz → HPF@f0 | baked in ("substantial bark on the higher velocity layers") |
| Damper | tone-bar Q → 10 at note-off, plus a −36 dB note-off pulse | `ampeg_release` 0.5 to 0.2 s by register; **no damper-noise sample** |
| Sustain pedal | holds note-off; pedal-up applies release Q | `ampeg_releasecc64=100` with half-pedal curve 11 |
| Tremolo / Suitcase vibrato | global AM, sine/triangle morph, rate, depth in dB | sfz LFO on volume (mono file), auto-pan LFO, or "sv" samples with per-note baked vibrato |
| Amp / preamp | output tanh soft clip | recording-chain EQ (treble boost, low-mid scoop); no amp model |
| Mechanical noises | hammer leak (key-down), note-off pulse (damper) | **none** (noise removed with CoolEdit 96) |

## Equations

1. **EP-MK1 v2.3 velocity → hammer gain** (`EP-MK1.pd:1396`, voice objects 57→58→12→13→14→93→15→16):
   `gv(v) = 2^(−5·(1 − (v−1)/126))`, v = 1..127. That gives gv(1) = 2^−5 = 0.03125 (−30.10 dB), gv(64) = 2^−2.5 = 0.177 (−15.05 dB) and gv(127) = 1 (0 dB), i.e. **0.2389 dB per velocity step**.
   Blog v1 (S2, `sources/web/epmk1-post.txt:36`): `2^((1−((v−1)/126))·−4)`, giving −24.08 dB to 0 dB.
2. **Hammer pulse** (S4d p.1; `EP-MK1.pd:810-811, 941`): `h(t) = gv·cos(2π(0.75 + 0.5·(1 − t/T)))` for 0 ≤ t ≤ T, and 0 afterwards, with T = 1/f0. This equals `gv·sin(π t/T)`: a positive half-sine one fundamental period long.
3. **Resonator** (RBJ BPF, constant skirt; `tutorial/b.resonator~.pd` comments): `H(z) = (b0 − b0 z^−2)/(1 + a1 z^−1 + a2 z^−2)` with b0 = sin w0/(2(1+α)), a1 = −2cos w0/(1+α), a2 = (1−α)/(1+α), α = sin w0/(2Q), w0 = 2πf/fs.
   **DERIVED**: pole radius ≈ 1 − α ≈ 1 − πf/(Q·fs), so τ = Q/(πf) and **T60 = 3·ln(10)·Q/(π f) ≈ 2.199·Q/f** (seconds).
4. **Pickup** (`EP-MK1.pd` voice objects 17-25, 39-40, 66, 77, 94, 99-105, 108, 31):
   `x = LPF2_{fc=PickupLPF, Q=0.404}(tb + Atk·h)·G + Send·tn`
   `y = x(27+x²)/(27+9x²)` with x clipped to [−3, 3] (Padé tanh, `tutorial/hv.tanh.pd`)
   `y2 = (2^{s·y} − 1)/2^{s}` with s = 10^{Sym_dB/20}. This maps y ∈ [−1, 1] onto [(2^{−s}−1)/2^s, (1−2^{−s})], an exponential and therefore asymmetric curve that generates even harmonics.
   `p = HPF2_{fc=f0, Q=0.404}(Lvl·y2 + ±Buzz·y2^4)`
5. **Tremolo** (top canvas, `EP-MK1.pd:150-168`): `out = Σvoices/2 · (1 − On·10^{Depth_dB/20}·lfo(φ))`, with `lfo = (1−k)(0.5−0.5cos 2πφ²) + k·2min(φ,1−φ)`, k = Shape/127. Defaults: Depth −9 dB gives 0.355, so the gain swings between 1.0 and 0.645 (a 3.8 dB dip). Rate is 3 Hz.
6. **jRhodes3d amplitude vs velocity** (sfz default, W12): `amp_veltrack=100` (not overridden in any jRhodes sfz) gives `Gain(v) = 20·log10((v/127)²) dB = 40·log10(v/127)`. The per-layer sample levels sit on top of that: "peak at 3 dB difference per layer on the low notes" (README). Velocity crossfades use the default `xf_velcurve=power` (equal-power). **DERIVED** (low notes, no-xfade file): `L(v) ≈ 40·log10(v/127) − 3·(5 − layer(v))` dB, with layer(v) = 5 for v ≤ 47, 4 for 48-72, 3 for 73-95, 2 for 96-111 and 1 for v ≥ 112, where 1 is the loudest file (`jRhodes3d-mono-no-xfade.sfz` group lines; see the diff in Parameters). The result spans about −96 dB at v=1 to 0 dB at v=127. On real players the bottom of that range is never reached.
7. **jRhodes3d tremolo** (`jRhodes3d-mono.sfz:57-69`): sine LFO on volume, `depth_dB = 6·CC1/127`, `rate = 0.1 + 9.9·CC92/127` Hz, `delay = 2·CC93/127` s, `fade = 2·CC94/127` s. Defaults (`set_hdcc`): depth 0, rate 0.1+9.9·0.5 = 5.05 Hz, delay 0.5 s, fade 0.5 s.
8. **Half-pedal curve** (`jRhodes3d-mono.sfz:43-50`, curve 11, applied to `ampeg_releasecc64=100`, i.e. up to +100 s release): CC64 → factor {0:0, 32:0, 42:0.1, 54:0.3, 62:0.4, 64:1, 127:1}, interpolated linearly.

## Parameters

### jRhodes3d velocity layers (`jRhodes3d-mono.sfz:81-149`, `jRhodes3d-mono-no-xfade.sfz` same lines)

| Group (file suffix) | Dynamic | xfade version: lovel–hivel | xfin (vel) | xfout (vel) | no-xfade version: lovel–hivel |
|---|---|---|---|---|---|
| G1 (`_5`) | softest | 1–60 | none | 25→60 | 1–47 |
| G2 (`_4`) | | 25–84 | 25→60 | 61→84 | 48–72 |
| G3 (`_3`) | | 61–103 | 61→84 | 85→103 | 73–95 |
| G4 (`_2`) | | 85–119 | 85→103 | 104→119 | 96–111 |
| G5 (`_1`) | loudest | 104–127 | 104→119 | none | 112–127 |

Layer spacing: "sampled to peak at 3 dB difference per layer on the low notes and to maintain volume throughout each layer" (README). Layers that actually exist (S1 tree listing, S1h):

| Root | Real layer files | Substitutions in sfz |
|---|---|---|
| F1, B1, E2, A2, D3, G3, B3, D4, F4 | `_1` to `_5` | none |
| B4, E5 | `_1`, `_2`, `_4`, `_5` | G3 uses `_4` (`:125-126`) |
| A5, D6, G6, C7 | `_2`, `_4`, `_5` | G3 uses `_4`, G5 uses `_2` (`:127-130`, `:161-164`) |

Totals: 65 files per variant (S1 tree). The README says 67, a minor inconsistency.

### jRhodes3d key map, release, sample length (`jRhodes3d-mono.sfz:82-96`; lengths from S1h)

| Root (MIDI) | Key range (main sfz) | ampeg_release (s) | Length `_5` soft (s) | Length `_1`/`_2` loud (s) |
|---|---|---|---|---|
| F1 (29) | A0–Ab1 (21–32) | 0.5 | 18.6 | 16.8 (`_1`) |
| B1 (35) | A1–Db2 (33–37) | 0.5 | 23.0 | 19.2 |
| E2 (40) | D2–Gb2 (38–42) | 0.5 | 24.6 | 15.0 |
| A2 (45) | G2–B2 (43–47) | 0.4 | 25.0 | 19.6 |
| D3 (50) | C3–E3 (48–52) | 0.4 | 20.6 | 14.6 |
| G3 (55) | F3–A3 (53–57) | 0.4 | 20.4 | 16.2 |
| B3 (59) | Bb3–C4 (58–60) | 0.4 | 17.6 | 13.0 |
| D4 (62) | Db4–Eb4 (61–63) | 0.3 | 17.8 | 14.0 |
| F4 (65) | E4–Ab4 (64–68) | 0.3 | 15.0 | 12.4 |
| B4 (71) | A4–Db5 (69–73) | 0.3 | 12.8 | 9.2 |
| E5 (76) | D5–Gb5 (74–78) | 0.3 | 5.2 | 5.4 |
| A5 (81) | G5–B5 (79–83) | 0.3 | 8.4 | 6.6 (`_2`) |
| D6 (86) | C6–E6 (84–88) | 0.2 | 7.2 | 6.4 (`_2`) |
| G6 (91) | F6–A6 (89–93) | 0.2 | 3.6 | 3.0 (`_2`) |
| C7 (96) | Bb6–C8 (94–108) | 0.2 | 1.4 | 1.4 (`_2`) |

All files are 44100 Hz, mono, 16-bit (S1h). The per-folder sfz uses C1–F7 as the outer limits and adds `ampeg_release=0.3` at group level, overridden per region (`_jRhodes3d-mono-flac.sfz:18-33`). Lengths are "until trimmed after denoising", **not** T60: treat them as an upper bound on audible decay at about −60 to −70 dB below peak (**ESTIMATE**). Tuning: no `tune`/`transpose` opcodes, i.e. the samples are as recorded.

### jRhodes3d controls (`jRhodes3d-mono.yml`, `jRhodes3d-mono.sfz:8-79`)

| Control | CC | Range | Default |
|---|---|---|---|
| Tremolo Amp | 1 | 0–6 dB | 0 |
| Tremolo Freq | 92 | 0.1–10 Hz | 5.0 (yml) / 5.05 (sfz) |
| Tremolo Delay | 93 | 0–2 s | 0.5 |
| Tremolo Fade | 94 | 0–2 s | 0.5 |
| AutoPan Depth | 95 | 0–100 % | 0 |
| AutoPan Freq | 96 | 0.1–10 Hz | 2.5 (yml) / 2.575 (sfz) |
| Stereo width (st/sv files) | 1 | `width_oncc1=100`, curve 99 | set_hdcc1 = 0.5 |
| Sustain | 64 | half-pedal curve 11, release +100 s | none |
| Master volume | none | `volume=6` dB | none |
| Keyswitch | G7/Ab7/A7/Bb7/B7/C8 | variant select | G7 |

### EP-MK1 user-facing parameters (S4 `EP-MK1.txt:7-35`; GUI groups from `sources/web/EP-MK1-GUI-1.png`)

| Group | Parameter | Unit | Range | Default (v2.3 txt) | GUI v1 default (if different) |
|---|---|---|---|---|---|
| Output | Master Level | dB | −100..0 | 0 | |
| Tuning | Base Frequency | Hz | 100..20000 | 440 | |
| Tuning | Base MIDI Note | | 0..127 | 69 | |
| Tuning | # of Divisions | | 1..100 | 12 | |
| Tuning | Interval to Divide | | 0..30 | 2 | |
| Tine | Tine Ratio 1 | ×f0 | 0..30 | 7 | |
| Tine | Tine Ratio 2 | ×f0 | 0..30 | 20 | |
| Tine | Tine HPF | Hz | 20..20000 | 2000 | |
| Tine | Tine Decay | Q | 1..2000 | 500 | |
| Tine | Tine Level | dB | −100..0 | −30 | |
| Tine | Tine Pick Send | dB | −100..0 | −21 | |
| Tone Bar | Tone Bar Decay | Q | 1..2000 | 1000 | |
| Tone Bar | Sustain Pedal | 0/1 | | 0 (CC64 ≥ 127 → 1) | |
| Tone Bar | Tone Bar Release | Q | 1..2000 | 10 | |
| Tone Bar | Noteoff Level | dB | −100..0 | −36 | −24 |
| Tone Bar | Tone Bar Level | dB | −100..0 | −6 | |
| Tone Bar | Hammer Level | dB | −100..0 | −30 | |
| Pickup | Pickup Gain | dB | 0..30 | 15 | |
| Pickup | Pickup Attack | dB | −100..30 | 3 | 0 |
| Pickup | Pickup LPF | Hz | 20..20000 | 1000 | 500 |
| Pickup | Pickup Symmetry | dB | 0..30 | 15 | |
| Pickup | Pickup Level | dB | −100..0 | −6 | |
| Pickup | Buzz Phase | 0/1 (→ ±1) | | 1 | |
| Pickup | Buzz Level | dB | −100..0 | −9 | |
| Tremolo | On/Off | 0/1 | | 1 | |
| Tremolo | Shape (sine↔tri) | | 0..127 | 0 (sine) | |
| Tremolo | Rate | Hz | 0..20000 | 3 | |
| Tremolo | Depth | dB | −100..0 | −9 | |

Fixed internals: filter Q 0.404061 for all HPF/LPF; tone-bar trim −3 dB (0.707946); retrigger fade 1 ms and trigger delay 2 ms; 32 voices; output Padé tanh.

### Rhodes hardware facts (web, concise)

| Fact | Value | Source |
|---|---|---|
| 73-key range | E1–E7 ("six octaves", middle C = C4) | W7; Horniman/Audiofanzine listings, via search |
| 73-key fundamentals | "41 Hz to 2.6 kHz" (Rhodes Service Manual, quoted) | W6 |
| 88-key range | A0–C8 | general knowledge, **not verified** against a Rhodes document (Gap) |
| Mark I / Mark II | Mark I Stage/Suitcase 1970; Mk II late 1979 ("simply a set of cosmetic changes"); 54-key added with Mk II | W9 |
| Hammer tips: felt → neoprene | 1970–71 | W2, W9 |
| Hammer tips by register (manual, 88-position numbering) | tips 1–30: 30 duro, 1/4"; 31–40: 50 duro, 5/16"; 41–50: 70 duro, 3/8"; 51–64: 90 duro, 7/16"; 65–88: wrapped wood (extra hard), 7/16" | W1 |
| Hammer tips (Steve's Corner numbering) | keys 00–23: 30 Shore; 24–33: 50; 34–43: 70; 44–57: 90; 58–81: maple + 3 layers shrink tube. Colours: black / red / yellow / black | W2 |
| Escapement | ideal 1/32"; extreme bass 1/4"–3/8"; extreme treble 1/32"–3/32" | W1 |
| Strike line | about 2-1/4" (bass) to about 1/8" (treble) from the tone-generator leading edge | W1 |
| Damper clearance | 3/8"–1/2" | W1 |
| Tine stock | 0.075" piano wire (original) | W11 |
| Tine-to-pickup horizontal gap | 1/32" mid-range; 1/16" bass; 1/16" wood-tip (top) notes; "mostly fundamental" voicing covered the first 15 notes | W3 |
| Pickup voicing effect | "Off-axis settings produce a rounded, mellower tone"; "on-axis alignment sounds more mid-range with less low-end"; tine closer to the pickup axis means "the fundamental and odd harmonics decrease, causing the second harmonics to rise"; closer pickup gives more output | W6 |
| Bark (from the jRhodes author) | "Moving pickups closer causes more bark for reasons other than just a stronger signal… waveforms… more 'distorted' looking for hard strikes when the pickups are closer"; "bark (like the tine bell tone) is emphasized if you filter out the fundamental"; early Mark I has "more bell-like tine tone" | W8 (learjeff = Jeff Learman) |
| Close pickup = "bell" | "Putting the two close together gives a characteristic 'bell' sound" | W9 |
| Metallic register | "a metallic timbre is generated when playing keys one octave above the C-5 and up" (Wadhams, quoted) | W6 |
| E3 spectrum | partials 2–5 present; fundamental loudest (−15.4 dB on a TLM 103) | W6 |
| Suitcase Vibrato | first mono tremolo, "square-wave pattern"; became L↔R panning when the Suitcase amps went stereo in 1969; Speed + Intensity controls; meant to simulate a rotary speaker | W4 |
| Suitcase amps | Jordan 50 W (1966–69, mono vibrato); Peterson 80 W (stereo, concentric Treble/Bass and Intensity/Speed); Haigler 100 W (stereo, switch + Speed/Intensity knobs) | W5 |
| Peterson 80 W | two 40 W solid-state amps (germanium); four 12" 32 Ω Eminence speakers, pairs front/back; ping-pong panning | W6 |
| Peterson vibrato rate/depth (Hz, dB) | **not found** in any source checked | Gap |
| Decay per register | **no published measurements found**. Treble sustain is the known weak spot: tone-bar clips are used on about notes 54–73 to lengthen it | W10 |

## Discretization / algorithm

- **EP-MK1**: everything runs in Pd at the host rate. The resonators are biquads (Direct Form I via Pd `biquad~`) with RBJ coefficients computed in control rate at note-on. The pulse is a sample-accurate `vline~`. Filter states are cleared explicitly at retrigger, after the 1 ms fade-out, for click-free and repeatable attacks (S2 §2; S4d §5). Voices stop DSP via `switch~` when `env~` reaches 0. A constant Q gives T60 ∝ 1/f automatically, with no per-key table needed.
- **jRhodes3d**: plain sample playback with pitch-shift across 3 to 15 keys per root (C7 is stretched up to C8, +12 semitones), velocity crossfades (equal power) or hard switches, and an sfz AHDSR release.
- **Numerical issue relevant to the FM-1 (DERIVED)**: tone-bar pole radius `r ≈ 1 − πf/(Q·fs)`. With E1, Q=1000 and fs=44100, 1−r ≈ 2.9·10⁻⁶. That needs a coefficient resolution of at least 2⁻²¹ to keep T60 within about 10 %, so Q15 is impossible and **Q30/Q31 coefficients with a 64-bit accumulator are required** for the tone-bar resonator. The tine resonators (7f, 20f, Q 500) have 1−r ≈ 4·10⁻⁵ to 10⁻³: Q24+ is fine. The −3 dB/Q 0.404 HPF/LPF are benign in Q15/Q23.
- Constant-skirt BPF peak gain = Q (1000), so the input must be scaled down by about 60 dB. **Alternative (ESTIMATE, better for fixed point)**: implement each mode as a normalised 2-pole oscillator `y[n] = 2r·cos(w)·y[n−1] − r²·y[n−2]`, with the hammer injected as `x·(1−r)` or simply as the initial state. This removes the Q-sized gain and the b0/b2 multiplies (3 multiplies per sample per mode).

## Measured / reference behaviour

Calibration targets for our model:

1. **Decay length vs register (S1h)**. These are lengths of denoised unlooped samples, used as a proxy for an audible decay of about 60 dB or more (**ESTIMATE**). They are roughly flat at **15–25 s from F1 to D4**, then drop: F4 15 s, B4 ~10–13 s, E5 ~5.3 s, A5/D6 ~7 s, G6 ~3.3 s, C7 1.4 s.
   Compare EP-MK1's constant Q=1000 (**DERIVED**, T60 = 2.2·Q/f): E1 53 s, A2 20 s, A4 5.0 s, E5 3.3 s, C7 1.05 s, E7 0.83 s. So **constant Q makes the bass about 2.5× too long and the mid (A4–F4) about 2× too short relative to jRhodes**. Recommendation: use a **per-key T60 table**, not a constant Q. Initial target (**ESTIMATE** from S1h): T60 ≈ 18 s for MIDI ≤ 62, falling log-linearly to about 12 s at 71, about 6 s at 81 and about 1.5 s at 96.
2. **Release (damper) times** (`jRhodes3d-mono.sfz:82-96`): 0.5 s (A0–Gb2), 0.4 s (G2–C4), 0.3 s (Db4–B5), 0.2 s (C6–C8). EP-MK1's release Q=10 gives T60 = 22/f: 0.53 s at E1 but only 0.05 s at A4 and 0.01 s at C7. That is **much shorter than jRhodes in the treble**. Adopt the jRhodes values as release-T60 targets per register. Real damper felt is also less effective on the top notes (**ESTIMATE**, common knowledge).
3. **Velocity dynamic range**. jRhodes: about 3 dB of sample-level step per layer (bass), 4 steps, so **about 12 dB of timbre-carrying level range** across the layers. On top of that sits the sfz `40·log10(v/127)` scaling. EP-MK1: 30 dB of excitation range, linear in dB. Bark should appear only in the top 2 layers (v ≳ 96 in the no-xfade map): "substantial bark on the higher velocity layers" (README).
4. **Pitch vs velocity**: "the Rhodes low notes go a bit sharp when struck harder" (`package/info.yml`). This is a target for a small velocity-dependent pitch offset or downward glide in the bass. The magnitude is not given (Gap).
5. **Tremolo**: the original Suitcase used a **square-ish** waveform, as AM (pre-1969) or as L/R panning (stereo, 1969+) (W4). Plugin defaults for rate are 3 Hz (EP-MK1) and 5 Hz (jRhodes); depth defaults are −9 dB, i.e. a 3.8 dB dip (EP-MK1), and up to 6 dB (jRhodes).
6. **Timbre by register**: "metallic" above about C5 (W6); per-register hammer-tip hardness rises toward the treble (W1/W2), i.e. shorter contact and brighter excitation. In EP-MK1 this happens implicitly because the pulse length is 1/f0.
7. **Even-harmonic content** depends on the tine/pickup alignment: on-axis gives more 2nd harmonic and less fundamental (W6). EP-MK1's "Symmetry" (exponential asymmetry) is the control for this.

## FM-1 implementation notes

**Cost sketch per voice (ESTIMATE)**: 1 tone-bar mode (Q31, 64-bit MAC), 2 tine modes, 1 pickup LPF, 1 HPF. The tine HPF can be dropped by computing the tine excitation as a short precomputed click instead. The pickup curve is a single 1-D LUT of 256 to 1024 entries with linear interpolation, covering `tanh → exp-asym` combined; this avoids the Padé division and `pow`, and the y^4 buzz is two multiplies. The hammer is a precomputed half-sine table resampled per key, or a per-key 17–1070-sample pulse. That comes to about 25–35 multiply-accumulates per sample per voice, i.e. **8 voices × 44100 × ~35 ≈ 12 M MAC/s**. The pickup must stay **per voice**, not on the mix: the real pickup is per tine, and a shared nonlinearity would intermodulate chords. Use EP-MK1's trick of skipping silent voices (env below threshold), and clear state only on (re)trigger, after a 1 ms fade (≈ 44 samples).

**Panel mapping proposal** (7 encoders, plus FX/ENV/LFO/EDIT pages; ESTIMATE, based on EP-MK1's parameter set):

| Page | ENC_KNOB1 | ENC_KNOB2 | ENC_KNOB3 | ENC_KNOB4 |
|---|---|---|---|---|
| Main (no button) | **Bark/Drive** (pickup gain G, 0–30 dB) | **Bell** (tine level + send) | **Decay** (scales the per-key T60 table, ×0.25..×2) | **Tone** (pickup LPF, 300 Hz–8 kHz) |
| ENV | **Hammer** (velocity sensitivity: dB range 12–36, default 30) | **Release** (damper T60 scale) | **Damper thump** (note-off pulse level, −60..−20 dB) | **Key-down thump** (hammer-to-output level) |
| LFO | **Trem rate** (0.5–10 Hz) | **Trem depth** (0–100 %, AM) | **Shape** (sine↔square; square = Suitcase) | **Mode** (mono AM / stereo pan "Suitcase") |
| EDIT | **Voicing/Symmetry** (asymmetry s, 0–30 dB) | **Tine ratio** (7 / preset alternatives) | **Buzz** (y^4 level, sign) | **Velocity curve** select (see below) |
| FX | output drive (amp tanh) | bass EQ | treble EQ | chorus/stereo width |

ENC_ALGORITHM selects the voicing presets as "models": Mark I bell (low G, high tine), Mark I bark (high G, high s), Suitcase (pan tremolo on), Dyno-ish (strong tine, tone up). ENC_PRESETS browses user presets. ENC_SELECT moves the parameter focus or edits the value of the highlighted item. All knob values map to precomputed integer tables (T60 → coefficient per key per scale step, generated on the host).

**Noises: cheap options**
- Key-down hammer "thump": free. Add the hammer pulse directly to the output at about −30 dB (EP-MK1's Hammer Level).
- Damper (key-up) thump: free. At note-off, inject a second half-sine at about −36 dB into the tone-bar mode while switching its decay to the release value (EP-MK1).
- Key-release click or felt noise: jRhodes has **no** noise samples. **ESTIMATE**: a 5–20 ms burst of LPF'd noise from an LFSR (a 16-bit LFSR and one 1-pole LPF, near-zero cost), or a ≤ 2 kB 8-bit sample shared by all keys.
- Pedal-up/down noise: optional, same LFSR burst at lower cutoff. Low priority.

**Velocity curve to adopt (ESTIMATE, recommendation)**: drive the **excitation amplitude** with EP-MK1's linear-in-dB law, `gv = 2^(−R/6.0206·(1 − (v−1)/126))` with a user range R of 12–36 dB (default **30 dB**, i.e. the v2.3 code's `-5` exponent). Store it as a 128-entry Q15 table per R setting, generated on the host. Let the pickup nonlinearity create bark at high v, rather than crossfading timbres as jRhodes does. Calibrate so that the onset of visible pickup clipping corresponds to v of about 96 (jRhodes' top two layers). Optionally add a small post-gain to match jRhodes' perceived level spacing of about 3 dB per 24 velocity steps in the bass (**DERIVED**: 12 dB over the layer centres 24…120).

## Gaps & open questions

- **Peterson/Suitcase vibrato rate range (Hz) and depth**: not found in W4, W5, W6, jsisynth.com/peterson.html or diystompboxes. A schematic analysis or a measurement is needed. Plugins use 0.1–10 Hz (jRhodes) and 3 Hz default (EP-MK1).
- **Per-register T60 of a real Rhodes**: not published in the sources checked. The S1h sample lengths are only a proxy (denoised, trimmed, EQ'd, unknown threshold). Measuring the decay envelope of the jRhodes FLACs (CC BY-NC, fine for analysis) would give real T60 and two-stage decay values. That requires downloading the audio, which was out of scope here.
- **Absolute dB per layer in the treble**: the README only states 3 dB per layer "on the low notes".
- **Magnitude of the velocity-dependent sharpening in the bass** (info.yml): unknown.
- **88-key range A0–C8** is not verified against a Rhodes document. The hammer-tip numbering in W1 (1–88) and W2 (00–81) is inconsistent and its mapping onto the 73-key E1–E7 range is ambiguous.
- **Vertical tine/pickup offset values** (the parameter that sets bark) are not given numerically anywhere (W3 gives horizontal only). This needs to come from the papers covered by the other agents.
- **EP-MK1 licence conflict** (GPL-3.0 in the repo vs BSD-3 on Patchstorage) and **jRhodes sfz licence string conflict** (CC-SA-BY in the sfz header vs CC0 in LICENSE).
- **EP-MK1 tremolo "sine"** uses φ², which looks like a bug. Do not copy it.
- **Recording chain EQ** of jRhodes (treble boost, low-mid scoop) has no stated frequencies or gains, so the samples are not a neutral spectral target.

## Machine-readable

```json
{
  "source": {
    "agent": 5,
    "items": [
      {"id": "S1", "url": "https://github.com/sfzinstruments/jlearman.jRhodes3d", "title": "jlearman.jRhodes3d", "author": "Jeff Learman", "date": "recorded ~2006", "licence": "samples CC BY-NC 4.0; sfz/docs CC0"},
      {"id": "S2", "url": "https://mikemorenoaudio.wordpress.com/2019/01/10/ep-mk1-physical-modeled-electric-piano-vst/", "title": "EP-MK1 // Physical Modeled Electric Piano VST", "author": "Mike (Miguel) Moreno", "date": "2019-01-10", "licence": null},
      {"id": "S3", "url": "https://patchstorage.com/ep-mk1/", "title": "EP-MK1 rev 2.3", "author": "mikemorenodsp", "date": "2020-01", "licence": "BSD-3-Clause (per Patchstorage)"},
      {"id": "S4", "url": "https://github.com/MikeMorenoDSP/EP-MK1", "title": "EP-MK1 source", "author": "Miguel Moreno", "date": "2019-01-29..2022-11-14", "licence": "GPL-3.0"},
      {"id": "W1", "url": "https://www.fenderrhodes.com/org/manual/ch4.html"},
      {"id": "W2", "url": "https://fenderrhodes.com/service/hammer-tips.html"},
      {"id": "W3", "url": "https://www.fenderrhodes.com/service/tine-settings.html"},
      {"id": "W4", "url": "https://www.fenderrhodes.com/history/effects.html"},
      {"id": "W5", "url": "https://www.fenderrhodes.com/service/amp-diffs.html"},
      {"id": "W6", "url": "https://soundgirls.org/the-fender-rhodes/"},
      {"id": "W7", "url": "https://www.soundonsound.com/reviews/scarbee-rsp-73"},
      {"id": "W8", "url": "https://www.kvraudio.com/forum/viewtopic.php?p=2035781"},
      {"id": "W9", "url": "https://en.wikipedia.org/wiki/Rhodes_piano"},
      {"id": "W10", "url": "https://www.vintagevibe.com/blogs/news/how-tone-bar-clips-improve-sustain-on-rhodes-pianos"},
      {"id": "W11", "url": "https://www.fenderrhodes.com/org/manual/ch7.html"},
      {"id": "W12", "url": "https://sfzformat.com/opcodes/amp_veltrack/"}
    ]
  },
  "blocks": {
    "epmk1": {
      "hammer": {"type": "half_sine_pulse", "length": "1/f0", "gain_law": "2^(-5*(1-(v-1)/126))", "gain_db_range": [-30.1, 0], "blog_v1_law": "2^(-4*(1-(v-1)/126))", "direct_out_db": -30, "into_pickup_db": 3, "src": "EP-MK1.pd:1396,810-811,941"},
      "tone_bar": {"type": "rbj_bpf_constant_skirt", "freq": "f0", "Q": 1000, "trim_db": -3, "level_db": -6, "release_Q": 10, "t60_formula_s": "2.199*Q/f0"},
      "tine": {"type": "2x rbj_bpf", "ratios": [7, 20], "Q": 500, "pre_hpf_hz": 2000, "pre_hpf_Q": 0.404061, "level_db": -30, "send_to_pickup_db": -21},
      "pickup": {"pre_lpf_hz": 1000, "pre_lpf_Q": 0.404061, "gain_db": 15, "sat": "x(27+x^2)/(27+9x^2), |x|<=3", "asym": "(2^(s*y)-1)/2^s", "symmetry_db": 15, "buzz": "sign*level*y2^4", "buzz_db": -9, "level_db": -6, "post_hpf": "f0, Q 0.404061"},
      "damper": {"noteoff_Q": 10, "noteoff_pulse_db": -36, "pedal": "holds noteoff; pedal-up sets release Q without pulse"},
      "tremolo": {"type": "global AM", "gain": "1 - depth*lfo", "lfo": "(1-k)*(0.5-0.5cos(2pi*phi^2)) + k*2*min(phi,1-phi)", "rate_hz_default": 3, "depth_db_default": -9, "stereo": false},
      "retrigger": {"fade_ms": 1, "trigger_delay_ms": 2, "clear_filter_state": true},
      "output": {"voice_sum_scale": 0.5, "soft_clip": "pade tanh"},
      "polyphony": 32
    },
    "jrhodes3d": {
      "instrument": "1977 Rhodes Mark I Stage 73 (bought new 1978)",
      "recording": {"source": "harp connector direct", "eq": "treble boost + low-mid scoop", "denoised": true, "rate_hz": 44100, "bits": 16, "channels": 1, "looped": false},
      "velocity_layers": 5,
      "layer_step_db_low_notes": 3,
      "amp_veltrack_db": "40*log10(v/127)",
      "xfade_curve": "power",
      "noises": null,
      "tremolo": {"type": "sfz lfo volume sine", "depth_db_max": 6, "rate_hz": [0.1, 10], "rate_default_hz": 5.05, "delay_s": [0, 2], "fade_s": [0, 2]},
      "autopan": {"depth_pct": [0, 100], "rate_hz": [0.1, 10], "rate_default_hz": 2.575},
      "sustain": {"ampeg_releasecc64_s": 100, "half_pedal_curve": {"0": 0, "32": 0, "42": 0.1, "54": 0.3, "62": 0.4, "64": 1, "127": 1}},
      "pitch_note": "low notes go a bit sharp when struck harder"
    }
  },
  "params": {
    "jrhodes_velocity_groups_xfade": [
      {"file": "_5", "lovel": 1, "hivel": 60, "xfin": null, "xfout": [25, 60]},
      {"file": "_4", "lovel": 25, "hivel": 84, "xfin": [25, 60], "xfout": [61, 84]},
      {"file": "_3", "lovel": 61, "hivel": 103, "xfin": [61, 84], "xfout": [85, 103]},
      {"file": "_2", "lovel": 85, "hivel": 119, "xfin": [85, 103], "xfout": [104, 119]},
      {"file": "_1", "lovel": 104, "hivel": 127, "xfin": [104, 119], "xfout": null}
    ],
    "jrhodes_velocity_groups_noxfade": [[1, 47], [48, 72], [73, 95], [96, 111], [112, 127]],
    "epmk1_user_params": [
      {"name": "Master Level", "unit": "dB", "min": -100, "max": 0, "default": 0},
      {"name": "Base Frequency", "unit": "Hz", "min": 100, "max": 20000, "default": 440},
      {"name": "Base MIDI Note", "min": 0, "max": 127, "default": 69},
      {"name": "# of Divisions", "min": 1, "max": 100, "default": 12},
      {"name": "Interval to Divide", "min": 0, "max": 30, "default": 2},
      {"name": "Tine Ratio 1", "min": 0, "max": 30, "default": 7},
      {"name": "Tine Ratio 2", "min": 0, "max": 30, "default": 20},
      {"name": "Tine HPF", "unit": "Hz", "min": 20, "max": 20000, "default": 2000},
      {"name": "Tine Decay", "unit": "Q", "min": 1, "max": 2000, "default": 500},
      {"name": "Tine Level", "unit": "dB", "min": -100, "max": 0, "default": -30},
      {"name": "Tine Pick Send", "unit": "dB", "min": -100, "max": 0, "default": -21},
      {"name": "Tone Bar Decay", "unit": "Q", "min": 1, "max": 2000, "default": 1000},
      {"name": "Sustain Pedal", "values": [0, 1], "default": 0},
      {"name": "Tone Bar Release", "unit": "Q", "min": 1, "max": 2000, "default": 10},
      {"name": "Noteoff Level", "unit": "dB", "min": -100, "max": 0, "default": -36},
      {"name": "Tone Bar Level", "unit": "dB", "min": -100, "max": 0, "default": -6},
      {"name": "Hammer Level", "unit": "dB", "min": -100, "max": 0, "default": -30},
      {"name": "Pickup Gain", "unit": "dB", "min": 0, "max": 30, "default": 15},
      {"name": "Pickup Attack", "unit": "dB", "min": -100, "max": 30, "default": 3},
      {"name": "Pickup LPF", "unit": "Hz", "min": 20, "max": 20000, "default": 1000},
      {"name": "Pickup Symmetry", "unit": "dB", "min": 0, "max": 30, "default": 15},
      {"name": "Pickup Level", "unit": "dB", "min": -100, "max": 0, "default": -6},
      {"name": "Buzz Phase", "values": [0, 1], "default": 1},
      {"name": "Buzz Level", "unit": "dB", "min": -100, "max": 0, "default": -9},
      {"name": "Tremolo On/Off", "values": [0, 1], "default": 1},
      {"name": "Tremolo Shape", "min": 0, "max": 127, "default": 0},
      {"name": "Tremolo Rate", "unit": "Hz", "min": 0, "max": 20000, "default": 3},
      {"name": "Tremolo Depth", "unit": "dB", "min": -100, "max": 0, "default": -9}
    ],
    "rhodes_hardware": {
      "key_range_73": ["E1", "E7"],
      "key_range_88": ["A0", "C8"],
      "key_range_88_verified": false,
      "fundamental_range_73_hz": [41, 2600],
      "hammer_tips_manual_88pos": [
        {"tips": [1, 30], "durometer": 30, "height_in": 0.25},
        {"tips": [31, 40], "durometer": 50, "height_in": 0.3125},
        {"tips": [41, 50], "durometer": 70, "height_in": 0.375},
        {"tips": [51, 64], "durometer": 90, "height_in": 0.4375},
        {"tips": [65, 88], "durometer": "wrapped wood", "height_in": 0.4375}
      ],
      "hammer_tips_steves_corner": [
        {"keys": [0, 23], "shore": 30}, {"keys": [24, 33], "shore": 50}, {"keys": [34, 43], "shore": 70}, {"keys": [44, 57], "shore": 90}, {"keys": [58, 81], "shore": "maple+3x shrink"}
      ],
      "escapement_in": {"ideal": 0.03125, "extreme_bass": [0.25, 0.375], "extreme_treble": [0.03125, 0.09375]},
      "tine_pickup_horizontal_gap_in": {"mid": 0.03125, "bass": 0.0625, "wood_tip_treble": 0.0625},
      "tine_pickup_vertical_offset": null,
      "suitcase_vibrato": {"waveform": "square-ish", "mono_until": 1969, "stereo_pan_from": 1969, "rate_hz": null, "depth_db": null},
      "felt_to_neoprene_year": [1970, 1971],
      "mark2_year": 1979
    },
    "fm1_proposed_velocity": {"law": "2^(-R/6.0206*(1-(v-1)/126))", "R_db_default": 30, "R_db_range": [12, 36], "table": "128 x Q15 per R"}
  },
  "per_key": [
    {"midi": 29, "note": "F1", "f0_hz": 43.65, "jr_keys": [21, 32], "jr_layers": [1,2,3,4,5], "jr_release_s": 0.5, "jr_len_soft_s": 18.6, "jr_len_loud_s": 16.8, "epmk1_t60_tonebar_s_Q1000": 50.4, "epmk1_t60_release_s_Q10": 0.50, "hammer_pulse_ms": 22.91},
    {"midi": 35, "note": "B1", "f0_hz": 61.74, "jr_keys": [33, 37], "jr_layers": [1,2,3,4,5], "jr_release_s": 0.5, "jr_len_soft_s": 23.0, "jr_len_loud_s": 19.2, "epmk1_t60_tonebar_s_Q1000": 35.6, "epmk1_t60_release_s_Q10": 0.36, "hammer_pulse_ms": 16.2},
    {"midi": 40, "note": "E2", "f0_hz": 82.41, "jr_keys": [38, 42], "jr_layers": [1,2,3,4,5], "jr_release_s": 0.5, "jr_len_soft_s": 24.6, "jr_len_loud_s": 15.0, "epmk1_t60_tonebar_s_Q1000": 26.7, "epmk1_t60_release_s_Q10": 0.27, "hammer_pulse_ms": 12.13},
    {"midi": 45, "note": "A2", "f0_hz": 110.0, "jr_keys": [43, 47], "jr_layers": [1,2,3,4,5], "jr_release_s": 0.4, "jr_len_soft_s": 25.0, "jr_len_loud_s": 19.6, "epmk1_t60_tonebar_s_Q1000": 20.0, "epmk1_t60_release_s_Q10": 0.20, "hammer_pulse_ms": 9.09},
    {"midi": 50, "note": "D3", "f0_hz": 146.83, "jr_keys": [48, 52], "jr_layers": [1,2,3,4,5], "jr_release_s": 0.4, "jr_len_soft_s": 20.6, "jr_len_loud_s": 14.6, "epmk1_t60_tonebar_s_Q1000": 15.0, "epmk1_t60_release_s_Q10": 0.15, "hammer_pulse_ms": 6.81},
    {"midi": 55, "note": "G3", "f0_hz": 196.0, "jr_keys": [53, 57], "jr_layers": [1,2,3,4,5], "jr_release_s": 0.4, "jr_len_soft_s": 20.4, "jr_len_loud_s": 16.2, "epmk1_t60_tonebar_s_Q1000": 11.2, "epmk1_t60_release_s_Q10": 0.11, "hammer_pulse_ms": 5.10},
    {"midi": 59, "note": "B3", "f0_hz": 246.94, "jr_keys": [58, 60], "jr_layers": [1,2,3,4,5], "jr_release_s": 0.4, "jr_len_soft_s": 17.6, "jr_len_loud_s": 13.0, "epmk1_t60_tonebar_s_Q1000": 8.9, "epmk1_t60_release_s_Q10": 0.089, "hammer_pulse_ms": 4.05},
    {"midi": 62, "note": "D4", "f0_hz": 293.66, "jr_keys": [61, 63], "jr_layers": [1,2,3,4,5], "jr_release_s": 0.3, "jr_len_soft_s": 17.8, "jr_len_loud_s": 14.0, "epmk1_t60_tonebar_s_Q1000": 7.5, "epmk1_t60_release_s_Q10": 0.075, "hammer_pulse_ms": 3.41},
    {"midi": 65, "note": "F4", "f0_hz": 349.23, "jr_keys": [64, 68], "jr_layers": [1,2,3,4,5], "jr_release_s": 0.3, "jr_len_soft_s": 15.0, "jr_len_loud_s": 12.4, "epmk1_t60_tonebar_s_Q1000": 6.3, "epmk1_t60_release_s_Q10": 0.063, "hammer_pulse_ms": 2.86},
    {"midi": 71, "note": "B4", "f0_hz": 493.88, "jr_keys": [69, 73], "jr_layers": [1,2,4,5], "jr_release_s": 0.3, "jr_len_soft_s": 12.8, "jr_len_loud_s": 9.2, "epmk1_t60_tonebar_s_Q1000": 4.45, "epmk1_t60_release_s_Q10": 0.045, "hammer_pulse_ms": 2.02},
    {"midi": 76, "note": "E5", "f0_hz": 659.26, "jr_keys": [74, 78], "jr_layers": [1,2,4,5], "jr_release_s": 0.3, "jr_len_soft_s": 5.2, "jr_len_loud_s": 5.4, "epmk1_t60_tonebar_s_Q1000": 3.34, "epmk1_t60_release_s_Q10": 0.033, "hammer_pulse_ms": 1.52},
    {"midi": 81, "note": "A5", "f0_hz": 880.0, "jr_keys": [79, 83], "jr_layers": [2,4,5], "jr_release_s": 0.3, "jr_len_soft_s": 8.4, "jr_len_loud_s": 6.6, "epmk1_t60_tonebar_s_Q1000": 2.5, "epmk1_t60_release_s_Q10": 0.025, "hammer_pulse_ms": 1.14},
    {"midi": 86, "note": "D6", "f0_hz": 1174.66, "jr_keys": [84, 88], "jr_layers": [2,4,5], "jr_release_s": 0.2, "jr_len_soft_s": 7.2, "jr_len_loud_s": 6.4, "epmk1_t60_tonebar_s_Q1000": 1.87, "epmk1_t60_release_s_Q10": 0.019, "hammer_pulse_ms": 0.85},
    {"midi": 91, "note": "G6", "f0_hz": 1567.98, "jr_keys": [89, 93], "jr_layers": [2,4,5], "jr_release_s": 0.2, "jr_len_soft_s": 3.6, "jr_len_loud_s": 3.0, "epmk1_t60_tonebar_s_Q1000": 1.40, "epmk1_t60_release_s_Q10": 0.014, "hammer_pulse_ms": 0.64},
    {"midi": 96, "note": "C7", "f0_hz": 2093.0, "jr_keys": [94, 108], "jr_layers": [2,4,5], "jr_release_s": 0.2, "jr_len_soft_s": 1.4, "jr_len_loud_s": 1.4, "epmk1_t60_tonebar_s_Q1000": 1.05, "epmk1_t60_release_s_Q10": 0.011, "hammer_pulse_ms": 0.48}
  ]
}
```

Notes on the JSON: `jr_len_*` are sample lengths (S1h), not T60. `epmk1_t60_*` are DERIVED from T60 = 2.199·Q/f0. `jr_layers` uses jRhodes file suffixes, where 1 is the loudest.
