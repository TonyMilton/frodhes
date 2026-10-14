# Code references: rdpiano, STK Rhodey

Local copies (with `.git` removed) are in `docs/model/research/sources/04-code-rdpiano-stk/{rdpiano,stk,STKAudioKit}`. All `file:line` references below point into those copies. Nothing was built or run. The only processing was a small Python script, run in a separate scratch directory, that read the two STK `.raw` waveforms as data to get their harmonic content.

## Source

| Repo | URL | Commit (HEAD of `--depth 1` clone, 2026-10-15) | Licence | Use under GPL-3.0-only Frodhes |
|---|---|---|---|---|
| rdpiano | https://github.com/giulioz/rdpiano | `9f32e02780b4aef78574356ccc73f54be3e11416` | GPL-3.0 (full GPLv3 text in `LICENSE`; no "or later" notice found; GPLv3 §14 then lets the recipient pick any version). MAME-derived CPU core: BSD-3-Clause (`librdpiano/include/mame_utils.h:1`, `mcu_ops.h:4`). | **Code: yes, it can be ported**, provided attribution is kept and the result stays GPL. **ROMs: NO.** `roms/*.bin` are Roland firmware and sample-ROM dumps (MKS-20, MK-80, RD-200). They are Roland copyright, the GPL grant does not cover them, and they must not be copied, converted or shipped. The `lsp/spaced.cpp` chorus looks like a transliteration of a Roland DSP microprogram (24-bit accumulators, memory offsets), so its IP status is uncertain. Port the ideas, not that file. |
| STKAudioKit | https://github.com/AudioKit/STKAudioKit | `1beeb675678260d90faf5db98b5b84c9fd0b2ceb` | MIT (`LICENSE`), plus the bundled STK sources under the STK licence (`Sources/Stk/LICENSE`, "1995--2016") | **Port: yes.** It is a thin wrapper and adds nothing Rhodes-specific. |
| STK | https://github.com/thestk/stk | `6aacd357d76250bb7da2b1ddf675651828784bbc` | STK licence (`LICENSE`), an MIT-style permissive licence. The request to send modifications upstream is explicitly "not a binding provision". | **Port: yes.** It is GPL-compatible. Keep the copyright and permission notice in the ported files. |

Other notes:
- The STK `Rhodey` comment says the basic FM patent expired in 1995 (`stk/src/Rhodey.cpp:23-27`).
- STKAudioKit's `Rhodey.mm`, `Rhodey.h` and `FM.mm` differ from upstream STK only in formatting and copyright year. I checked this with a whitespace-insensitive diff. Its `sinewave.raw` and `fwavblnk.raw` are byte-identical to upstream (checked with `cmp`).

## Summary

**rdpiano: a chip-level emulator, not a physical model.**
- rdpiano emulates the Roland "SA" (Structured Adaptive) sample-playback digital pianos: MKS-20, RD-1000 and the Roland-built **Rhodes MK-80** (`README.md:9-11`).
- It runs the original 6801 CPU firmware (MAME core) on the original ROMs. It reimplements the custom sound gate arrays IC19 (envelope), IC9 (phase/address) and IC8 (log-sample decode/mix) from silicon traces (`re_stuff/verilog`, `re_stuff/silicon_tooling`). The exp ROMs are marked "bit accurate" (`librdpiano/src/sound_chip.cpp:64,118`).
- The EP sound ("MKS-20: E-Piano 1/2", "MK-80: Classic/Special/Blend/Contemporary", `rdpiano_juce/Source/PluginProcessor.cpp:13-21`) comes **entirely from Roland's sampled waveforms in ROM**. Up to 10 sample "parts" per voice each get their own log-domain multi-stage envelope, sequenced by the firmware through end-of-segment IRQs.
- It contains no tine, pickup or hammer modelling at all.
- What we can reuse:
  - The fixed-point architecture: log-domain samples, envelope and interpolation, decoded by an exp LUT, with no multipliers.
  - An exponential pitch LUT (4096 steps per octave).
  - A rate table that doubles every 8 entries.
  - The segment-and-IRQ envelope sequencing.
  - The plugin-level stereo tremolo, which is an autopan.
- The README says the plugin is moving to the Gearmulator project; this repo is kept as an archive (`README.md:1-5`).

**STK Rhodey: a 4-operator FM patch (TX81Z algorithm 5).**
- Two independent 2-operator FM pairs are summed (`stk/src/Rhodey.cpp:6-14`).
  - Pair A is the body: carrier at 2·f, modulator at f, index 0.536·vel cycles, linear decay over 1.5 s.
  - Pair B is the tine "ping": carrier at 2·f, modulator at 30·f. The modulator uses the waveform `fwavblnk` (half-rectified, blanked sine) with feedback through a two-zero filter. Its index is 0.109·vel cycles and it decays in 0.25 s.
- All envelopes are **linear** ADSRs: 1 ms attack, sustain 0, 40 ms release.
- Velocity scales the output amplitude and both modulation indices linearly. There is no key scaling at all.
- An optional 6 Hz sine tremolo (AM) is off by default (depth 0).
- In about 25 lines it is the cheapest "Rhodes-like" reference, with known weaknesses:
  - The decay is not key-scaled.
  - Every note dies to silence within 1.5 s.
  - Above about MIDI 54 it aliases badly at 44.1 kHz.
- STKAudioKit just wraps one monophonic `Rhodey`. It sets amplitude = vel/127 and uses equal-tempered frequency (`STKAudioKit/Sources/CSTKAudioKit/STKInstrumentDSP.mm:21-22`).

## Model architecture

### rdpiano (Roland SA engine, CPU-B board)

```
MIDI -> 6801 firmware (ROM) --register writes/IRQ--> [per part: IC19 log-env] + [IC9 exp-pitch phase acc + loop] -> wave ROM (log sample + log delta)
      -> IC8: log-add(volume) -> exp LUT (x2: sample, frac*delta) -> sum 16 voices x 10 parts -> 20/32 kHz
      -> [plugin] SpaceD chorus (24-bit DSP emu) -> resample -> stereo tremolo (autopan, float) -> 350 Hz peak EQ (float)
```

| Rhodes part | rdpiano equivalent |
|---|---|
| hammer / attack transient | Recorded inside the samples. Separate "parts" can carry attack segments with their own fast envelopes; which part does what is set by the firmware and is not visible in the C code. |
| tine + tonebar | Sampled waveform segments with loops (`wave_addr_loop`). |
| pickup | Baked into the samples. |
| damper / release | Firmware-programmed envelope segment (env_speed/env_dest) on note-off. Sustain-pedal MIDI is forwarded (`librdpiano/src/mcu.cpp:611-614`). |
| tremolo | Plugin only: float stereo autopan (`PluginProcessor.cpp:523-533`). |
| amp / cabinet | Plugin only: +8 dB peak EQ at 350 Hz, Q 0.2, "tuned by ear to the MKS-20" (`PluginProcessor.cpp:536-545`), plus the SpaceD chorus. |
| noises | None modelled separately. |

### STK Rhodey

```
op2 sine(f)   --env2,gain--> PM of op1 sine(2f) --env1--\
                                                         +-> x0.5 -> *(1 + modDepth*sin(2pi*6Hz*t)) -> out
op4 fwavblnk(30f) <-twozero fb- ; --env4,gain--> PM of op3 sine(2f) --env3--/
```

Mapping onto Rhodes parts, using TX81Z operator numbering (STK `waves_[0..3]` are op1..op4):

| Rhodes part | Rhodey block |
|---|---|
| tine fundamental + low harmonics ("body") | op1 carrier (2·f) modulated by op2 (f) gives sidebands at f, 3f, 4f… Decays linearly over 1.5 s (env1/env2). |
| tine/tonebar high "ping" / bark | op3 carrier (2·f) modulated by op4 (30·f, fwavblnk + feedback) gives a band around 28f–32f. Fast decay: env4 0.25 s, env3 1.0 s. |
| hammer | Only the 1 ms linear attack. No noise or impulse. |
| pickup nonlinearity | None. The FM sidebands stand in for it. |
| damper | ADSR release: linear to 0 in 40 ms from the current value. |
| tremolo | `vibrato_` 6 Hz sine applied as AM. Depth 0 by default. |
| amp, noises | None. |

## Equations / algorithms

### STK Rhodey: exact per-sample algorithm

Constructor (`stk/src/Rhodey.cpp:37-61`) and base class (`stk/src/FM.cpp:31-76`):

```
waves[0..2] = FileLoop("sinewave.raw")   // 1024-sample int16 BE sine, normalized to peak 1.0   (Rhodey.cpp:41-42; FileLoop.h:33 doNormalize=true)
waves[3]    = FileLoop("fwavblnk.raw")   // 256 samples: |sin(4*pi*k/256)| for k<128, 0 for k>=128 (Rhodey.cpp:43)
ratio = {1.0, 0.5, 1.0, 15.0}            // Rhodey.cpp:45-48
fmGains[i] = 0.933033^(99-i)             // FM.cpp:59-63 (-0.602 dB per step; fmGains[99]=1)
gains = {fmGains[99], fmGains[90], fmGains[99], fmGains[67]} = {1.0, 0.535887, 1.0, 0.108819}   // Rhodey.cpp:50-53
adsr[0].setAllTimes(0.001, 1.50, 0.0, 0.04)  // Rhodey.cpp:55
adsr[1].setAllTimes(0.001, 1.50, 0.0, 0.04)  // Rhodey.cpp:56
adsr[2].setAllTimes(0.001, 1.00, 0.0, 0.04)  // Rhodey.cpp:57
adsr[3].setAllTimes(0.001, 0.25, 0.0, 0.04)  // Rhodey.cpp:58
twozero: b0=1 (TwoZero.cpp:22), b1=0, b2=-1 (FM.cpp:39), gain=1.0 (Rhodey.cpp:60)   => y[n] = x[n] - x[n-2]
vibrato (LFO) = 6.0 Hz sine, 2048-entry table, linear interp  (FM.cpp:42; SineWave.h:4; SineWave.h:108-114)
modDepth = 0.0; control1 = 1.0; control2 = 1.0              (FM.cpp:53-55)
```

Note-on (`Rhodey.cpp:67-90`):

```
base = 2.0 * f                                   // Rhodey.cpp:76  (!) base is twice the played pitch
for i: waves[i].rate = 1024or256 * base*ratio[i] / fs    // FileLoop.h:101 -> op freqs {2f, f, 2f, 30f}
gains = amp * {1.0, 0.535887, 1.0, 0.108819}     // Rhodey.cpp:84-87, amp = vel/127 in STKAudioKit
all ADSR keyOn  (attack from current value; phases NOT reset)   // FM.cpp:130-134, ADSR.cpp:47-51
```

Tick (`stk/include/Rhodey.h:75-97`). `addPhaseOffset(x)` sets, it does not accumulate, a read offset of `x` cycles, i.e. `x*fileSize` samples (`FileLoop.cpp:126-130`, applied at `FileLoop.cpp:150-157`). This is true phase modulation:

```
m2  = gains[1] * env2() * W0(ph2) * control1          // Rhodey.h:79-80   (op2 -> op1)
op1.phaseOffset = m2                                  // Rhodey.h:82      (in cycles)
op4.phaseOffset = twozero.lastOut                     // Rhodey.h:83      (feedback, in cycles) = x4[n-1]-x4[n-3]
x4  = gains[3] * env4() * W1(ph4 + offset4)           // Rhodey.h:84
twozero.tick(x4)                                      // Rhodey.h:85
op3.phaseOffset = x4                                  // Rhodey.h:87      (op4 -> op3)
y   = (1 - control2/2) * gains[0]*env1()*W0(ph1+m2)   // Rhodey.h:88
    + (control2/2)     * gains[2]*env3()*W0(ph3+x4)   // Rhodey.h:89
y   = y * (1 + modDepth * lfo())                      // Rhodey.h:92-93  (tremolo = AM, not FM)
out = 0.5 * y                                         // Rhodey.h:95
each FileLoop: read with linear interpolation, then time += rate (wrap modulo size)  // FileLoop.cpp:187-197, Stk.cpp:390-396
```

The update order within a tick is env/osc op2, then op4, then op1 and op3. Each FileLoop is ticked exactly once per sample. op1's offset is set from the op2 sample of the same tick, so there is no extra delay.

ADSR (`stk/include/ADSR.h:115-158`, `stk/src/ADSR.cpp`). The envelope is linear in amplitude:

```
attackRate  = 1/(aTime*fs)                      // ADSR.cpp:126
decayRate   = (1 - sustain)/(dTime*fs)          // ADSR.cpp:136  (sustain = 0 => full scale over dTime)
releaseTime = rTime; on keyOff: releaseRate = value/(rTime*fs)   // ADSR.cpp:146-147, 62-63
ATTACK : v += attackRate; if v >= target(=1): v = 1, state = DECAY
DECAY  : v -= decayRate;  if v <= sustain(=0): v = 0, state = SUSTAIN (silent)
RELEASE: v -= releaseRate; if v <= 0: IDLE
```

Controls (`FM.cpp:147-170`, `FM.h:62-71`). The value v is 0..128, normalized to v/128.
- CC2 → `control1 = 2·v/128`, which scales the op2→op1 index from 0 to 2× the default.
- CC4 → `control2 = 2·v/128`, which crossfades the pairs. The default 1.0 gives 0.5/0.5.
- CC11 → LFO rate = 12·v/128 Hz.
- CC1 → modDepth = v/128.
- CC128 (aftertouch) → `adsr[1]` and `adsr[3]` targets (sustain levels for the two modulators).
- `fmSusLevels` and `fmAttTimes` (`FM.cpp:65-75`) are computed but not used by Rhodey.

Closed form, with the defaults and θ in cycles:

```
y(t) = 0.25*amp*[ e1(t)*sin(2pi*(2f t + 0.535887*amp*e2(t)*sin(2pi f t)))
               +  e3(t)*sin(2pi*(2f t + 0.108819*amp*e4(t)*W1(30 f t + fb))) ] * (1 + d*sin(2pi*6t))
```

### rdpiano: SA sound chip, per part per sample

Source: `librdpiano/src/sound_chip.cpp:213-351`. The engine has 16 voices × 10 parts (`sound_chip.h:22-23`). The chip is clocked once per output sample at 20 kHz or 32 kHz. The 6801 CPU runs 100 or 62 cycles per sample, i.e. a 2 MHz CPU (`mcu.cpp:576-586`). Per-part registers are written by the firmware (`sound_chip.cpp:171-211`): `pitch_lut_i` (16-bit), `wave_addr_loop`, `wave_addr_high`, `env_dest`, `env_speed`, `env_offset`, plus per-voice `flags_0` (env enable) and `flags_1` (phase run).

**IC19, log envelope** (`sound_chip.cpp:239-272`). `env_value` is 28 bits: integer bits [27:20] and fraction [19:0].

```
inc = env_table[env_speed]            // 0..127 = rising rates; 128..255 = falling (two's-complement + carry-in) (l.246-249)
level8 = 1 + (env>>20) + env_offset   // l.251; overflow (>255) means "audible"; 16 env steps per octave
volume(atten, 14 bit) = ~(env[19:14] | (level8&0xF)<<6 | (overflow ? (level8&0xF0)<<6 : 0))   // l.255-259
env += inc ; if crossed env_dest (8-bit, compared on bits [27:20]) => env = dest<<20, raise IRQ   // l.261-271
```

The CPU then loads the next (dest, speed) segment, giving a multi-stage envelope. The env_table rate doubles every 8 entries (`sound_chip.cpp:6-34`).

**IC9, exponential pitch + loop** (`sound_chip.cpp:275-293`):

```
inc   = phase_exp_table[pitch_lut_i]       // pitch_lut_i: [11:0] = 4096 steps/octave mantissa, [15:12] = octave (l.65-115: exp2(13+m/4096))
acc   = (inc + sub_phase) & 0xFFFFFF       // 24-bit phase, sample index = acc>>9 (11 bits) => 9-bit fraction
if (acc>>16) >= wave_addr_loop (8-bit): acc[23:16] -= wave_addr_loop   // loop by loop*128 samples (my reading of l.277-281)
sub_phase = flags_1 ? acc : 0
addr  = wave_addr_high<<11 | (sub_phase>>9 & 0x7FF)   // 2048-word page per part
mute if sub_phase[23:20] != 0 or pitch_lut_i[15:14]==11 or !flags_1     // l.288-292 (forces +15 octaves attenuation)
```

**IC8, log-domain playback + interpolation** (`sound_chip.cpp:296-340`):

```
S  = samples_exp[addr]   (14-bit log magnitude, 1024 units/octave) + sign
D  = samples_delta[addr] (9-bit log magnitude of next-sample delta, 32 units/octave) + sign
t1 = sat14(volume + S)                                   // gain = addition in log domain
t2 = sat14(volume + ((addr_table[sub_phase[8:5]] + D) << 5))   // addr_table[k] = round(-32*log2(k/16)), [0]=0x1E0 (=mute)
out += exp(t1)*sgnS + exp(t2)*sgnD                        // samples_exp_table: 32768-entry, 15-bit, (t>>10)=octave shift, t&1023 mantissa
```

This is linear interpolation with a 4-bit fraction, `x[n] + (k/16)·Δ[n]`, computed with **only adds and two exp-LUT reads**. The 16-entry `addr_table` (`sound_chip.cpp:46-47`) is exactly −32·log2(k/16). I verified all 16 entries to ±0.5.

The sample ROM word is 24 bits, spread across three 8-bit ROMs: 14-bit log sample + sign, 9-bit log delta + sign (`sound_chip.cpp:368-425`).

**Plugin post-processing.**
- Tremolo (`PluginProcessor.cpp:523-533`):
  - `gL = (1-d) + d·(0.5+0.5·sin(r·π·n/fs))`
  - `gR = (1-d) + d·(0.5+0.5·sin(π + r·π·n/fs))`
  - Rate is `r/2` Hz with r = 0..14, i.e. 0–7 Hz. Depth `d = depth/14`.
  - L and R run in antiphase, which makes it a stereo autopan like the Rhodes Suitcase "vibrato".
- Chorus: a 24-bit integer DSP program. Its state is `eram[65536]` and it uses linearly interpolated modulated taps (`lsp/spaced.cpp:192-260`). It has 10-bit fractional delay interpolation, `multiplCoef1 = (offs & 0x3ff) << 13` (l.211).

## Parameters

### STK Rhodey

| Param | Value | Source |
|---|---|---|
| Algorithm | TX81Z #5: 4→3, 2→1, summed | `Rhodey.cpp:6-14` |
| Base frequency | 2·f_note | `Rhodey.cpp:76` |
| Ratios op1..op4 | 1.0, 0.5, 1.0, 15.0 (×base), i.e. 2f, f, 2f, 30f | `Rhodey.cpp:45-48` |
| Waveforms | op1–3 `sinewave.raw` (1024 × int16 BE, peak ±32767); op4 `fwavblnk.raw` (256 × int16, \|sin\| over 2 humps then 128 zeros; harmonics re DC: 0.318, 0.424 at h1, 0.255 at h3, 0.212 at h4, 0.061 at h5…) | `Rhodey.cpp:41-43`; file analysis |
| fmGains table | fmGains[i] = 0.933033^(99−i); step −0.602 dB | `FM.cpp:59-63` |
| gains op1..op4 | 1.0, 0.535887 (−5.42 dB), 1.0, 0.108819 (−19.27 dB), all × amp | `Rhodey.cpp:50-53, 84-87` |
| Mod index op2→op1 | 0.535887·amp·control1·env2 **cycles** (3.367 rad at amp=1) | `Rhodey.h:79-82` |
| Mod index op4→op3 | 0.108819·amp·env4 cycles (0.684 rad at amp=1) | `Rhodey.h:84-87` |
| op4 feedback | phase offset = x4[n−1] − x4[n−3] (cycles), gain 1 | `FM.cpp:39-40`, `Rhodey.cpp:60`, `Rhodey.h:83`, `TwoZero.h:94-97` |
| Mix | (1−control2/2)·pairA + (control2/2)·pairB; default control2 = 1 gives 0.5/0.5; output × 0.5 | `Rhodey.h:88-95`, `FM.cpp:55` |
| ADSR op1 | A 1 ms, D 1.50 s (linear to 0), S 0, R 40 ms | `Rhodey.cpp:55` |
| ADSR op2 | A 1 ms, D 1.50 s, S 0, R 40 ms | `Rhodey.cpp:56` |
| ADSR op3 | A 1 ms, D 1.00 s, S 0, R 40 ms | `Rhodey.cpp:57` |
| ADSR op4 | A 1 ms, D 0.25 s, S 0, R 40 ms | `Rhodey.cpp:58` |
| ADSR rate @44.1 kHz as Q31 per-sample increment | A: 48695774; D1.5: 32464; D1.0: 48696; D0.25: 194783; R(from 1.0): 1217394 | derived from `ADSR.cpp:126,136,63` |
| LFO (tremolo) | sine 2048-pt table with linear interp; 6.0 Hz default; CC11 → 0..12 Hz | `FM.cpp:42,161-162`, `SineWave.h:4` |
| Tremolo depth | modDepth default 0; CC1 → 0..1; AM: ×(1 + d·sin) | `FM.cpp:53,163-164`, `Rhodey.h:92-93` |
| Velocity | amp = vel/127 scales output **and** both indices linearly | `STKInstrumentDSP.mm:21`, `Rhodey.cpp:84-87` |
| Key scaling | none (f = 440·2^((n−69)/12)) | `STKInstrumentDSP.mm:22` |
| Sample rate | default 44100; ADSR rates rescale on change | `Stk.h:597`, `ADSR.cpp:38-45` |
| Oscillator interpolation | linear, float | `FileLoop.cpp:187-194`, `Stk.cpp:390-396` |

### rdpiano

| Param | Value | Source |
|---|---|---|
| Polyphony | 16 voices × 10 active parts (16 register slots) | `sound_chip.h:22-24` |
| Output rate per patch | MKS-20: P1–3 20k, Harpsi 32k, Clavi 32k, Vibe 20k, **E-Piano 1 20k, E-Piano 2 32k**; MK-80: **Classic 20k, Special 20k, Blend 20k, Contemporary 32k**, AP1 20k, AP2 20k, Clavi 32k, Vibe 20k | `PluginProcessor.cpp:71-75` |
| CPU | 6801 at 2 MHz (100 cycles per sample @20k, 62 @32k) | `mcu.cpp:580-583` |
| Pitch resolution | 4096 steps/octave (0.293 cent), 16 octave shifts | `sound_chip.cpp:65-115` |
| Phase accumulator | 24 bit; sample index = bits [19:9] (11 bits per 2048-word page), 9-bit fraction, 4 bits [8:5] used for interpolation | `sound_chip.cpp:276-284,316` |
| Sample format | 14-bit log magnitude + sign; 9-bit log delta + sign; 24-bit words | `sound_chip.cpp:391-424` |
| Log scale | 1024 units per octave (6.02 dB) for sample/volume; delta 32 units per octave | `sound_chip.cpp:119-123,322,329-330` |
| exp LUT | 32768 × 15-bit (sign × 16 octaves × 1024) | `sound_chip.cpp:119-163` |
| phase exp LUT | 65536 × 19-bit | `sound_chip.cpp:65-115` |
| Envelope | 28-bit accumulator; 8-bit level; 16 steps per octave (0.376 dB/step) | `sound_chip.cpp:243-271` |
| Env rate table | 256 entries; [1]=0x23 … [127]=0x1D8000; ×2 every 8 entries; [128+k] = −[k] | `sound_chip.cpp:6-34` |
| Env rate in dB/s (@20 kHz) | idx 16: 0.92; 32: 3.68; 48: 14.7; 64: 58.8; 80: 235; 96: 941; 112: 3763; 127: 13876 (×1.6 at 32 kHz) | derived from table and scale above |
| Interp LUT | addr_table = {0x1E0,0x80,0x60,0x4D,0x40,0x36,0x2D,0x26,0x20,0x1B,0x16,0x11,0x0D,0x0A,0x06,0x03} = round(−32·log2(k/16)) | `sound_chip.cpp:46-47` |
| Example env segment program (from RE notes, patch unknown, commented-out) | dest {0xCB,0xD3,0xD2,0xC5,0xBB,0x9D,0xA5,0x00}, speed {0x7F,0x4A,0xA9,0xBD,0xAE,0xB4,0x30,0xCC}; pitch_lut_i 0x6C00 | `re_stuff/rom_tools/descramble_wave.py:139-151` |
| Tremolo (plugin) | rate 0..14 gives 0..7 Hz (default 6, i.e. 3 Hz); depth/14 (default 6); L/R 180° apart | `PluginProcessor.cpp:160-171,523-533` |
| Chorus rate table | period in ms per setting 1..15: 2700,1380,910,680,540,450,385,335,300,265,245,220,205,190,175 | `PluginProcessor.cpp:77-93` |
| Post EQ | peak 350 Hz, Q 0.2, +8 dB | `PluginProcessor.cpp:537-542` |
| Fixed-point I/O | chip sum s32 (15-bit per term); `<<5` into the 24-bit chorus; `>>6` out; /65536 to float | `PluginProcessor.cpp:461-484` |

## Discretization / algorithm cost

**STK Rhodey in float, per voice per sample:**
- 4 table oscillators: phase add, wrap, index, interpolation lerp (1 mul), phase-offset add+wrap.
- 4 ADSR ticks: add + compare.
- 4 gain×env×osc products (8 mul).
- twozero: 1 sub, 2 moves.
- Mix and AM: about 4 mul.
- Total: roughly **20 mul + 30 add/compare/branch**.
- LFO: 1 per instrument.
- Tables: 1024 + 256 samples (2.5 KB as int16), plus a 2048-entry LFO table.

**Integer port estimate (per voice per sample):**
- 4 × (`ph += inc`; `idx = (ph + off) >> 22`; `s = tab[idx]`), with no interpolation if the sine table is ≥1024 entries Q15.
- 4 × `(s * envgain) >> 15`.
- 2 × index scaling `(m * K) << n` into Q32 phase.
- feedback `x4[n-1] - x4[n-3]`.
- mix.
- That is about **8–10 MUL + 25 ALU + 4 loads ≈ 35–45 instructions**.
- If the envelopes are evaluated once per 16- or 32-sample sub-block, with a linear ramp or held, then **~30 instructions** per sample.
- 8 voices × 256 frames × 40 ≈ **82k instructions per block** (8 voices × 44 100 × 40 ≈ 14 M instr/s).
- The AC791N clock and CPI are not established in these sources. *If* it is about 160 MHz with CPI ≈ 1.5, that is ≈ 0.77 ms per block (13 % of the 5.8 ms budget). At about 320 MHz it is ≈ 0.38 ms.
- **The "bark" pair only (op3+op4) costs about half that.**

**rdpiano SA engine:**
- Per part per sample: about 12 adds/compares (env), 4 (phase/loop), 2 sample-ROM reads + 2 exp-LUT reads, 4 saturating adds. That is about **25 ALU ops, 0 multiplies**.
- The chip computes 160 parts per sample.
- Tables:
  - exp decode 32768 × u16 (64 KB)
  - phase exp 65536 × u32 (256 KB; could be computed analytically, or as 4096 entries plus a shift)
  - env rate 256 × u32 (1 KB)
  - interpolation 16 × u16
  - samples: 128K words × 24 bit per ROM set (384 KB raw), Roland copyright
- The SpaceD chorus is about 60 MACs per stereo sample with a 64K-word delay RAM.

## Measured / reference behaviour

Neither repo contains measurements of a real Rhodes. What follows is behaviour derived from the code:

**STK Rhodey**
- **Amplitude and timing**
  - Every note is silent 1.5 s after note-on, even with the key held (sustain 0, linear decay). There is no key-dependent decay time.
  - The decay is linear in amplitude, not exponential in dB, so the tail sounds like it "drops off a cliff".
  - Peak output ≤ 0.5·amp·(1+modDepth). Two pairs at 0.5 each, then ×0.5, gives ≤ 0.5.
- **Brightness and velocity:** brightness tracks velocity linearly. At amp=1 the op1 index is about 3.37 rad, so the spectrum is strong out to about 5 sidebands, i.e. ≥5f. The op2 index decays linearly with the same 1.5 s as op1, so brightness and loudness fall together.
- **The ping:** the bark/ping band sits at 2f ± k·30f, i.e. at 28f, 32f, … It decays to 0 in 0.25 s (env4 controls the index; the carrier env3 lasts 1.0 s).
- **Aliasing at 44.1 kHz**
  - op4 (30f) itself crosses Nyquist at f > 735 Hz (MIDI ≥ 78).
  - The 4th harmonic of fwavblnk (amplitude 0.21) aliases for f > 184 Hz (MIDI ≥ 54), and the 3rd for f > 245 Hz.
  - Sidebands of op3 alias from even lower keys.
- **Retrigger:** a repeated note restarts the attack from the current envelope value. Oscillator phases are free-running.

**rdpiano**
- The README claims accurate emulation, with exp ROMs "bit accurate" from silicon (`sound_chip.cpp:64,118`). There is a demo video (`README.md:13-15`).
- The 350 Hz EQ was "tuned by ear listening to the MKS-20" (`PluginProcessor.cpp:536`).
- The tremolo and chorus are approximations, "less accurate than the digital emulation" (`README.md:11`).

## FM-1 implementation notes

**Directly reusable in integer fixed point (no FPU, no 64-bit division):**

1. **STK Rhodey as a cheap fallback voice** (permissive licence, so the code can be ported verbatim with notices).
   - Phase: Q32 `uint32` accumulators with host-precomputed increments `inc = round(f_op/44100 · 2^32)`. Examples: op1 for A4 = 85 704 563; op4 for A4 = 1 285 568 442. See `per_key` below.
   - Sine: 1024-entry Q15 table. fwavblnk can be generated, not loaded: `w[k] = |sin(4πk/256)|` for k<128, else 0 (Q15, 256 entries).
   - PM: the modulator output is Q15, and the index in cycles is applied as `off = (m_q15 * idx_q16) << 1` into Q32 phase. For example, idx 0.535887 is Q16 35 120 and 0.108819 is Q16 7 132. All of this is a 32×32 multiply at most.
   - Feedback: keep two previous op4 outputs and use `x[n-1]-x[n-3]` directly as a Q32 phase offset with the same scaling.
   - Envelopes: Q31 linear ramps (increments in the Parameters table). It is better to replace them with exponential (dB-linear) decays, see point 3.
2. **"Hybrid" bark layer.**
   - Use only Rhodey pair B (op3 at 2f, op4 at 30f with fwavblnk + feedback, 0.25 s index decay) on top of the main tine/pickup model, to add the bright attack "ping".
   - Cost is about 15–20 instructions per voice-sample. Its index can be gated by velocity (STK uses a linear `amp`; a curve table would be better).
   - Give it a key-scaled level that fades to 0 above roughly MIDI 70 to avoid aliasing.
3. **From rdpiano: log-domain gain and envelopes.**
   - Represent amplitude as attenuation in units of 1/1024 octave and decode with an exp LUT. Note that 1024 mantissa entries are enough; the octave is a shift, so you do not need the full 32K table.
   - An envelope is then a linear accumulator (constant dB/s, which matches tine decays being roughly exponential).
   - Multi-stage decays (fast initial then slow) come from (dest, rate) segments with an "end reached" event, like rdpiano's IRQ. Do this at block rate on the FM-1.
   - The rate table that doubles every 8 entries gives a compact 8-bit, musically even rate control.
4. **From rdpiano: exponential pitch.** Use a 4096-step-per-octave mantissa LUT plus an octave shift, then compute `inc = mant[m] >> (k - oct)`. This avoids any division or pow at note-on and allows cheap pitch-bend and detune.
5. **From rdpiano: multiply-free interpolation.** The log-domain lerp (`exp(S)+exp(D+log(frac))`) is elegant, but the pi32v2 has a hardware multiplier, so a plain Q15 lerp is simpler. Keep it only as a technique for any future sample layer (e.g. hammer noise in log-compressed storage).
6. **Tremolo.** Use rdpiano's stereo autopan form: `g = (1-d) + d·(0.5±0.5·sin)`, with L and R 180° apart and rate about 0–7 Hz. STK's tremolo is mono AM `(1 + d·sin)`, which needs headroom because it can exceed 1.

**Risks:**
- **Licence:** STK is fine (MIT-like). rdpiano code is GPL-compatible, but the ROM sample data and firmware are Roland's and must never be used. The SpaceD chorus port is uncertain IP, so treat it as ideas only.
- **Aliasing:** STK's op4 at 30f with a harmonically rich waveform aliases above about MIDI 54 at 44.1 kHz. Mitigate with key scaling, a sine for op4 at high keys, or a cap on the effective ratio.
- **Sound quality:** STK Rhodey is a crude "DX-ish" EP. Its linear decays (1.5 s) and missing key scaling make it a poor primary model, so use it as a fallback or attack layer only.
- **Phase-modulation precision:** with a 1024-entry table and no interpolation, PM noise is about −60 dB. Use 2048/4096 entries or a lerp if the noise is audible on the pure sine of the body.
- **Feedback stability:** the twozero feedback has gain 2 at fs/4 and the feedback index is bounded by about 2·0.109·amp cycles, so it is stable, but integer wrap of the phase offset must be modular (uint32 arithmetic does this naturally).

## Gaps & open questions

- **rdpiano velocity and key mapping:** velocity→part, envelope and loop parameters live in the 6801 firmware and the params ROM (IC18), which the emulator executes. They are not readable from the C++. Extracting them would mean disassembly (`re_stuff/disasm/mk80_rom_b.asm` exists) of copyrighted firmware. As data about a design this is fine to read, but nothing can be copied.
- **rdpiano loop semantics:** my reading of `sound_chip.cpp:277-281` is that it wraps `acc[23:16]` by `wave_addr_loop` when reached, i.e. a loop length of loop×128 samples. Which "part" carries the attack and which carries the sustain loop for the EP patches is not documented.
- **rdpiano clocking:** whether the chip's per-sample update really runs at 20 kHz or 32 kHz exactly comes from the plugin table (`PluginProcessor.cpp:71-75`), not from hardware docs. The resampler hard-codes /32000 for buffer sizing (`PluginProcessor.cpp:337`).
- **STK Rhodey:** no reference recordings or rationale for its constants (0.933033 gain step, 15× ratio) appear in the repo.
- **FM-1 CPU:** the AC791N clock rate and MUL latency are not established by these sources. The cost estimates above are in instructions and need a cycle count on hardware.

## Machine-readable

```json
{
  "source": {
    "id": "04-code-rdpiano-stk",
    "repos": [
      {"name": "rdpiano", "url": "https://github.com/giulioz/rdpiano", "commit": "9f32e02780b4aef78574356ccc73f54be3e11416", "licence": "GPL-3.0 (MAME parts BSD-3-Clause); ROMs Roland copyright - not licensed", "port_code": true, "port_data": false, "kind": "chip-level emulator of Roland SA sample-playback (MKS-20, RD-1000, Rhodes MK-80)"},
      {"name": "STKAudioKit", "url": "https://github.com/AudioKit/STKAudioKit", "commit": "1beeb675678260d90faf5db98b5b84c9fd0b2ceb", "licence": "MIT + STK licence", "port_code": true, "kind": "Swift/ObjC wrapper of STK Rhodey, monophonic"},
      {"name": "stk", "url": "https://github.com/thestk/stk", "commit": "6aacd357d76250bb7da2b1ddf675651828784bbc", "licence": "STK licence (MIT-style, permissive)", "port_code": true, "kind": "4-op FM (TX81Z algorithm 5)"}
    ]
  },
  "blocks": {
    "stk_rhodey": {
      "topology": "op2->op1 + op4->op3, summed (TX81Z alg 5)",
      "operators": [
        {"op": 1, "stk_index": 0, "role": "carrier body", "freq_mult_of_note": 2.0, "wave": "sine1024", "gain": 1.0, "adsr": {"a_s": 0.001, "d_s": 1.5, "s": 0.0, "r_s": 0.04}, "ref": "Rhodey.cpp:45,50,55"},
        {"op": 2, "stk_index": 1, "role": "modulator of op1", "freq_mult_of_note": 1.0, "wave": "sine1024", "gain": 0.535887, "index_cycles_at_vel1": 0.535887, "adsr": {"a_s": 0.001, "d_s": 1.5, "s": 0.0, "r_s": 0.04}, "ref": "Rhodey.cpp:46,51,56"},
        {"op": 3, "stk_index": 2, "role": "carrier ping", "freq_mult_of_note": 2.0, "wave": "sine1024", "gain": 1.0, "adsr": {"a_s": 0.001, "d_s": 1.0, "s": 0.0, "r_s": 0.04}, "ref": "Rhodey.cpp:47,52,57"},
        {"op": 4, "stk_index": 3, "role": "modulator of op3, self-feedback via twozero", "freq_mult_of_note": 30.0, "wave": "fwavblnk256", "gain": 0.108819, "index_cycles_at_vel1": 0.108819, "adsr": {"a_s": 0.001, "d_s": 0.25, "s": 0.0, "r_s": 0.04}, "ref": "Rhodey.cpp:48,53,58"}
      ],
      "feedback": {"filter": "y[n]=x[n]-x[n-2]", "gain": 1.0, "applied_as": "phase offset cycles of op4 = y[n-1]", "ref": "FM.cpp:39; Rhodey.cpp:60; Rhodey.h:83-85"},
      "mix": {"pairA": 0.5, "pairB": 0.5, "output_scale": 0.5, "ref": "Rhodey.h:88-95; FM.cpp:55"},
      "envelope_shape": "linear ADSR",
      "tremolo": {"type": "AM y*(1+d*sin)", "rate_hz_default": 6.0, "rate_hz_range": [0, 12], "depth_default": 0.0, "depth_range": [0, 1], "lfo_table": 2048, "ref": "FM.cpp:42,53,161-164; Rhodey.h:92-93"},
      "velocity": "amp=vel/127 multiplies all 4 operator gains (output level and both mod indices linear)",
      "key_scaling": null,
      "sample_rate_default": 44100,
      "interp": "linear (float)"
    },
    "rdpiano_sa": {
      "voices": 16,
      "parts_per_voice": 10,
      "output_rate_hz": [20000, 32000],
      "phase_bits": 24,
      "pitch_steps_per_octave": 4096,
      "sample_word_bits": 24,
      "sample_log_bits": 14,
      "delta_log_bits": 9,
      "log_units_per_octave": 1024,
      "env_bits": 28,
      "env_steps_per_octave": 16,
      "env_rate_table_entries": 256,
      "env_rate_doubling_every": 8,
      "interp_frac_bits": 4,
      "multipliers": 0,
      "envelope_sequencing": "CPU reloads (dest,speed) on end-of-segment IRQ",
      "tremolo_plugin": {"type": "stereo autopan, L/R 180 deg", "rate_hz": "param/2, param 0..14", "depth": "param/14", "ref": "PluginProcessor.cpp:523-533"},
      "post_eq": {"type": "peak", "f_hz": 350, "q": 0.2, "gain_db": 8, "ref": "PluginProcessor.cpp:537-542"}
    }
  },
  "params": {
    "stk_fmGains_formula": "0.933033^(99-i)",
    "stk_gain_q15": {"op1": 32767, "op2": 17560, "op3": 32767, "op4": 3566},
    "stk_index_q16_cycles": {"op2_to_op1": 35120, "op4_to_op3": 7132},
    "stk_adsr_q31_inc_44k1": {"attack_1ms": 48695774, "decay_1500ms": 32464, "decay_1000ms": 48696, "decay_250ms": 194783, "release_40ms_from_full": 1217394},
    "stk_lfo_6hz_q32_inc_44k1": 584349,
    "stk_tables": {"sine_entries": 1024, "fwavblnk_entries": 256, "fwavblnk_formula": "|sin(4*pi*k/256)| for k<128 else 0"},
    "rdpiano_addr_table": [480, 128, 96, 77, 64, 54, 45, 38, 32, 27, 22, 17, 13, 10, 6, 3],
    "rdpiano_env_db_per_s_at_20k": {"16": 0.919, "32": 3.675, "48": 14.699, "64": 58.795, "80": 235.18, "96": 940.719, "112": 3762.875, "127": 13875.6},
    "rdpiano_patch_rates_hz": {"MKS20_EPiano1": 20000, "MKS20_EPiano2": 32000, "MK80_Classic": 20000, "MK80_Special": 20000, "MK80_Blend": 20000, "MK80_Contemporary": 32000},
    "est_cost_fm4_int_instr_per_voice_sample": 40,
    "est_cost_bark_pair_int_instr_per_voice_sample": 18,
    "est_cost_8voices_block256_instr": 81920,
    "fm1_cpu_clock_hz": null
  },
  "per_key": [
    {"midi": 21, "f0_hz": 27.5, "op1_hz": 55.0, "op2_hz": 27.5, "op3_hz": 55.0, "op4_hz": 825.0, "op4_above_nyquist": false, "inc_q32_op1": 5356535, "inc_q32_op4": 80348028},
    {"midi": 28, "f0_hz": 41.203, "op1_hz": 82.407, "op2_hz": 41.203, "op3_hz": 82.407, "op4_hz": 1236.1, "op4_above_nyquist": false, "inc_q32_op1": 8025735, "inc_q32_op4": 120386018},
    {"midi": 33, "f0_hz": 55.0, "op1_hz": 110.0, "op2_hz": 55.0, "op3_hz": 110.0, "op4_hz": 1650.0, "op4_above_nyquist": false, "inc_q32_op1": 10713070, "inc_q32_op4": 160696055},
    {"midi": 40, "f0_hz": 82.407, "op1_hz": 164.814, "op2_hz": 82.407, "op3_hz": 164.814, "op4_hz": 2472.21, "op4_above_nyquist": false, "inc_q32_op1": 16051469, "inc_q32_op4": 240772037},
    {"midi": 45, "f0_hz": 110.0, "op1_hz": 220.0, "op2_hz": 110.0, "op3_hz": 220.0, "op4_hz": 3300.0, "op4_above_nyquist": false, "inc_q32_op1": 21426141, "inc_q32_op4": 321392111},
    {"midi": 52, "f0_hz": 164.814, "op1_hz": 329.628, "op2_hz": 164.814, "op3_hz": 329.628, "op4_hz": 4944.41, "op4_above_nyquist": false, "inc_q32_op1": 32102938, "inc_q32_op4": 481544074},
    {"midi": 57, "f0_hz": 220.0, "op1_hz": 440.0, "op2_hz": 220.0, "op3_hz": 440.0, "op4_hz": 6600.0, "op4_above_nyquist": false, "inc_q32_op1": 42852281, "inc_q32_op4": 642784221},
    {"midi": 64, "f0_hz": 329.628, "op1_hz": 659.255, "op2_hz": 329.628, "op3_hz": 659.255, "op4_hz": 9888.83, "op4_above_nyquist": false, "inc_q32_op1": 64205876, "inc_q32_op4": 963088147},
    {"midi": 69, "f0_hz": 440.0, "op1_hz": 880.0, "op2_hz": 440.0, "op3_hz": 880.0, "op4_hz": 13200.0, "op4_above_nyquist": false, "inc_q32_op1": 85704563, "inc_q32_op4": 1285568442},
    {"midi": 76, "f0_hz": 659.255, "op1_hz": 1318.51, "op2_hz": 659.255, "op3_hz": 1318.51, "op4_hz": 19777.65, "op4_above_nyquist": false, "inc_q32_op1": 128411753, "inc_q32_op4": 1926176295},
    {"midi": 78, "f0_hz": 739.989, "op1_hz": 1479.978, "op2_hz": 739.989, "op3_hz": 1479.978, "op4_hz": 22199.67, "op4_above_nyquist": true, "inc_q32_op1": 144137319, "inc_q32_op4": 2162059789},
    {"midi": 81, "f0_hz": 880.0, "op1_hz": 1760.0, "op2_hz": 880.0, "op3_hz": 1760.0, "op4_hz": 26400.0, "op4_above_nyquist": true, "inc_q32_op1": 171409126, "inc_q32_op4": 2571136885},
    {"midi": 88, "f0_hz": 1318.51, "op1_hz": 2637.02, "op2_hz": 1318.51, "op3_hz": 2637.02, "op4_hz": 39555.31, "op4_above_nyquist": true, "inc_q32_op1": 256823506, "inc_q32_op4": 3852352590},
    {"midi": 93, "f0_hz": 1760.0, "op1_hz": 3520.0, "op2_hz": 1760.0, "op3_hz": 3520.0, "op4_hz": 52800.0, "op4_above_nyquist": true, "inc_q32_op1": 342818251, "inc_q32_op4": 847306473},
    {"midi": 100, "f0_hz": 2637.02, "op1_hz": 5274.041, "op2_hz": 2637.02, "op3_hz": 5274.041, "op4_hz": 79110.61, "op4_above_nyquist": true, "inc_q32_op1": 513647012, "inc_q32_op4": 3409737884},
    {"midi": 108, "f0_hz": 4186.009, "op1_hz": 8372.018, "op2_hz": 4186.009, "op3_hz": 8372.018, "op4_hz": 125580.27, "op4_above_nyquist": true, "inc_q32_op1": 815363807, "inc_q32_op4": 3640522516}
  ]
}
```

Notes on `per_key`:
- The increments are `round(f_op/44100·2^32) mod 2^32`. op4 increments above Nyquist wrap and alias, as in STK.
- No source has per-key decay or velocity data, so those fields are omitted rather than invented.
