# 08 · Felucca: tempo, clock sync, scales, chords, arp

## Source

- Felucca firmware (GPL-3.0-only, the same licence as Frodhes, so it can be ported), read in place at
  `docs/model/research/sources/06-felucca/Felucca`. Nothing was built or run.
- Path prefixes used below: `fw/` = `Felucca/firmware/src/`, `tests/` = `Felucca/tests/`, `FR/` = the Frodhes repo root.
- Files read: `fw/midi_clock.c`, `fw/seq.c` (keyboard, scale, arp, transport), `fw/chord.c`, `fw/fx.c` (tempo and divisions),
  `fw/voice.c` (LFO sync), `fw/params.c` (name tables, ranges, pages), `fw/core.h` (swing, step_t), `fw/ui_layer.c`
  (tap tempo, SCL layer), `fw/ui_input.c` (LEDs, SELECT = BPM), `fw/midi_control.c` (MIDI IN to chords), and the
  `fw/perform.c`, `fw/motion.c` and `fw/song_chain.c` headers. Tests: `tests/scale_test.c`, `chord_test.c`, `swing_test.c`,
  `ratchet_test.c`, `seq155_test.c`, `perform_test.c` (headers and the scale table).
- The Frodhes side: `FR/firmware/src/frodhes.c`, `FR/docs/API.md`, `FR/firmware/src/platform.c:174-189` (midi_get and
  midi_send), and `FR/firmware/src/usb.c:746` (clock and transport messages reach the MIDI ring).

## Summary

- **Tempo.** It is a global `G_BPM`, an integer from 40 to 240 that defaults to 120 (`fw/params.c:187`). Everything timed uses one function,
  `beat_samples()` (`fw/fx.c:219-222`). It returns `FS*60/BPM` samples per quarter, or the tempo measured from an external clock.
  Divisions are integer fractions or multiples of that number (`fw/fx.c:217,223-227`).
  No float and no 64-bit division are used anywhere in it.
- **MIDI clock in.** You pick INT, USB or TRS (`fw/params.c:49,189`). The tempo is measured over each 6 pulses (a 1/16 note).
  A plausibility window rejects gaps and bursts. Between pulses, positions are interpolated per audio block from timestamps taken when the message arrives
  (`fw/midi_clock.c:33-104`). Start, Continue and Stop drive the transport (`fw/midi_clock.c:11-31`).
  **There is no MIDI clock out** anywhere in Felucca.
- **Tap tempo.** Tap is GLO held plus the F4 key. It averages the last 4 taps, starts setting the tempo from the 3rd tap, and starts over after 2 s without a tap. It only works with the internal clock
  (`fw/ui_layer.c:361-383`).
- **Swing.** Swing is 0..100 and lengthens even steps by `base*sw/250`, so 100 gives step lengths of 1.4x and 0.6x (`fw/core.h:373-384`).
- **Scales.** There are 16 scales stored as 12-bit masks (`fw/seq.c:16-33`). Each track has ROOT 0..11, SCALE, QNT and TRN ±24
  (`fw/params.c:109-112`). QNT has five modes:
  - **OFF**
  - **SNAP**: out-of-scale keys are rounded *down*.
  - **WHITE**: white keys walk the scale degrees from C4 = root, and black keys are silent.
  - **SEQ** and **SEQ+T**: these also snap sequencer notes.

  The code is at `fw/seq.c:113-163`. MIDI IN is *not* scale-quantized; it only gets chords (`fw/midi_control.c:104-127`).
- **Chords, arp and sequencer.**
  - Chord keys: 9 types (diatonic triad and 7th, plus fixed shapes) and 5 voicings, at most 4 notes, with chord naming (`fw/chord.c`).
  - Arp: 14 modes, with RATE in tempo divisions, OCT 1..4, GATE, its own SWING, PROB, HOLD (latch) and ORDER
    (`fw/seq.c:231-449`, `fw/params.c:101-108`).
  - Sequencer: 4 tracks of 64 steps. It is heavy and not worth porting for Frodhes.
- **What to port for Frodhes.**
  - The beat_samples and divisions core (about 30 lines).
  - The tap averager.
  - The tempo measurement in the clock follower, but not the per-block interpolation.
  - SCALE_MASK, scale_snap and the WHITE mapping.
  - Optionally arp_pick (the mode logic is about 40 lines of pure index math).

  Frodhes has to add MIDI clock out itself. Its platform already passes 0xF8/FA/FB/FC to `midi_get` (`FR/firmware/src/usb.c:746`),
  but with no timestamp.

## Tempo & clock

### Storage and range

| What | Value | Where |
| --- | --- | --- |
| BPM | `song.g[G_BPM]`, int16, **40..240**, default **120**, resolution 1 BPM | `fw/params.c:187` |
| Swing (global) | `G_SWING` 0..100, default 0; per track `P_SSWING` 0..100 (sum clamped to `SWING_MAX` 100); the arp has `P_ASWING` 0..100 | `fw/params.c:105,115,188`, `fw/core.h:373-378` |
| Clock source | `G_CLOCK`: 0 INT, 1 USB, 2 TRS | `fw/params.c:49,189` |
| Delay time | `G_DTIME`, an index into `N_DTIME` (13 entries), default 1 = 1/8 | `fw/params.c:16-17,191` |
| Delay buffer | `DLY_LEN` 65536 samples = 1.486 s (1/4 fits from 41 BPM, 1/4D from 61, 1/2 from 81) | `fw/fx.c:5` |

### The internal clock

- **There is no PPQN counter.** The time base is **samples**. `beat_samples()` is the length of a quarter note:
  ```c
  /* fw/fx.c:218-222 */
  static uint32_t midi_beat_samples;   /* zero until an external clock has a measured tempo */
  static uint32_t beat_samples(void)
  { return song.g[G_CLOCK] && midi_beat_samples ? midi_beat_samples : (uint32_t)FS * 60u / (uint32_t)song.g[G_BPM]; }
  ```
- **Each consumer keeps its own counter.** It adds `n` (the block's samples) each block and fires when the counter reaches a period, keeping the remainder:
  - the sequencer `seq_tick`
  - the arp `arp_pos` (`fw/seq.c:443-447`)
  - the metronome `clk_pos` (`fw/seq.c:1264-1282`)
  - the LED `beat_pos` (`fw/seq.c:1410-1415`)

  All of them run once per audio block in `events_block` (`fw/seq.c:1296-1418`).

  Note that with the internal clock the arp and the LED beat run **even when the transport is stopped**
  (`arp_step(..., clock_mode ? seq_n : n, ...)`, `fw/seq.c:1409-1410`).
- **The metronome.** It counts 1/16 steps (`div_samples(2)`). A beat is 4 of them (`click_beat_len = 4*div_samples(2)`). This means the click never drifts against
  1/16 tracks, even though `beat_samples/4` truncates (`fw/seq.c:336-356`). `click_beat_now()` gives 0..3, or -1 when stopped, and drives the
  on-screen metronome (`fw/seq.c:1286-1293`, `fw/ui_draw.c:153,210`).
- **Transport requests** from the UI come through `transport_req`: 1 start, 2 stop, 3 restart (`fw/seq.c:51,1308-1327`).
  With an external clock, PLAY acts as if a 0xFA had arrived (`fw/seq.c:1309-1310`). GLO+PLAY restarts the song from the top on INT only (`fw/seq.c:1321-1326`).

### Tap tempo (`fw/ui_layer.c:361-383`)

```c
/* GLO TAP: from the third tap the tempo of the taps (the last 4); 2 s without one starts over. INT clock only */
if (song.g[G_CLOCK]) { ui_message("TAP: CLK IS EXT"); return; }
if (n && fm1_ms - lys.tap[n-1] > 2000u) n = 0;            /* timeout 2000 ms */
if (n == 4u) { shift left by one; n = 3; }               /* window: the last 4 taps (3 intervals) */
lys.tap[n++] = fm1_ms;
if (n >= 3u && lys.tap[n-1] != lys.tap[0])
    song.g[G_BPM] = clamp(60000u * (n-1) / (lys.tap[n-1] - lys.tap[0]), 40, 240);
ui.bpm_t = 40;                                            /* header BPM highlighted for 40 frames */
```

- The buffer is `uint32_t tap[4]; uint8_t ntap;` (`fw/ui_layer.c:101-102`).
- It is the mean over the span of all the taps, not the median of the intervals.
- It does not re-phase the clock: the beat phase is left alone.

### MIDI clock in (`fw/midi_clock.c`, `fw/seq.c:1372-1397`)

- **Timestamps.** USB-MIDI packets are timestamped with `fm1_ms` when the ring is written (`fw/usb.c:186-187`). The TRS UART
  keeps a timestamp and the source for F8/FA/FB/FC (`fw/midi_uart.c:10,34-35`).
- **Messages are only taken from the selected source** (`clock_mode == source`, `fw/seq.c:1379`). Changing `G_CLOCK` stops the
  sequencer and zeroes the clock state (`fw/seq.c:1300-1305`).
- **0xFA Start**: position 0, measurement reset, `seq_start()` (`fw/midi_clock.c:13-18`).
- **0xFB Continue**: the position stays at the rendered one, the measurement is reset, and playing resumes (`fw/midi_clock.c:19-27`). Song Position (0xF2) is not handled.
- **0xFC Stop**: `seq_stop()` (`fw/midi_clock.c:28-29`).
- **0xF8 tempo measurement** (`fw/midi_clock.c:36-67`):
  - It takes one measurement every **6 pulses** (1/16 note): `dt = ms - tempo_ms`.
  - It is accepted only if **62 ≤ dt ≤ 375 ms**, which is 240..40 BPM. Anything else is "gaps and corrupt bursts".
  - Samples per quarter: `new_beat = FS*dt/250` (6 pulses = 1/4 beat, so a beat is 4·dt ms, and `FS*4dt/1000 = FS*dt/250`).
  - The display BPM: `G_BPM = clamp((15000 + dt/2)/dt, 40, 240)`.
  - There is **no averaging filter**. The 6-pulse window *is* the smoothing. With 1 ms timestamps the error is at most about 1/62, so roughly ±2 BPM at 240 and
    less at slow tempos.
  - On a tempo change while playing, every running phase (the step positions, the gates, nudges and the click) is rescaled by
    `ratio = (new<<12)/old` (Q12) with a 64-bit **multiply** (`fw/midi_clock.c:47-63`).
- **0xF8 position** (`fw/midi_clock.c:68-83`):
  - Each pulse adds `(beat_samples()+rem)/24` samples, carrying the remainder (`rem = q % 24`).
  - It also measures the interval between pulses (accepted range 8..80 ms) and computes `interp_q8 = pulse_samples*256/interval_ms`. This is the number of samples per ms
    in Q8.
- **Interpolation** (`midi_clock_advance`, `fw/midi_clock.c:86-104`):
  - Each block it advances to `pos + elapsed_ms*interp_q8>>8` and never passes the next pulse until that pulse arrives.
  - It advances at most `FS/8` per block.
  - So the sequencer is pulse-locked, with jitter of about 1 ms.
- **Loss of clock.** If no pulse arrives for 500 ms while playing, it calls `seq_stop()` and invalidates the tempo (`fw/seq.c:1388-1394`).
- **The arp under an external clock.**
  - It advances with the clock (`seq_n`) only.
  - Gates still count down in real time when the transport stops, so no note hangs (`fw/seq.c:332-333,1409`).
  - With no clock running, the arp does not step.

### MIDI clock out

- None. A grep for any 0xF8 send finds only input handling (`fw/usb.c:756,815`, `fw/midi_uart.c:34`).
  Felucca is a follower only.

### Swing (`fw/core.h:374-384`, `fw/seq.c:443-447`, `tests/swing_test.c:3-9`)

```c
static inline int32_t track_swing(const track_t *t)   /* own + global, 0..100 */
{ int32_t sw = t->p[P_SSWING] + song.g[G_SWING]; return sw < 0 ? 0 : sw > SWING_MAX ? SWING_MAX : sw; }
static inline uint32_t swing_step_len(const track_t *t, uint32_t base, uint32_t idx)
{ int32_t sw = track_swing(t) * (int32_t)base / 250; return base + (uint32_t)((idx & 1u) ? -sw : sw); }
```

- Even steps get longer and odd steps shorter, so 100 gives 1.4x and 0.6x (equivalent to about 70 % swing).
- The arp uses the same formula with its own `P_ASWING`, switching on `arp_idx & 1` (`fw/seq.c:443-446`).

## Sync divisions

### Tables

```c
/* fw/params.c:13 — ARP RATE, SEQ DIV, LFO SYNC (stored indices, append-only) */
N_DIV[]   = {"1/4","1/8","1/16","1/32","8T","16T","1/2","1/1","2BAR","4BAR"};
/* fw/params.c:16-17 — the delay's TIME: N_DIV's ten + the dotted ones */
N_DTIME[] = {..N_DIV.., "1/8D","1/16D","1/4D"};
/* fw/fx.c:217,223-227 */
static const uint8_t DIV_DEN[6] = {1, 2, 4, 8, 3, 6};
static uint32_t div_samples(uint32_t div)
{   uint32_t quarter = beat_samples();
    return div < 6u ? quarter / DIV_DEN[div]            /* 1/4 1/8 1/16 1/32 8T(=q/3) 16T(=q/6) */
         : div < 10u ? quarter << (div - 5u)            /* 1/2 1/1 2BAR 4BAR */
         : quarter / DIV_DEN[div % 6u]; }
/* fw/fx.c:234-240 — dotted: 3 quarters >> {2,3,1} = 3/4 q (1/8D), 3/8 q (1/16D), 3/2 q (1/4D) */
static const uint8_t DIV_DOT[3] = {2, 3, 1};
s = d - 10u < 3u ? (beat_samples() * 3u) >> DIV_DOT[d - 10u] : div_samples(d);
return s < 16u ? 16u : s >= DLY_LEN ? DLY_LEN - 1u : s;     /* clamp to the buffer */
```

### Display order and LFO sync

- The display order (longest first) is separate from the stored order (`fw/params.c:290-292`):
  - `DIV_ORDER = {9,8,7,6,0,1,4,2,5,3}` gives 4BAR 2BAR 1/1 1/2 1/4 1/8 8T 1/16 16T 1/32.
  - `DTIME_ORDER = {9,8,7,6,12,0,10,1,11,4,2,5,3}`.
- **LFO sync** (`fw/params.c:7-8`, `fw/voice.c:51-60`). Each value is one LFO cycle per division:
  - `N_LSYNC = {"OFF","4BAR","2BAR","1/1","1/2","1/4","1/8","8T","1/16","16T","1/32"}`
  - `LSYNC_DIV[11] = {0,9,8,7,6,0,1,4,2,5,3}` (maps to N_DIV).
  ```c
  static uint32_t lfo_sync_inc(const track_t *t)          /* phase step per CTL-sample block, Q32 phase */
  {   uint32_t cyc = div_samples(LSYNC_DIV[t->p[P_LSYNC] % 11]), q, r;
      cyc = cyc ? cyc : 1u;
      q = 0xFFFFFFFFu / cyc; r = 0xFFFFFFFFu % cyc;      /* two 32-bit divides, no 64-bit */
      return q * CTL + (r * CTL + CTL) / cyc; }
  ```
  - The phase drift is under a millionth of a cycle per cycle (`fw/voice.c:46-49`).
  - SYNC dims the RATE knob on screen (`fw/ui_draw.c:1318`).
  - LFO TRIG FREE plus SYNC re-phases the LFO to the bar on PLAY (`fw/seq.c:835`).
- **ENV SYNC**, a finer integer table in **1/384 of a 4/4 bar (a quarter = 96)** (`fw/params.c:26-31`). It covers
  1/64T … 4BAR, with dotted and triplet values, 25 entries:
  `ESYNC_UNITS = {0,4,6,8,9,12,16,18,24,32,36,48,64,72,96,128,144,192,256,288,384,576,768,1152,1536}`
  for `"0","1/64T","1/64","1/32T","1/64D","1/32","1/16T","1/32D","1/16","1/8T","1/16D","1/8","1/4T","1/8D","1/4","1/2T","1/4D","1/2","1/1T","1/2D","1/1","1/1D","2BAR","3BAR","4BAR"`.
  This "units of 1/96 quarter" table is the best fit for Frodhes (see the recommendations).
- **perform.c** (the FX hold effects) uses beat fractions directly:
  - `PF_DEN = {2,4,8,2}` for REPEAT 1/8, 1/16, 1/32 and REVERSE (`fw/perform.c:174-175`).
  - A grid of 1/16 = `beat_samples()>>2` (`fw/perform.c:310`).
  - TAPE STOP lasts 1 beat, capped at 32000 samples (`fw/perform.c:62,238-242`).

### At 120 BPM (beat = 22050 samples)

| Div | Units (q=96) | Samples | ms | Hz (LFO) |
| --- | --- | --- | --- | --- |
| 1/1 | 384 | 88200 | 2000 | 0.5 |
| 1/2 | 192 | 44100 | 1000 | 1 |
| 1/4D | 144 | 33075 | 750 | 1.33 |
| 1/4 | 96 | 22050 | 500 | 2 |
| 1/8D | 72 | 16537 | 375 | 2.67 |
| 1/4T | 64 | 14700 | 333 | 3 |
| 1/8 | 48 | 11025 | 250 | 4 |
| 1/16D | 36 | 8268 | 187.5 | 5.33 |
| 1/8T | 32 | 7350 | 167 | 6 |
| 1/16 | 24 | 5512 | 125 | 8 |
| 1/16T | 16 | 3675 | 83 | 12 |
| 1/32 | 12 | 2756 | 62.5 | 16 |

## Scales (tables)

### SCALE_MASK

The masks, copied exactly (`fw/seq.c:16-33`). Bit i means i semitones above ROOT.

```c
static const uint16_t SCALE_MASK[] = {
    0xFFF,                                   /* CHR */
    (1 << 0) | (1 << 2) | (1 << 4) | (1 << 5) | (1 << 7) | (1 << 9) | (1 << 11),   /* MAJ */
    (1 << 0) | (1 << 2) | (1 << 3) | (1 << 5) | (1 << 7) | (1 << 8) | (1 << 10),   /* MIN */
    (1 << 0) | (1 << 2) | (1 << 3) | (1 << 5) | (1 << 7) | (1 << 9) | (1 << 10),   /* DOR */
    (1 << 0) | (1 << 2) | (1 << 4) | (1 << 5) | (1 << 7) | (1 << 9) | (1 << 10),   /* MIX */
    (1 << 0) | (1 << 2) | (1 << 4) | (1 << 7) | (1 << 9),                          /* PEN */
    (1 << 0) | (1 << 3) | (1 << 5) | (1 << 7) | (1 << 10),                         /* MPEN */
    (1 << 0) | (1 << 2) | (1 << 3) | (1 << 5) | (1 << 7) | (1 << 8) | (1 << 11),   /* HARM */
    (1 << 0) | (1 << 1) | (1 << 3) | (1 << 5) | (1 << 7) | (1 << 8) | (1 << 10),   /* PHRY */
    (1 << 0) | (1 << 2) | (1 << 4) | (1 << 6) | (1 << 7) | (1 << 9) | (1 << 11),   /* LYD */
    (1 << 0) | (1 << 1) | (1 << 3) | (1 << 5) | (1 << 6) | (1 << 8) | (1 << 10),   /* LOC */
    (1 << 0) | (1 << 2) | (1 << 3) | (1 << 5) | (1 << 7) | (1 << 9) | (1 << 11),   /* MEL (ascending) */
    (1 << 0) | (1 << 3) | (1 << 5) | (1 << 6) | (1 << 7) | (1 << 10),              /* BLUES (minor) */
    (1 << 0) | (1 << 2) | (1 << 4) | (1 << 6) | (1 << 8) | (1 << 10),              /* WHOLE */
    (1 << 0) | (1 << 1) | (1 << 3) | (1 << 4) | (1 << 6) | (1 << 7) | (1 << 9) | (1 << 10), /* DIMHW */
    (1 << 0) | (1 << 2) | (1 << 3) | (1 << 5) | (1 << 6) | (1 << 8) | (1 << 9) | (1 << 11), /* DIMWH */
};
```

### Interval form

Interval form, as the test states it (`tests/scale_test.c:9-18`), with the names from `fw/params.c:18-19`:

| # | Name | Intervals | n |
| --- | --- | --- | --- |
| 0 | CHR | 0 1 2 3 4 5 6 7 8 9 10 11 | 12 |
| 1 | MAJ (Ionian) | 0 2 4 5 7 9 11 | 7 |
| 2 | MIN (Aeolian) | 0 2 3 5 7 8 10 | 7 |
| 3 | DOR | 0 2 3 5 7 9 10 | 7 |
| 4 | MIX | 0 2 4 5 7 9 10 | 7 |
| 5 | PEN (major pentatonic) | 0 2 4 7 9 | 5 |
| 6 | MPEN (minor pentatonic) | 0 3 5 7 10 | 5 |
| 7 | HARM (harmonic minor) | 0 2 3 5 7 8 11 | 7 |
| 8 | PHRY | 0 1 3 5 7 8 10 | 7 |
| 9 | LYD | 0 2 4 6 7 9 11 | 7 |
| 10 | LOC | 0 1 3 5 6 8 10 | 7 |
| 11 | MEL (melodic minor, ascending) | 0 2 3 5 7 9 11 | 7 |
| 12 | BLUES (minor blues) | 0 3 5 6 7 10 | 6 |
| 13 | WHOLE | 0 2 4 6 8 10 | 6 |
| 14 | DIMHW (half-whole) | 0 1 3 4 6 7 9 10 | 8 |
| 15 | DIMWH (whole-half) | 0 2 3 5 6 8 9 11 | 8 |

### Root, transpose and octave

- `P_ROOT` is 0..11 (C..B) and `P_TRANS` is −24..+24 semitones; both are per track (`fw/params.c:109,112`).
- The octave buttons (`song.octave`) add `12*oct`.
- In the SCL layer, pressing any key sets ROOT to that key's note name: `ROOT = (k+5)%12`, since key 0 is F3 (`fw/ui_layer.c:653-654`).

### Key mapping, `kb_pitch` (`fw/seq.c:132-163`)

The key's raw note is `n = 53 + k`, where key 0 is F3.

- **OFF**: `n + 12*oct + TRN`, chromatic.
- **SNAP** (and SEQ, SEQ+T): `scale_snap(n + 12*oct + TRN)`. An out-of-scale note moves **down** to the nearest scale note:
  `while (guard-- && !(mask >> ((n-ROOT+120)%12) & 1)) n--;` (`fw/seq.c:113-119`).
  - Two adjacent keys can give the same note.
  - Felucca's input layer makes a note held by several sources sound once (`fw/chord.c:15`).
  - TRN is applied *before* the snap, so the scale stays fixed and transpose moves the notes inside it.
- **WHITE**: white keys play the scale degrees and black keys are silent (`KB_SILENT` 255).
  - It uses `DEGREE[12] = {0,-1,1,-1,2,3,-1,4,-1,5,-1,6}`.
  - **C4 is degree 0 = the root** (`60 + ROOT`).
  - Each white key is the next degree, wrapping by the scale's note count, so a pentatonic gives 5 white keys per octave and a diminished scale gives 8.
  - TRN and the octave are added *after* the degree walk.
  - This is the "white keys play the scale" mode, and it is the one fully pinned down by `tests/scale_test.c:21-55`.
- **SEQ**: as SNAP, and sequenced notes also snap when they play. **SEQ+T** also adds TRN to those notes (`fw/seq.c:931-959`).

### MIDI IN versus local keys

- MIDI IN notes are **not** quantized: `midi_play` only runs `chord_build` (`fw/midi_control.c:104-127`).
- The DIA chords snap their *root* onto the scale (`fw/chord.c:54-55`).
- The arp re-maps latched *keys* through `kb_pitch` on every step. A ROOT, SCALE or TRN change therefore reaches notes that are already held. MIDI notes play as they came (`fw/seq.c:183-191,366-378`).

### Display

- The SCL page shows ROOT, SCL, QNT and TRN, with the GR_SCALE graph (`fw/params.c:460`).
- In the SCL layer, the root key is lit and the scale's keys "breathe" (`fw/ui_layer.c:852-855`).
- MENU > SCALE LEDS: the scale keys glow and the root glows brighter, with an INV option (`fw/ui_input.c:301-330,424-435`).

## Chords-Arp-Sequencer

### Chord keys (`fw/chord.c`)

- `P_CHRD` is one of OFF, DIA3, DIA7, MAJ, MIN, DOM7, MAJ7, MIN7, SUS4, POW. `P_VOIC` is one of CLOSE, OPEN, INV1, INV2, +OCT (`fw/params.c:42-43`).
- The shapes (`fw/chord.c:21-23`):
  `{0,4,7},{0,3,7},{0,4,7,10},{0,4,7,11},{0,3,7,10},{0,5,7},{0,7,12}` (−1 terminated, `CHORD_MAX 4`).
- **DIA3 and DIA7** stack every other note of the scale from the key, after snapping the key down. CHR falls back to the major scale (`fw/chord.c:41-68`).
- **Voicings** (`fw/chord.c:93-119`):
  - OPEN raises the 2nd tone an octave.
  - INV1 and INV2 rotate the chord.
  - +OCT adds the root an octave down and drops the 5th of a 7th chord.
- Notes are sorted, de-duplicated and clamped to 0..127.
- Each key remembers exactly the notes it started (`kb_chord[27][4]`), and each MIDI note does too (`mchord_t {id,ch,src,n,note[4]}`, 24 slots). Releasing it ends exactly those notes (`fw/chord.c:25-27`).
- `chord_name` builds names such as "Cm7", "F#m7b5" and "Gsus4" from a 12-bit mask (`fw/chord.c:158-182`).
- **No strum** exists: all the chord's notes start in the same block.

### Arp (`fw/seq.c:174-449`)

**State in track_t:**

- `held[16]`, `nheld`
- `arp_phys` (the physical key count)
- `arp_pos` (samples into the step)
- `arp_idx`, `arp_note`, `arp_ch[3]`, `arp_off` (gate samples left), `arp_walk`

**Parameters** (`fw/params.c:101-108`):

| Param | Values | Default |
| --- | --- | --- |
| MODE | 15 entries | — |
| RATE | N_DIV | 1/16 |
| OCT | 1..4 | — |
| GATE | 1..127/128 of the step | 64 |
| SWG | 0..100 | — |
| PROB | 0..127 | — |
| HOLD | OFF / ON | — |
| ORD | NOTE / PLAY | — |

**Modes** (`fw/seq.c:224-232`, `fw/params.c:11-12`): OFF, UP, DN, UPDN, RND, ORD, REPEAT, DNUP, UP+8, CONV, DIVG, PINKY, THUMB, WALK, CHORD.

- `arp_pick` is pure index math on `i = arp_idx` and `len` (`fw/seq.c:291-330`). For example, UPDN is
  `cyc = 2*len-2; k = i%cyc; return k<len ? k : cyc-k;`.
- **The note list.** `arp_list` sorts the held notes (unless ORD is set) and appends the copies for each OCT, up to 64 notes. REPEAT plays the last note (`fw/seq.c:366-398`).
- **Timing** (`fw/seq.c:427-449`):
  - `period = div_samples(ARATE)`, `sw = ASWING*period/250`.
  - `arp_pos += n`. The arp fires when `arp_pos >= period ± sw`.
  - The first note fires at once: `arp_pos = 0xFFFFFFF` sentinel on the first key (`fw/seq.c:193-196`).
- **Gate.** `arp_off = period*AGATE/128` (`fw/seq.c:415`).
- **Latch (HOLD).** A new chord replaces the latched one when the first new key goes down after all keys are up (`fw/seq.c:177-178`). Key-ups are ignored while HOLD is on (`fw/seq.c:206-207`).
  Turning HOLD off with no key held drops the chord (`fw/seq.c:1360-1367`).
- **Output.** The arp ends in `trk_note_on/off` at velocity 100. Recording captures what the arp plays.

### Sequencer and the rest (only noted)

- **Sequencer.** 4 tracks × 64 steps of `step_t {note[4], n, time, flags (ACCENT|SLIDE|RATCH), vel, hit, acc, probability}`
  (`fw/core.h:14,155-164`). Each track has its own LEN, DIV, SWING and GATE (polymeter).
  It also has ratchets x1..x4 (`tests/ratchet_test.c:3-8`), conditions, FILL and EUCLID (`tests/seq155_test.c:3-12`), and nudge.
- **Other files.**
  - `motion.c` is per-step parameter automation and locks (`fw/motion.c:3-10`).
  - `song_chain.c` chains saved projects into sections (`fw/song_chain.c:3-12`).
  - `perform.c` is the FX-hold performance effects (beat repeat and so on) on the master bus (`fw/perform.c:8,43`).

  None of these suit Frodhes.

### Port cost

| Part | Cost | Why |
| --- | --- | --- |
| SCALE_MASK, scale_snap, WHITE mapping | trivial | pure functions, about 50 lines |
| chord_tones, chord_make, chord_name | cheap | pure, about 150 lines; only `trk_vmode` and `chord_kit` to stub |
| arp_pick and arp_list | cheap | pure index math |
| arp_step | moderate | needs a held-note list and Frodhes's note on/off; it runs in the ISR in Felucca |
| Sequencer, motion, song chain | not worth it | — |

## UI & LEDs

Felucca's panel button `B_SCL` is the physical **SEL** button (`fw/panel.c:9`, `fw/ui_input.c:38`). Frodhes calls it `BTN_SEL`.

| Function | Control | Where |
| --- | --- | --- |
| BPM | **SELECT encoder** turns the BPM on any page, with acceleration (`accel(EN_SELECT, s, 200)`), unless MENU > BPM LOCK or SELECT PAGE/MODW/VEL take it; GLO + SELECT always changes the BPM | `fw/ui_input.c:1758-1775` |
| BPM feedback | the header BPM is drawn in the accent colour for 40 frames (`ui.bpm_t`) | `fw/ui_draw.c:340,358,1610-1635` |
| CLOCK page | HOME tapped repeatedly reaches CLOCK; KNOB 1..3 are BPM, SWG and CLK | `fw/params.c:497-499` |
| Tap tempo | **GLO held + F4 key** | `fw/ui_layer.c:9-13,647` |
| Tap LED | in the GLO layer, F4 is "can" (breathing) only on the INT clock | `fw/ui_layer.c:849-850` |
| Beat LED | the **ARP button flashes on the beat** while any arp plays: lit for 1/6 beat, or 1/2 beat on beat 1 of the bar; inverted on the ARP page | `fw/ui_input.c:207-215,408-410` |
| Metronome | the header icon swings on `click_beat_now` | `fw/ui_draw.c:153,210` |
| Scale setup | SCL (SEL) tap opens the SCL page (ROOT SCL QNT TRN) and a second tap opens CHORD (CHRD VOIC); **SCL held** makes any key set ROOT, KNOB 1..4 ROOT SCL CHRD VOIC, root lit and scale breathing | `fw/params.c:460-461`, `fw/ui_layer.c:15-16,70,653-654,852-855` |
| Scale LEDs | MENU > SCALE LEDS: the scale's keys glow dim and the root brighter | `fw/ui_input.c:301-330,424-435` |
| Arp | ARP tap opens ARP (MODE RATE OCT GATE), a second tap opens ARP 2 (SWG PROB HOLD ORD) | `fw/params.c:489-490` |
| Played notes | the keys light where the arp or sequencer note would be played (`play_leds`) | `fw/ui_input.c:240-262` |

## Frodhes recommendations

### Constraints

- BTN_REC is taken: it is the sustain pedal.
- The effects follow the reface CP, so the delay TIME, the tremolo, the phaser and the chorus rate each need an optional sync.
- `midi_get` delivers F8/FA/FB/FC (`FR/firmware/src/usb.c:746`). However, it gives **no timestamp**, so Frodhes has to stamp each message in the main
  loop as it drains the ring (with `fm1_micros()`). The error is one main-loop pass, a few ms, which the averaging below absorbs.
- `midi_send(0xF8,0,0)` produces a correct CIN 0xF single-byte packet, because `st>>4 = 0xF` (`FR/firmware/src/platform.c:186-189`).

### 1. Tempo engine (main loop, integer)

```c
/* tempo.c — owned by the main loop; the ISR only reads the volatiles */
#define BPM10_MIN 400u            /* 40.0 */
#define BPM10_MAX 2400u           /* 240.0 */
typedef struct {
    uint16_t bpm10;               /* 0.1 BPM resolution (saved in settings, 2 bytes) */
    uint8_t  src;                 /* 0 INT, 1 MIDI (follow); auto: MIDI while pulses arrive */
    uint8_t  clk_out;             /* send 0xF8 when INT */
    uint32_t beat_us;             /* 600000000 / bpm10  (40.0 BPM -> 1.5e6 us: fits) */
    uint32_t next_pulse_us, pulse_rem; /* Bresenham over 24 pulses: no drift */
    uint8_t  pulse;               /* 0..23 inside the beat */
    uint32_t tap[4]; uint8_t ntap; /* Felucca glo_tap, in ms */
    uint32_t in_last_us, in_acc_us; uint8_t in_n; /* MIDI follow */
} tempo_t;
static volatile uint32_t beat_samples_v = 22050;  /* written by the main loop, read by the ISR (one writer) */

static void tempo_set10(tempo_t *t, uint32_t bpm10) {
    t->bpm10 = clamp(bpm10, BPM10_MIN, BPM10_MAX);
    t->beat_us = 600000000u / t->bpm10;
    beat_samples_v = 44100u * 600u / t->bpm10;    /* 26.46e6 / bpm10: 32-bit */
}
/* tap (Felucca fw/ui_layer.c:361-383), ms → 0.1 BPM */
static void tempo_tap(tempo_t *t) {
    uint32_t n = t->ntap;
    if (n && fm1_ms - t->tap[n-1] > 2000u) n = 0;
    if (n == 4u) { t->tap[0]=t->tap[1]; t->tap[1]=t->tap[2]; t->tap[2]=t->tap[3]; n = 3; }
    t->tap[n++] = fm1_ms; t->ntap = n;
    if (n >= 3u && t->tap[n-1] != t->tap[0])
        tempo_set10(t, 600000u * (n-1) / (t->tap[n-1] - t->tap[0]));
    /* optional: re-phase so the beat lands on this tap: t->pulse = 0; t->next_pulse_us = now + pulse_us */
}
/* MIDI follow: average 24 pulses (one beat). Felucca measures 6 pulses with ms stamps; with
   main-loop jitter, a whole beat plus a one-pole is steadier. */
static void tempo_midi_f8(tempo_t *t, uint32_t now_us) {
    uint32_t dt = now_us - t->in_last_us; t->in_last_us = now_us;
    if (dt < 10000u || dt > 70000u) { t->in_n = 0; t->in_acc_us = 0; return; } /* 240..~36 BPM per pulse: reject */
    t->in_acc_us += dt;
    if (++t->in_n == 24u) {
        uint32_t b = t->in_acc_us;                 /* us per beat */
        t->beat_us += ((int32_t)(b - t->beat_us)) / 4;   /* one-pole smoothing; snap if |diff| > 10 % */
        t->bpm10 = (uint16_t)(600000000u / t->beat_us);
        beat_samples_v = t->beat_us / 100u * 441u / 100u;   /* us -> samples, 32-bit only (<0.01 % error) */
        t->in_n = 0; t->in_acc_us = 0;
    }
    t->pulse = (t->pulse + 1u) % 24u;              /* the beat phase follows the master */
}
/* INT: schedule 24 PPQN in the main loop; drives MIDI clock out, the beat LED, the arp */
static void tempo_poll(tempo_t *t) {
    uint32_t now = fm1_micros();
    while ((int32_t)(now - t->next_pulse_us) >= 0) {
        uint32_t q = t->beat_us + t->pulse_rem;
        t->next_pulse_us += q / 24u; t->pulse_rem = q % 24u;
        if (t->clk_out) midi_send(0xF8, 0, 0);
        t->pulse = (t->pulse + 1u) % 24u;          /* pulse 0 = the beat: LED on, arp ticks every N pulses */
    }
}
```

Notes on the sketch:

- **No 64-bit divide.** The us-to-samples conversion stays 32-bit (`beat_us/100*441/100`).
- **Transport.** Handle 0xFA by resetting `pulse=0` and the arp index, 0xFB by continuing, and 0xFC by stopping the arp.
- **Source switching.** Follow MIDI automatically while F8 arrives (less than 500 ms since the last one, as at `fw/seq.c:1392`), then fall back to INT,
  keeping the last measured BPM.
- **Clock out.** Make it an option, off by default, so it does not fight a DAW that is master.

### 2. Sync-division table

Use one table for delay TIME, tremolo, phaser, chorus and arp. It uses Felucca's ESYNC unit of 1/96 quarter (`fw/params.c:26-31`).

```c
static const char *const SYNC_NAME[] = {"FREE","1/32","1/16T","1/16","1/8T","1/16D","1/8","1/4T","1/8D",
                                         "1/4","1/4D","1/2","1/1","2BAR"};
static const uint16_t SYNC_UNITS[]   = {0, 12, 16, 24, 32, 36, 48, 64, 72, 96, 144, 192, 384, 768};
/* samples (ISR side): beat_samples_v <= 66150 (40 BPM), x768 = 50.8e6: 32-bit OK */
static uint32_t sync_samples(uint32_t i) { return beat_samples_v * SYNC_UNITS[i] / 96u; }
/* delay: fold down an octave of time until it fits the buffer (Felucca clamps instead, fw/fx.c:239) */
static uint32_t delay_sync(uint32_t i, uint32_t maxlen)
{ uint32_t s = sync_samples(i); while (s >= maxlen) s >>= 1; return s; }
/* LFO (tremolo / phaser / chorus): Q32 phase step per sample, Felucca voice.c:56-59 per sample */
static uint32_t lfo_sync_inc(uint32_t i)        /* cycles = the division (or x2/x4 via a MULT knob) */
{ uint32_t c = sync_samples(i); c = c ? c : 1u; return 0xFFFFFFFFu / c; }
```

Recompute these only when `beat_samples_v` or the knob changes (in the main loop), and publish the incs as volatiles.

- **Delay.** Glide from the old delay time to the new one to avoid a zipper.
- **Tremolo and phaser rates.** These are musically *fast*. The useful range is 1/32 to 1/4. For the reface CP's
  tremolo, 1/8T to 1/16 at 90-120 BPM gives 4-8 Hz, the classic Rhodes Suitcase range.
- **Chorus.** It is slow: use 1/1, 2BAR, or an extra 4BAR at 1536 units.
- **Re-phasing (optional).** On pulse 0 of a bar, reset the LFO phase only when the user asks for it (a "retrig on beat" flag). Free-running is
  smoother.

### 3. Scale mode for an EP player

- **Default OFF.** A Rhodes player wants chromatic keys.
- **Offer SNAP and WHITE.**
  - SNAP keeps the keyboard layout honest: wrong notes fall onto a neighbour, which is good for jamming over a loop or improvising on a few
    keys.
  - WHITE ("white keys play the scale") is the beginner and one-hand mode. On 27 keys (16 white) it gives more than 2 octaves of the scale.
- **Keep TRN out of the snap**, as Felucca does: the scale stays fixed and transpose moves inside it.
- **Scales.** These 10 are enough for EP: MAJ, MIN, DOR, MIX, LYD, PHRY, HARM, MEL, PEN, MPEN, BLUES. That is 11 with BLUES, and it is
  worth keeping, since it is the soul and funk scale. Optionally add WHOLE and DIMHW for jazz.
- **MIDI IN.** Do not quantize, matching Felucca, with an optional "MIDI IN QNT" setting.
- **Dedupe.** SNAP can give two held keys the same note. Frodhes's `held[k]` already tracks per key. Add a reference count per note
  (`uint8_t cnt[128]`) so the second key does not retrigger and the first key-up does not cut the second.
- **LEDs.** Use `fm1_led_dim` for scale tones, full brightness for the root, and the normal lit state for held keys. The display shows
  `C DOR · SNAP`.
- **Chords (optional, cheap).** Port the DIA3 and DIA7 chord keys for one-finger diatonic chords, at most 4 notes.

### 4. Simple arp and strum (optional)

- **Arp.**
  - Run it in the **main loop** on the 24-PPQN pulse counter: a step every `24*SYNC_UNITS[i]/96` pulses, so 1/16 is every 6 pulses
    and 1/8T is every 8.
  - The jitter is one loop pass, under 1 ms in practice.
  - Modes: UP, DN, UPDN, RND, ORD (as played), CHORD (repeat), copied from `arp_pick`.
  - Add OCT 1..3, GATE, and LATCH. The sustain pedal on REC could double as latch while the arp is on, but keep it as the pedal.
  - Velocity: the key's velocity, or a fixed 100 for the onboard keys.
- **Strum.**
  - It is a delay of k·`strum_ms` per chord note from low to high (or reversed on alternate strums), a 1..40 ms knob.
  - It needs a tiny pending-note queue (`{note, vel, due_ms}[8]`) drained in the main loop.
  - It does not exist in Felucca.

### 5. Controls (avoiding REC)

| Function | Control |
| --- | --- |
| BPM | SELECT encoder on a TEMPO page; GLO + SELECT anywhere (as Felucca) |
| Tap | **PLAY** tapped (Frodhes has no sequencer, so PLAY is free); hold PLAY to toggle MIDI clock out |
| Beat LED | PLAY flashes on each beat (1/6 beat on, the bar's first longer, as in `fw/ui_input.c:207-215`) |
| Scale | **SEL** tapped opens the SCALE page (KNOB 1 ROOT, 2 SCALE, 3 MODE OFF/SNAP/WHITE, 4 TRN); SEL held + key sets ROOT |
| Arp | **ARP** toggles, and ARP held + KNOBs set MODE, RATE, OCT, GATE; the ARP LED is lit while on |
| Sync | each FX rate knob turned past its minimum lands on the SYNC divisions, or a SYNC on/off per effect on the FX page |

## Port list

| Felucca file:function / symbol | Lines | Use in Frodhes |
| --- | --- | --- |
| `fw/fx.c: beat_samples, div_samples, DIV_DEN` | 217-227 | replace with the 1/96-unit table above (same idea) |
| `fw/fx.c: delay_samples, DIV_DOT` | 234-240 | dotted delay; clamp to the buffer |
| `fw/params.c: ESYNC_UNITS / ESYNC_NAMES` | 26-31 | the source of the unit table |
| `fw/voice.c: lfo_sync_inc` | 51-60 | the synced LFO increment (32-bit divides) |
| `fw/ui_layer.c: glo_tap` | 361-383 | tap tempo, almost verbatim |
| `fw/midi_clock.c: midi_clock_pulse` (the tempo part) | 36-67 | the measurement window and rejection; adapt to µs and 24-pulse averaging |
| `fw/midi_clock.c: midi_clock_transport` | 11-31 | Start/Continue/Stop semantics |
| `fw/seq.c: 500 ms clock-loss stop` | 1388-1394 | the fallback to INT |
| `fw/seq.c: SCALE_MASK` | 16-33 | verbatim |
| `fw/seq.c: scale_mask, scale_snap` | 107-119 | verbatim (drop track_t, pass root and mask) |
| `fw/seq.c: kb_pitch` (the WHITE branch, DEGREE) | 132-163 | verbatim |
| `fw/params.c: N_SCALE, N_QUANT, N_NOTE` | 18-19, 40, 54 | names |
| `fw/chord.c: CHORD_SHAPE, chord_tones, chord_make, chord_name` | 21-23, 41-182 | optional chord keys |
| `fw/seq.c: arp_pick, arp_list, arp_fire, arp_step` | 291-449 | optional arp (pull out of track_t) |
| `fw/core.h: swing_step_len` | 380-384 | arp swing (optional) |
| `fw/ui_input.c: arp_led, scale_leds` | 207-215, 301-330 | the LED logic |
| `tests/scale_test.c: EXPECTED, mapping_test` | 9-55 | port as a host test for the scale map |

## Gaps

- **No MIDI clock out** in Felucca. Frodhes must write it (the sketch above, `tempo_poll`).
- **The internal BPM is an integer** (1 BPM). Tap and follow round to 1 BPM in `G_BPM`. The follow path keeps sample resolution in
  `midi_beat_samples` (`fw/midi_clock.c:46,64-65`).
- **Tap is ignored when the clock is external.** It does not re-phase the beat either (`fw/ui_layer.c:364-368`).
- **Follow smoothing** is just a 6-pulse window with a range check; there is no PLL or averaging (`fw/midi_clock.c:40-66`). It relies on the
  timestamps taken in the USB ISR (`fw/usb.c:186-187`). Frodhes's `midi_get` has no timestamp, so expect more jitter. Average over a beat.
- **Song Position Pointer (0xF2)** is not handled. Continue resumes from the position that was rendered (`fw/midi_clock.c:19-21`).
- **MIDI IN is never scale-quantized**, and there is no option for it (`fw/midi_control.c:104-127`).
- **SNAP only rounds down.** There is no "nearest" or "up" option (`fw/seq.c:113-119`).
- **WHITE mode** fixes C4 as the root degree regardless of the octave layout. On Frodhes's F3..G5 keyboard that puts the root
  on the 5th white key (`tests/scale_test.c:46-47`).
- **No strum, no swing on the chord keys**, and no per-note velocity in the arp (it always plays at 100) (`fw/seq.c:423`).
- **Not read in detail:** the sequencer internals (`seq_tick` and `seq_step`), `motion.c` and `song_chain.c` (only their headers were read). They are irrelevant for Frodhes.

## Machine-readable

```json
{
  "source": "Felucca (GPL-3.0-only), firmware/src",
  "bpm": {"min": 40, "max": 240, "default": 120, "resolution": 1, "felucca_ref": "params.c:187",
          "frodhes_recommended": {"store": "bpm10", "min": 400, "max": 2400, "default": 1200}},
  "beat_samples": "FS*60/BPM (fx.c:221); external: FS*dt_6pulses_ms/250 (midi_clock.c:46)",
  "midi_clock_in": {"measure_pulses": 6, "accept_dt_ms": [62, 375], "pulse_interval_ms": [8, 80],
                    "loss_stop_ms": 500, "messages": ["0xF8", "0xFA", "0xFB", "0xFC"], "clock_out": false},
  "tap": {"window_taps": 4, "min_taps": 3, "timeout_ms": 2000, "formula": "60000*(n-1)/(t[n-1]-t[0])"},
  "swing": {"range": [0, 100], "formula": "base + (odd ? -1 : 1) * swing*base/250"},
  "divisions_units_per_quarter": 96,
  "divisions": [
    {"name": "1/32", "units": 12}, {"name": "1/16T", "units": 16}, {"name": "1/16", "units": 24},
    {"name": "1/8T", "units": 32}, {"name": "1/16D", "units": 36}, {"name": "1/8", "units": 48},
    {"name": "1/4T", "units": 64}, {"name": "1/8D", "units": 72}, {"name": "1/4", "units": 96},
    {"name": "1/2T", "units": 128}, {"name": "1/4D", "units": 144}, {"name": "1/2", "units": 192},
    {"name": "1/1", "units": 384}, {"name": "2BAR", "units": 768}, {"name": "4BAR", "units": 1536}
  ],
  "felucca_n_div": ["1/4", "1/8", "1/16", "1/32", "8T", "16T", "1/2", "1/1", "2BAR", "4BAR"],
  "felucca_n_dtime_extra": ["1/8D", "1/16D", "1/4D"],
  "scales": {
    "CHR":   [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
    "MAJ":   [0, 2, 4, 5, 7, 9, 11],
    "MIN":   [0, 2, 3, 5, 7, 8, 10],
    "DOR":   [0, 2, 3, 5, 7, 9, 10],
    "MIX":   [0, 2, 4, 5, 7, 9, 10],
    "PEN":   [0, 2, 4, 7, 9],
    "MPEN":  [0, 3, 5, 7, 10],
    "HARM":  [0, 2, 3, 5, 7, 8, 11],
    "PHRY":  [0, 1, 3, 5, 7, 8, 10],
    "LYD":   [0, 2, 4, 6, 7, 9, 11],
    "LOC":   [0, 1, 3, 5, 6, 8, 10],
    "MEL":   [0, 2, 3, 5, 7, 9, 11],
    "BLUES": [0, 3, 5, 6, 7, 10],
    "WHOLE": [0, 2, 4, 6, 8, 10],
    "DIMHW": [0, 1, 3, 4, 6, 7, 9, 10],
    "DIMWH": [0, 2, 3, 5, 6, 8, 9, 11]
  },
  "scale_modes": ["OFF", "SNAP (round down)", "WHITE (white keys = degrees from C4 = root, black silent)", "SEQ", "SEQ+T"],
  "chord_shapes": {"MAJ": [0, 4, 7], "MIN": [0, 3, 7], "DOM7": [0, 4, 7, 10], "MAJ7": [0, 4, 7, 11],
                   "MIN7": [0, 3, 7, 10], "SUS4": [0, 5, 7], "POW": [0, 7, 12]},
  "arp_modes": ["OFF", "UP", "DN", "UPDN", "RND", "ORD", "REPEAT", "DNUP", "UP+8", "CONV", "DIVG", "PINKY", "THUMB", "WALK", "CHORD"]
}
```
