# 07 · Felucca UI and interaction design → a reface-CP-style UI for Frodhes

## Source

- **Felucca 1.6.1** (GPL-3.0-only, the same licence as Frodhes, so its code may be ported), read in place at
  `docs/model/research/sources/06-felucca/Felucca`. The tree was cloned without `.git` and without its `engines/`
  submodule. So `felucca_engine.h` (`param_desc_t`, `F_*`, `preset_t`) and the generated headers (`ui_fonts.h`,
  `ui_palettes.h`, `ui_icons.h`, the `TIME_MS_X10` / `LFO_HZ_X100` tables) are **not in the clone**. Their shape is
  inferred from how they are used, and this doc says so where that matters.
- Files read: `firmware/src/ui.c ui_input.c ui_layer.c ui_draw.c ui_graph.c (skimmed) ui_menu.c ui_help.c
  ui_name.c ui_tools.c ui_events.c (headers)`, `panel.c params.c menu_items.c gfx.c icons.c favorites.c upreset.c
  settings_persist.c storage.c storage_hw.c project.c (format header, settings, autosave) editor.c editor_menu.c
  main.c (loop) seq.c (scale)`, `README.md`, `web/EDITOR_PROTOCOL.md`, and `tests/ui_test.c ui_render.c run_tests.sh
  target_budget.txt`.
- The Frodhes side: `CLAUDE.md`, `docs/API.md`, `firmware/src/frodhes.c` (the minimal UI: name, last note, keyboard
  strip, octave and PEDAL status, and the sustain pedal on REC at `frodhes.c:69-85`), and `firmware/src/gfx.c`.
- The reface CP panel comes from the coordinator's brief and these pages, which were **not fetched**; the panel is
  described from general knowledge of the instrument:
  <https://usa.yamaha.com/products/music_production/synthesizers/reface/reface_cp.html> and
  <https://fr.yamaha.com/fr/products/music_production/synthesizers/reface/features.html>. Left to right, the panel has
  a TYPE rotary, DRIVE, a TREMOLO/WAH switch with DEPTH and RATE, a CHORUS/PHASER switch with DEPTH and SPEED, a
  D.DELAY/A.DELAY switch with DEPTH and TIME, REVERB DEPTH, and VOLUME. Each switch has three positions:
  effect A / off / effect B.

## Summary

- **Felucca's UI is large and table-driven.** About 11.6k lines across `ui*.c`. One `param_desc_t` table
  (label, format, min, max, default, names, unit; `params.c:80-81,83-168,186-223`) feeds the cards, formatting,
  the editor's DESC, presets and projects. A `PAGES[]` table of `{title, family, scope, graph, id[4]}`
  (`params.c:439-500`) maps each page's four params to KNOB 1..4.
- **Screen.** Lazy redraw: every element caches what it last drew (`ui.c:3-6`). The layout is fixed:
  a 24 px header, four 57x44 knob cards, a 122 px graph panel, and a 38 px footer (`ui.c:139-156`). Frames run at
  60/s at most (`main.c:307-316`). Text is anti-aliased Inter Tight in three sizes, with 4 sub-pixel phases and a
  cached blend ramp per fg/bg pair (`gfx.c:3-10`). The theme is 5 stored colours with derived tokens
  (`gfx.c:80-112`).
- **Gestures.** A page button does one of three things: tap = its page, hold = its *quick layer*, double tap = the
  layer locked open (`ui_layer.c:1-60,263-291`). HOME, SAVE and REC use a 0.7 s tap/hold helper
  (`ui_input.c:1296-1314`). Encoder acceleration is optional (`ui_input.c:470-498`). The turned knob's card turns
  accent-coloured for 40 frames, and its digits roll (`ui.c:137`, `ui_draw.c:60-110`).
- **Storage.** A/B 4 KiB sectors per object, with a 32-byte commit record written last and read back to check it
  (`storage.c:3-14,136-174`). Settings are written only if changed (`project.c:1242-1265`). User presets are 32
  slots of 192 B in two banks (`upreset.c:51-67`). The autosave writes at most once a minute, and only when quiet
  (`project.c:1287-1381`).
- **Web editor.** SysEx `F0 7D 46 4C cmd … F7`, with 14-bit values, DESC-driven parameters and a WATCH/PUSH
  live sync (`EDITOR_PROTOCOL.md:70-110,184-272,377-400`). The model can be reused, but Frodhes should use its own
  2-byte tag and a small subset. On Frodhes, `platform_poll()` hands every SysEx frame to `ota_service()`, which
  drops any frame that is not an update frame (`frodhes ota.c:146-166`, `platform.c:261`), so it needs a one-line
  app hook.
- **Proposal: a reface-CP-style PANEL screen.** Five columns: VOICE (TYPE + DRIVE) · TREM/WAH · CHO/PHA · DELAY ·
  REVERB. The knobs are mapped so that every reface control is at most one button tap away:
  - ALGORITHM = TYPE, SELECT = tempo, PRESETS = presets.
  - K1/K2 = DEPTH/RATE of the focused effect column; K3 = DRIVE and K4 = REVERB always.
  - LFO / FX / ARP focus a column. Tapping the focused button flicks its 3-way switch; holding it opens all four of
    the column's knobs.
  - EDIT/ENV = the voicing pages, SEL(SCL) = scale mode, GLO = tempo, PLAY = tap tempo, HOME = panel (hold: menu),
    SAVE = save (hold: undo).
  - **REC stays the sustain pedal.**

## Screen architecture

**Layers and pages.** `ui_draw_page` (`ui_draw.c:1569-1643`) picks one full-screen state, in priority order:
UBOOT countdown → MENU (HOME held) → count-in → OCT-/OCT+ dialog (`ui.confirm`) → NAME entry → a quick layer's map
over the page → the page itself. The page itself is header, cards, graph and footer (`ui_draw.c:1621-1641`).
Pages belong to *families*, one per button (`params.c:432-433`, `ui_input.c:38-39`). Tapping the same button again
steps through the family's pages (`ui.c:763-784`). HOME, MIXER and CLOCK form one cycle (`ui.c:800-813`). With
MENU > SELECT PAGE, SELECT can step pages instead (`ui.c:816-840`).

**Layout** (`ui.c:139-156`):

| Area | Size |
| --- | --- |
| Header | y 0..24 |
| Cards | y 28..72, four of 57x44 at x = 3 + 59c |
| Graph panel | y 76..198 |
| Footer | y 202..240 |

MENU > LARGE makes the cards 104 px tall and the panel a strip at y 136 (`ui.c:150-156,371-397`).

**Redraw strategy.**
- Each element has a signature and is drawn only when it changes:
  - header: `head_sig` (`ui_draw.c:355-370`)
  - footer: `foot_sig` (`ui_draw.c:857-859`)
  - graph: `graph_signature()` (`ui_graph.c:1185,2247-2248`)
  - each card: a key string made of label|value|unit|colour|gauge-pixel|icon|hot, compared with `ui.col[c]`
    (`ui_draw.c:648-694`)
- `ui.force` forces a full redraw after a page change (`ui.c:177`).
- Rolling digits redraw only a 17 px value strip of the card (`ui_draw.c:694-700`). They take 9 frames
  (`ui_draw.c:68`), snap when the turn is fast (`ui_draw.c:69,94-105`), and can be turned off (MENU > ANIM OFF,
  `ui.c:47`).
- Frame budget: the main loop draws one frame, then keeps polling input until 15 ms have passed, so at most about
  60 frames/s (`main.c:307-316`).
- Drawing goes into an off-screen strip of up to 240x124 px in `.pool` (59.5 KB), sent with one blit
  (`gfx.c:3-5,70-71`).

**Primitives** (`gfx.c`):

| Function | Lines |
| --- | --- |
| `cv_begin` / `cv_blit` / `cv_blit_from` | 188-218 |
| `cv_rect`, `cv_frame`, `cv_rule` | 227-260 |
| `cv_line`, `cv_line_t` (thick) | 261-290 |
| `cv_rrect` (anti-aliased rounded rectangle) | 303 |
| `ramp(fg, bg)` (cached 16-step blend) | 340 |
| `cv_alpha` / `cv_alpha_hc` (Huffman-coded 4-bit alpha) | 381, 429 |
| `cv_text`, `cv_text_on`, `cv_text_r`, `cv_text_in`, `text_fit`, `cv_text_fit` (ellipsis) | 593-690 |
| keycaps `cv_keycap` and key-hint rows `cv_key_row` (e.g. "[K1] HITS") | 700-790 |
| `draw_text_box` | 858 |

**Fonts.** `AF_S` 12 px/400, `AF_M` 15 px/500, `AF_L` 28 px/600, Inter Tight (`gfx.c:23`). Each glyph is
rasterised at 4 horizontal phases (2 for L) and kerned (`gfx.c:6-9`); they are generated by
`tools/gen_aa_font.py`. The usage rule is "M what is read, S what describes it, L the one big readout"
(`ui_draw.c:6-10`).

**Compared with Frodhes's `gfx.c`.** Frodhes has an older subset of the same code:
- `cv_begin`, `cv_rect`, `cv_line`, `cv_pset`, `cv_text`, `text_w` and `draw_text_box`
  (`frodhes gfx.c:62-187`)
- one 4-bit anti-aliased face per size, `FONT_S` 16 px and `FONT_L` 32 px, with capitals only for L (`docs/API.md`)

What it lacks:
- **Text can only be blended onto black.** Its ramp goes from black to the ink colour (`frodhes gfx.c:142-160`),
  so text on a filled card or switch cell shows a black fringe. Felucca's `ramp(fg,bg)` cache (`gfx.c:340-380`)
  is what makes filled cards and highlighted cells possible.
- Rounded rectangles, sub-pixel phases, kerning, ellipsis and icons.

Frodhes's canvas is 240x64 (`platform.c:57`). Frodhes also still carries the old 5-step `PALETTES[]`
(`frodhes gfx.c:31-58`), which `frodhes.c` does not use; it has its own `C_ACC`.

**Theme.** Each palette stores 5 colours: bg, surf, text, theme, accent (`gfx.c:21`). The other tokens (mid, dim,
line, sel, tint, ink, rec, raise, key, lane, grid) are derived from them by blending (`gfx.c:80-112`). STYLE is
FLAT (filled SURF cards) or LINE (1 px rules) (`gfx.c:91-95`). COLOR offers 10 built-in palettes plus CUSTOM,
which is set from the web editor (`favorites.c:33-55`, README "New in 1.6"). The host tests check that every
GREY pixel is grey and every MONO pixel neutral (`tests/ui_render.c:13-15`).

**Icons.** 4-bit alpha cells taken from the MIT Fukiai icon font, at 12, 16 and 24 px, Huffman-coded
(`icons.c:3-11`). A parameter's icon is chosen from its label (`icons.c:164-216`). `FELUCCA_ICONS=0` builds
without them (`icons.c:9-10,281-287`).

**Screen off.** MENU > SCREEN OFF turns the screen dark after 5 to 60 minutes. Waking it swallows the input that
woke it, then the screen comes back in steps: SLPOUT, 120 ms, a redraw, DISPON (`ui.c:229-366`).

**Host tests.**
- `tests/ui_test.c` compiles the real `ui*.c` against a stub display and HAL. It drives frames and the panel
  through helpers: `frame()` (16 ms: `ui_input` + `ui_draw`), `press()`, `hold()` (0.8 s) and `turn()`
  (`ui_test.c:250-284`), and covers sound loads, undo, saves, screen off, and a 150,000-frame soak of the rolling
  digits (`ui_test.c:1-40`).
- `tests/ui_render.c` renders every screen in every palette. Through `GFX_HOOK_*` (`gfx.c:27-66`) it lints the
  layout: text off-screen, overlapping, or cut; ink drawn in its own background colour; alignment within 1 px. It
  writes PPMs and a report (`ui_render.c:3-36`; run from `run_tests.sh:308-322`).

## Controls & gestures

| Control | Felucca role (default) | Where |
| --- | --- | --- |
| SELECT | Tempo (BPM, with acceleration). The menu option SELECT PAGE makes it step the family's pages; MODW/VEL make it play. BPM LOCK requires GLO held | `ui_input.c:1758-1780` |
| ALGORITHM | Selects the track (on every page). Steps tabs in the MENU | `ui_input.c:1756`, `ui_menu.c:514-520` |
| PRESETS | On HOME: browses sounds (`preset_step`). On list pages: picks the row (as KNOB 1). Steps rows in the MENU | `ui_input.c:1268-1294`, `ui.c:1709-1714` |
| KNOB 1..4 | The page's four params (`edit_param`). On HOME: the engine's four main params (`home_param`) | `ui_input.c:941-1055,1782-1812`, `ui.c:1734-1739` |
| OCT- / OCT+ | Octave ±3 (both together: 0). In dialogs and on action pages: back/cancel and do/confirm. Their LEDs breathe when the button would do something | `ui_input.c:44-49,1612,1695-1705` |
| HOME | Tap: HOME → MIXER → CLOCK. Hold: MENU | `ui.c:800-813`, `ui_input.c:1575` |
| SAVE | Tap: SAVE pages. Hold: UNDO the last sound load (`undo_swap`) | `ui_input.c:1606-1611` |
| REC | Tap: arm. Hold: its layer | `ui_input.c:1509,1587` |
| PLAY | Start/stop. GLO + PLAY: restart | `ui_input.c:1678-1688` |
| FX GLO SCL EDIT SEQ REC | Tap: page. Hold: a quick layer (keys and K1..4 become its shortcuts, with a map drawn over the page). Double tap: locked open | `ui_layer.c:1-60` |
| ENV LFO ARP | Tap only: their family's pages. LFO held makes knob turns *momentary*: values snap back on release, OCT+ keeps them | `ui_input.c:50-62` |

**The layer gesture** (`ui_layer.c:263-291`):
- Released before HOLD (0.3 to 0.6 s, set in the menu: `panel.c:76-87`) with nothing else touched: a tap.
- Held past HOLD: the map is shown (a peek).
- Any key, knob or button pressed meanwhile: a *combo*. The map opens at once and the release is not a tap.
- After a layer closes, KNOB 1..4 are ignored for 250 ms, so a knob still turning does not edit the page below
  (`ui_layer.c:111,293-299`).
- Keys pressed with the layer button held are the layer's: silent, no MIDI.
- **Port this gesture: it is the basis of the column hold below.**

**Long press.** `btn_hold` (`ui_input.c:1296-1314`) returns TAP on release, or HOLD once after 0.7 s; a hold never
also produces a tap.

**Acceleration** (`ui_input.c:470-498`). Off by default (MENU > KNOB ACCEL, `ui.c:48`). It applies only to ranges
wider than 32 steps and never to enums. It measures ms per detent: 25 ms gives x2, 6 ms or less gives x8 (x4 when
the range is 64 steps or less). A reversal or a pause longer than 40 ms resets it.

**Value display.** There is no popup. The card of the knob just turned is drawn in `T_ACCENT` for 40 frames
(`ui.c:137,171`; set at `ui_input.c:1289,1569`), and its digits roll (`ui_draw.c:60-110`). Transient messages go
in the header for about 60 frames (`ui.c:455-465`, `ui_draw.c:264-288`).

**Soft takeover / pickup.** Not needed and not present: every control is a relative encoder. The one absolute
control, MASTER, is the platform's volume.

**LEDs.** The whole LED picture is built off-line and copied one column at a time, to avoid flicker
(`ui_input.c:3-31`). Other options:
- LEDS OFF / DIM LO / DIM HI / INV (`panel.c:89-114`)
- scale LEDs: the root lit, the scale's notes lit (`ui_input.c:305-330`)
- breathing OCT LEDs (`ui_input.c:44-49`)

## Parameter system

**The descriptor.**
- `param_desc_t` = `{label, fmt, min, max, def, names, unit}`, from the `PD`/`PE` macros (`params.c:80-81`) and the
  `PU` macro (`params.c:172`). The type itself lives in the missing engines submodule (`core.h:38-40`).
- Formats: INT PCT BIPCT TIME LFOHZ CUTOFF DB SEMI ENUM BPM NOTE ONOFF OCT STEPS (`EDITOR_PROTOCOL.md:256-263`).
- Two tables: `TP[P_COUNT]` per track (111 params, `params.c:83-168`) and `GP[G_COUNT]` global (`params.c:186-223`).
- A descriptor can depend on context. `track_desc` swaps in the engine's own labels, the INSERT type's labels, or
  note values when ENV SYNC is on (`params.c:225-237`).

**One table drives:**
- the cards (`page_desc`, `params.c:504-523`)
- knob stepping (`param_turn`: clamped, display order for note divisions, skipping retired aliases;
  `params.c:290-318`)
- formatting (`param_format`, at most 5 characters plus a unit; `params.c:322-429`)
- the editor's DESC/GET/SET (`EDITOR_PROTOCOL.md:191-197`)
- presets and projects, which map stored values to today's params *by count* (`upreset.c:12-17,160-165`)
- MIDI LEARN (`ml_knob` called from `edit_param`, `ui_input.c:1051-1054`)

**Rule:** ids are append-only. New common params go just before the engine params (`core.h:52-53`), and enum
values are append-only (`params.c:11,145-147`).

**Formatting** (`params.c:323-429`):

| Format | Display |
| --- | --- |
| PCT | 0..127 shown as % (a 0..100 range shown as is) |
| BIPCT | -64..63 shown as ±100 % |
| TIME | a 128-entry ms×10 table: "x.x ms" / "nnn ms" / "x.xx s" |
| LFOHZ | a ×100 table: "x.xx Hz" |
| CUTOFF | Hz / kHz |
| DB | "OFF" or x.x dB |
| SEMI | "+n st" |
| BPM | "n BPM" |
| ENUM | a name, with an optional unit |
| INT with a 0-terminated name list | the range split evenly over the names |

All of these are integer only (`fmt_fix`, `libc.c:59-77`). Note divisions are shown longest first (`DIV_ORDER`,
`DTIME_ORDER`, `params.c:290-306`). The delay TIME list has dotted values appended (`params.c:14-17`).

## Presets & storage

- **Flash layout** (`storage.c:20-30`):

  | Object | Address |
  | --- | --- |
  | Settings | 0xFC000 (A) / 0xFD000 (B) (`storage.c:66-67`) |
  | 4 projects | 0x97000..0x9EFFF |
  | User samples | 0xA0000..0xDBFFF |
  | User presets | 0xDC000..0xDFFFF |
  | Autosave | 0xE5000 / 0xE6000 |

  Note: Felucca's settings take *two* sectors at 0xFC000, while Dinghy/Frodhes's `settings_save` uses one 256 B
  record at 0xFC000 (`docs/API.md`).
- **Wear and tear handling.** Each object has two sectors, A and B. A save writes the sector that is *not* current:
  erase, write the payload from offset 256, write the 32-byte header (magic, type, slot, seq, len, CRC, header CRC)
  **last**, then read it back (`storage.c:3-14,36-42,136-174`). On load, the newest valid copy wins, with
  wrap-around (`storage.c:98-121`), so a torn write leaves the old copy in charge. Erases and writes are only
  allowed inside the storage ranges (`FL_STORE_OK`, `storage_hw.c:32,43`). An erase silences the audio buffer and
  blanks the LED lines first (`storage_hw.c:22-40`).
- **Settings.** `persist_t` holds the palette, lowcut, panel map, a few flags and 520 B of favourites; spare bytes
  of `favorites.factory[15][…]` hold the UI prefs (`settings_persist.c:2-27`, `ui.c:41-80`). Import migrates old
  versions (`settings_persist.c:30-98`). `settings_poll` writes only when the transport is stopped, and only if
  the exported record differs from the last saved one (memcmp, no erase if equal), retrying after 1 s
  (`project.c:1242-1265`). `settings_later` defers writes from browsing until the view is left or 10 s pass
  (`ui.c:1605-1625`).
- **User presets.** 32 slots of 192 B: used, ver, engine, np, a 12-character name, params packed as value+64 in a
  byte, a 16-step pattern, and a category in the last byte (`upreset.c:43-67,72-84`). They are mirrored in RAM so
  that browsing never reads flash, and written as whole banks of 16. Saving is refused while the transport runs
  ("STOP TO SAVE", `upreset.c:307-320`). Names are 1 to 12 printable characters (`upreset.c:167-176`), entered
  phone-style on the keys (`ui_name.c:1-30`). An unused slot is labelled "U07" (`upreset.c:361`).
- **Factory presets.** A const `presets[]` per engine (`preset_t` in the submodule). The browser lists factory
  presets, then user presets, with favourites and categories as filters (`ui.c:1573-1730`). A load changes the
  sound only; the steps stay; SAVE held undoes it (`ui_test.c:5-10`).
- **Save UX.**
  1. SAVE tap opens the USER page: K1 picks the slot.
  2. OCT+ saves. A used slot asks OVERWRITE?.
  3. The NAME screen opens, prefilled; OCT+ writes, OCT- cancels.
  4. EDIT on the page renames the slot (`ui_name.c:4-11`, `ui_input.c:1612-1660`, `ui_help.c:44`).
- **Autosave.** A hash of the music (no copy). It writes only after 10 s idle with nothing sounding, at most once
  every 60 s, and never while playing. The code's comment works this out as more than 200,000 writes before the
  ~100k-cycle sector limit (`project.c:1287-1302,1313-1381`).
- **Projects.** FUN10 format, 3840 B, one storage object each, retained in `.noinit` too (`project.c:3-6,217`).

## Menus

- HOME held opens the MENU: five tabs, DISPLAY CONTROL AUDIO MIDI SYSTEM, with at most 8 rows each and no
  scrolling (`menu_items.c:46-80`).
  - Navigation: ALGORITHM steps the tab, PRESETS steps the row, any of K1..4 or OCT± changes the value. OCT+ opens
    CALIBRATION / INFO / ABOUT, and HOME closes the menu (`ui_menu.c:503-565`).
  - A tab remembers its last row (`ui.c:174-175`). Settings are saved when the menu closes (`ui_menu.c:496-502`).
- Rows come from one table that the editor shares through MENU_DESC/MENU_SET (`menu_items.c:1-20`,
  `editor_menu.c:1-20`). Two-valued rows are bits in a table (`menu_items.c:101-121`).
- **Help.** With MENU > HELP ON, each page shows a one-line hint built from keycaps and two or three words, for
  about 2 s on entry. Examples: `"[K1-4]A D S R[ENV]ENV DEST"`, `"[K1]SLOT[OCT+]SAVE[SAVE]PRESETS"`
  (`ui_help.c:1-70`). A test checks that every hint fits (`ui_help.c:12`). Each layer has a footer of key hints
  (`ui_layer.c:59-66,81-84`). This is cheap and worth copying.
- **First-run hints.** After a tap, the header says "HOLD [GLO] QUICK" until that layer has been opened once; the
  "seen" bits are saved (`ui_layer.c:51-52,80,231-237`).

## Web editor

The protocol (`web/EDITOR_PROTOCOL.md`):

| Part | Detail | Where |
| --- | --- | --- |
| Framing | `F0 7D 46 4C cmd args F7` (7D = non-commercial ID, "FL"). One reply per request, same cmd | `:70-80` |
| Values | v14: two 7-bit bytes, +8192 | `:84-86` |
| Core commands | INFO, GET, SET, DUMP, DESC (fmt/min/max/def/label/unit plus enum names), PRESET, NAMES, UP_LIST/GET/PUT/STORE/LOAD/ERASE | `:186-206` |
| Live sync | WATCH, then pushes of CHANGED/RELOAD (coalesced at 20 ms), ended by a 3 s PING timeout | `:207-212,377-400` |
| Settings and backup | MENU_DESC/MENU_SET; BACKUP_LIST/GET/PUT with pack7 | — |

The firmware side reads the frames first, so anything else stays for the OTA code (`editor.c:908-931`).

**Can Frodhes reuse it?** Yes, as a *model*:
1. **Use a different tag**, e.g. `F0 7D 46 52` ("FR"). Felucca's editor must not mistake a Frodhes for a Felucca.
2. **Implement a subset:** INFO, GET, SET, DUMP, DESC, WATCH, CHANGED, PING, and later UP_LIST/GET/PUT/LOAD.
   DESC-driven UIs mean that Frodhes's parameter table automatically becomes the browser editor's sliders.
3. **Add a platform hook.** On Frodhes, `platform_poll()` calls `ota_service()`, and `ota_take()` consumes and
   drops every frame that is not an update frame (`frodhes platform.c:255-261`, `ota.c:146-166`). The app needs a
   peek hook such as `app_sysex()` called before `ota_service`. This is the one platform change the editor needs;
   CLAUDE.md asks to keep such changes minimal.

## Cost

Felucca's numbers are estimates from the declarations; nothing was built.

**RAM**

| Item | Size | Section | Where |
| --- | --- | --- | --- |
| `cv_px` canvas, 240x124x2 | 59.5 KB | `.pool` | `gfx.c:70-71` |
| `st_buf` | 3.75 KB | — | `storage.c:77` |
| `up_bank`, 2 x (8 + 16 x 192) | 6.0 KB | `.pool` | `upreset.c:67` |
| `favorites` (also holds the prefs) | 520 B | — | `favorites.c:5-9` |
| `proj_slot[4]` | 15 KB | `.noinit` | `project.c:217` |
| The `ui` struct (four 32-character card caches, rolls, messages) | about 0.5 KB | — | `ui.c:158-226` |
| Layer, NAME and EUCLID state | small | — | — |

The UI proper is about 70 KB of RAM, almost all of it the canvas.

**Flash**
- The `ui*.c` code is about 11.6k source lines, plus `gfx.c`/`icons.c`, which is likely tens of KB of code.
- Fonts: 3 faces x ~95 glyphs x 4 phases of 4-bit Huffman-coded alpha, likely tens of KB. The exact size is in the
  generated `ui_fonts.h`, which is not in the clone.
- `tests/target_budget.txt` tracks only the DSP loop costs, not UI size.

**Frodhes target.** The proposal below fits the current 240x64 canvas if columns are drawn in two strips, or raise
`CV_MAX` to 240x176 (84 KB of the 336 KB pool). The cards' text would use `FONT_S`/`FONT_L`, plus a ported
`ramp(fg,bg)`. Estimate: under 10 KB of code, under 2 KB of RAM beyond the canvas.

## Proposed Frodhes UI (with mockups)

### Principles

- **One main screen, the PANEL, that looks like a reface CP.** Five fixed columns. Every sound control is visible
  and reachable from it without changing page.
- **Same control, same job, everywhere.**
  - ALGORITHM is always TYPE (the reface's big rotary).
  - SELECT is always tempo.
  - PRESETS is always presets (rows inside the menu).
  - K3 is always DRIVE and K4 always REVERB on the PANEL.
- **reface switches are buttons.** A column's button focuses it, so K1/K2 = its DEPTH/RATE. Tapping the focused
  column's button again flicks its 3-way switch: OFF → A → B → OFF. *Hold* the button for all four of the
  column's knobs (port of Felucca's layer gesture).
- **REC is the sustain pedal and nothing else**: hold it, or tap to latch; its LED and the PEDAL status show it
  (`frodhes.c:69-85`).
- Everything is integers, a byte per param, and draw-on-change per column.

### Column and parameter table (one table, Felucca-style)

Each param gets a `{label, fmt, min, max, def, names, unit}` entry. The same table feeds the cards, `param_format`,
the settings record, presets, the CC map and a future editor DESC.

| Column (button) | Switch (3-way) | K1 | K2 | Hold-layer K3 | Hold-layer K4 |
| --- | --- | --- | --- | --- | --- |
| VOICE (SEL hold / always) | TYPE on ALGORITHM: MK I · MK II · SUITCASE · BRIGHT (append-only enum) | — | — | DRIVE | — |
| TREM/WAH (**LFO**) | OFF · TREM · WAH | DEPTH % | RATE Hz, or a note value when SYNC is on | TREM: STEREO 0 = mono .. 127 = autopan · WAH: RANGE | SYNC OFF/1/1..1/16 |
| CHO/PHA (**FX**) | OFF · CHORUS · PHASER | DEPTH % | SPEED Hz | FDBK % (phaser) / WIDTH (chorus) | MIX % |
| DELAY (**ARP**) | OFF · D.DLY · A.DLY | DEPTH % (level) | TIME: ms, or a note value when SYNC is on | FDBK % | SYNC OFF/1/4/1/8D/1/8/1/8T/1/16 (port `N_DTIME` and `DTIME_ORDER`) |
| REVERB (none: one knob) | — | (PANEL K4) | — | — | — |

On the PANEL, K3 = DRIVE and K4 = REVERB DEPTH at all times. VOLUME is MASTER, handled by the platform.

**Pages besides the PANEL** (four knob cards, as in Felucca):

| Page (button) | K1 | K2 | K3 | K4 |
| --- | --- | --- | --- | --- |
| VOICING (**EDIT**) | TONE/BARK (pickup voicing) | HAMMER (hardness) | BELL (tine level) | VEL CURVE (SOFT · MED · HARD · FIXED) |
| VOICING 2 (**ENV**) | DECAY | RELEASE/DAMPER | KEY-OFF NOISE | TUNE (±50 ct) |
| SCALE (**SEL**, the "SCL" key: Felucca's printed label for matrix id 3, `panel.c:12,28`) | MODE (OFF · SNAP · DEGREES) | SCALE (MAJ MIN DOR MIX PEN MPEN BLUES HARM …) | ROOT (C..B) | TRANSPOSE (±24 st) |
| TEMPO (**GLO**) | BPM (40..240) | CLOCK (INT · USB) | TREM SYNC | DLY SYNC |

Notes on these pages:
- SCALE: **hold SEL + any key** sets ROOT (Felucca SCL layer, `ui_layer.c:15-16`). The key LEDs show the root lit
  and the scale's notes dim (`scale_leds`).
- TEMPO: TREM SYNC and DLY SYNC duplicate the columns' SYNC params as a shortcut.

**Scale modes** (port `seq.c:16-32,113-119,133-162`):
- SNAP: every key rounds down onto the scale.
- DEGREES (Felucca's WHITE): white keys walk the scale degrees from C4 = ROOT; black keys are silent.

Frodhes key 0 is F3 = 53, the same base as Felucca's `n = 53 + k`.

### Buttons

| Button | Tap | Hold / combo |
| --- | --- | --- |
| HOME | PANEL | MENU (LEDS, COLOR, KNOB ACCEL, HOLD time, MIDI channel, VEL CURVE global, HELP) |
| LFO / FX / ARP | Focus TREM/WAH, CHO/PHA or DELAY. Tap again on the focused column: flick the switch OFF→A→B→OFF | The column's 4-knob layer (K1..K4 as in the table). Release returns to the PANEL focus |
| EDIT / ENV | VOICING / VOICING 2 | — |
| SEL (SCL) | SCALE page | + key: ROOT |
| GLO | TEMPO page | — |
| PLAY | **TAP tempo** on every screen: the BPM is set from the third tap, and 2 s without a tap starts over (port `glo_tap`, `ui_layer.c:362-383`). The LED flashes on the beat | — |
| SAVE | SAVE page (PRESETS/K1 slot, OCT+ save, OCT- cancel; keys name it) | UNDO the last preset load |
| OCT- / OCT+ | Octave ±2 (both: 0). In SAVE or a dialog: cancel / confirm | — |
| SEQ | reserved (a phrase looper later) | — |
| **REC** | **Sustain latch** | **Sustain while held** (unchanged) |

Button LEDs:
- **LFO / FX / ARP** are lit when their column's switch is not OFF; the focused one breathes.
- **EDIT / ENV / SEL / GLO** are lit on their page.
- **REC** is lit while the sustain is on.
- **PLAY** flashes on the beat.

**Value display.**
- A turned control's cell turns accent-coloured for 40 frames (Felucca `hot_t`).
- A control whose value is not on screen (e.g. ALGORITHM = TYPE on the VOICING page) shows a 2 s header message,
  "TYPE MK II". There is no modal popup.
- Optional rolling digits. Acceleration off by default (port `accel`).

### Presets

- **The PANEL is the sound**, as on a reface: there is no edit buffer to lose.
  - The current sound and the globals (about 40 bytes) live in Dinghy's 256 B settings record.
  - It is saved 2 s after the last change once silent, as `frodhes.c` already does.
  - Port `settings_poll`'s memcmp-before-write too.
- **Factory presets.** 8 to 16 const entries, e.g. "MK I CLEAN", "SUITCASE TREM", "BRIGHT PHASER", "A.DLY BALLAD":
  the params only, no flash use.
- **User presets.** 16 slots of 48 B (12-character name, version, 32 params, spare), one bank of 768 B. Use
  Felucca `storage.c` A/B objects at a new pair of sectors, e.g. 0x97000/0x98000, which needs a matching widening
  of `FL_RANGE_OK` (`docs/API.md`, Memory and flash).
- **Browsing.** The PRESETS knob loads on each detent (factory list, then user slots) and shows "F03 SUITCASE TREM"
  in the header. A load is undoable with SAVE held. Changed params show an asterisk after the name.
- **Saving.** SAVE → the slot list in the graph area → OCT+ → name entry with prefill (port `ui_name.c`, or start
  with the automatic name "USER 05") → OCT+ writes. Writing is allowed only when silent: show "QUIET TO SAVE",
  as Felucca shows "STOP TO SAVE".
- **MIDI.** Program Change selects presets. CC map: TREM DEPTH 92 (CC 92 "Tremolo Depth"), CHO DEPTH 93, REVERB
  91, DRIVE 94 or 13, delay time and depth on general-purpose CCs. The table above carries a `cc` column.

### Mockup 1: PANEL, the main screen (DELAY focused)

Scale is about 6 px per character, 10 px per row. Columns are 48 px wide. The focused column is drawn as a filled
SURF card (shown with `#`) and its knobs in the accent colour.

```
+----------------------------------------+  y 0
| F03 SUITCASE TREM*      120  ♩  PEDAL  |  header: preset (* = edited), BPM (beat dot), sustain
+------+-------+-------+########+--------+  y 26
| TYPE | TREM  |  CHO  |# D.DLY#| REVERB |  switch, position A
|>MK I | >TREM |  CHO  |#>D.DLY#|        |  '>' = selected position (lit cell)
| MK II|  ---  | >---  |#  --- #|        |  OFF position
| SUIT |  WAH  |  PHA  |# A.DLY#|        |  position B
| BRITE|       |       |#      #|        |
+------+-------+-------+########+--------+  y 86
| (●)  |  (●)  |  ( )  |# (●)  #|  (●)   |  knob arcs (gauge = value)
| DRIVE| DEPTH | DEPTH |# DEPTH#| DEPTH  |
|  25% |  60%  |  --   |#  40% #|  35%   |  value, M face
|      |  (●)  |  ( )  |# (●)  #|        |
|      | RATE  | SPEED |# TIME #|        |
|      | 4.2Hz |  --   |# 1/8D #|        |  TIME as a note value (SYNC on)
+------+-------+-------+########+--------+  y 200
| K1 DEPTH  K2 TIME  K3 DRIVE  K4 REVERB |  footer: what the four knobs do now
| [LFO]TREM [FX]CHO [ARP]DLY [PLAY]TAP   |  key hints (cv_key_row)
+----------------------------------------+  y 240
```

Redraw cost:
- A knob turn redraws one 48x114 knob block.
- A focus change redraws two columns and the footer.
- A switch flick redraws one switch cell and that button's LED.

### Mockup 2: VOICING (EDIT), four knob cards with a velocity-curve graph

```
+----------------------------------------+
| VOICING              MK I   120  PEDAL |  header: page, TYPE (ALGORITHM still turns it)
+---------+---------+---------+----------+
| TONE    | HAMMER  | BELL    | VEL      |  four cards (57x44, as in Felucca)
|  +12%   |   64%   |  40%    |  HARD    |  the card of the knob just turned is accent-coloured
| ▬▬▬▬▬▬··| ▬▬▬▬▬···| ▬▬▬·····| ▬▬▬▬▬▬▬··|  gauge
+---------+---------+---------+----------+
|  out ▲                          ___/   |  graph panel: velocity -> level curve
|      |                     ___/        |  (or a tine/pickup sketch for TONE)
|      |               ___---            |
|      |        ___---                   |
|      |__---                     vel ▶  |
+----------------------------------------+
| [ENV]DECAY / RELEASE   [HOME]PANEL     |  footer hint (ui_help-style)
+----------------------------------------+
```

### Mockup 3: SCALE (SEL), with the keyboard strip showing the scale

```
+----------------------------------------+
| SCALE                 DEG  D DOR  120  |
+---------+---------+---------+----------+
| MODE    | SCALE   | ROOT    | TRANS    |
| DEGREES | DORIAN  |   D     |   +0 st  |
+---------+---------+---------+----------+
|  D  E  F  G  A  B  C  D  E  F  G  A    |  white keys -> the scale's degrees (from C4 = ROOT)
| ┌┐┌┐ ┌┐┌┐┌┐ ┌┐┌┐ ┌┐┌┐┌┐ ┌┐┌┐ ┌┐┌┐┌┐     |  keyboard F3..G5 (existing draw_keys)
| │█│ │█│  ...  black keys silent (dark)  |  root key in accent; scale keys lit
+----------------------------------------+
| [SEL]+KEY: ROOT    [PLAY]TAP  [HOME]   |
+----------------------------------------+
```

### Hold layer, shown over the PANEL while ARP is held

```
| [ARP] DELAY  D.DLY                     |  header
| DEPTH 40% | TIME 1/8D | FDBK 55% | SYNC ON |  K1..K4 = all four of the column's knobs
| [ARP]TAP: SWITCH   LET GO: PANEL       |
```

## Port list (file:function → purpose)

| Felucca file:function (lines) | Purpose in Frodhes |
| --- | --- |
| `params.c`: `PD`/`PE` macros and the `TP`/`GP` tables (80-81, 83-223) | The pattern for one Frodhes `PARAMS[]` table (+ `cc`, `col`, `page`) |
| `params.c:param_format` (322-429), `fmt_fix`/`fmt_int` (`libc.c:59-77`) | %, Hz, ms, dB, st, BPM and enum text, integer only |
| `params.c:param_turn`, `enum_order`, `DTIME_ORDER`, `N_DTIME` (14-17, 290-318) | Clamped knob steps; delay/tremolo sync divisions, longest first |
| `params.c:page_t`, `PAGES[]`, `page_desc` (439-523) | The VOICING / VOICING 2 / SCALE / TEMPO pages; column-layer pages |
| `ui_input.c:accel` (470-498) | Encoder acceleration |
| `ui_input.c:btn_hold` (1296-1314) | HOME (menu) and SAVE (undo) tap/hold |
| `ui_layer.c:layer_arm`, `layer_gesture`, `layer_let_go`, `layer_knobs_quiet` (147-299) | Column hold layers (LFO/FX/ARP), combos, the 250 ms knob quiet period |
| `ui_layer.c:glo_tap` (362-383) | TAP tempo on PLAY |
| `ui_input.c:scale_leds` (305-330), `seq.c:SCALE_MASK`, `scale_snap`, `kb_pitch` (16-32, 113-162) | Scale mode (SNAP / DEGREES) and its key LEDs |
| `ui_draw.c:draw_column` (cache key, 648-700), `roll_note`/`roll_text` (60-180) | Draw-on-change cells; optional rolling digits |
| `ui.c:VAL`, `hot_col`/`hot_t` (137, 171), `ui_say`/`ui_message` (455-465) | The accent on the turned knob; header messages |
| `gfx.c:ramp`, `cv_text_on`, `cv_rrect`, `text_fit` (303-380, 593-690) | Text on filled cells, rounded cells, ellipsis (fixes Frodhes's black-only blend) |
| `gfx.c` theme tokens and `palette_set` (80-176) | Optional: 5-colour palettes plus derived tokens instead of hard-coded `C_ACC` |
| `ui_help.c:HELP_PAGE` and `help_row` (15-109) | Keycap hint strings per page |
| `ui_name.c` (whole, ~470 lines) | Naming user presets with the keys (phone-style) |
| `storage.c` (whole) and `storage_hw.c:st_erase`/`st_prog` (28-46) | A/B, torn-write-safe user preset bank; erase with audio silenced |
| `upreset.c:up_name_ok`, `up_valid`, `params_by_count` idea (108-176) | Preset record validation; append-only migration |
| `project.c:settings_poll` (1242-1265), `autosave_quiet` (1337-1347), `ui.c:settings_later` (1605-1625) | No write when unchanged; write only when silent; deferred saves |
| `ui_menu.c:menu_input`/`menu_move`/`menu_tab_go` (503-565), `menu_items.c` tables (13-121) | A small MENU (2 to 3 tabs) driven by one row table |
| `editor.c:ed_service` (908-931), the framing, and the DESC/WATCH subset of `EDITOR_PROTOCOL.md` | A later browser editor (with Frodhes's own tag and an app SysEx hook) |
| `tests/ui_test.c:frame`/`press`/`hold`/`turn` (250-284) | Host UI tests in `tests/host.c` |
| `tests/ui_render.c`: the layout-lint idea through `GFX_HOOK_*` | Optional: catch clipped or overlapping text in screen PNGs |

## Gaps

- `param_desc_t`, `preset_t`, the font/palette/icon headers and the value tables (`TIME_MS_X10`, `LFO_HZ_X100`,
  `LEVEL_DB_X10`) come from the missing `engines/` submodule or from `build/gen`. Their exact layouts and sizes are
  inferred, not read.
- The UI's flash cost (code and fonts) was not measured, because nothing was built. The RAM figures come from the
  declarations.
- The reface CP pages were not fetched; the panel description is from general knowledge, as the brief summarised
  it. The TYPE names (MK I / MK II / SUITCASE / BRIGHT) are a proposal; the engine (`rhodes.c`) defines today only
  one voice.
- Which printed label sits on matrix button 3 is unclear. Dinghy calls it `BTN_SEL`; Felucca's calibrated table
  names it "SCL" (`panel.c:12,28`). Check on hardware.
- Frodhes's `rhodes.c` has no effects yet (tremolo, chorus/phaser, delay, reverb, drive). The UI table assumes
  them. Tempo-synced LFOs and delay need a global BPM in the audio path.
- The ui_graph.c graphs (ADSR, LFO, scope) were only skimmed; none is proposed except the velocity curve.
- A browser editor needs a platform hook before `ota_service()`, which touches platform code.

## Machine-readable

```json
{
  "globals": {
    "ENC_ALGORITHM": "voice.type",
    "ENC_SELECT": "tempo.bpm",
    "ENC_PRESETS": "preset.browse",
    "MASTER": "volume (platform)",
    "BTN_REC": "sustain: hold = on, tap = latch (reserved)",
    "BTN_PLAY": "tap tempo",
    "BTN_OCT_DOWN": "octave -1 / cancel",
    "BTN_OCT_UP": "octave +1 / confirm",
    "BTN_HOME": {"tap": "page PANEL", "hold": "MENU"},
    "BTN_SAVE": {"tap": "page SAVE", "hold": "undo last preset load"},
    "BTN_SEQ": "reserved"
  },
  "params": {
    "voice.type":    {"fmt": "enum", "names": ["MK I", "MK II", "SUITCASE", "BRIGHT"], "def": 0},
    "voice.drive":   {"fmt": "pct", "min": 0, "max": 127, "def": 20, "cc": 94},
    "tw.type":       {"fmt": "enum", "names": ["OFF", "TREM", "WAH"], "def": 0},
    "tw.depth":      {"fmt": "pct", "min": 0, "max": 127, "def": 64, "cc": 92},
    "tw.rate":       {"fmt": "lfohz", "min": 0, "max": 127, "def": 60},
    "tw.x":          {"fmt": "pct", "min": 0, "max": 127, "def": 0, "label_by_type": {"TREM": "STEREO", "WAH": "RANGE"}},
    "tw.sync":       {"fmt": "enum", "names": ["OFF", "1/1", "1/2", "1/4", "1/8", "1/8T", "1/16"], "def": 0},
    "cp.type":       {"fmt": "enum", "names": ["OFF", "CHORUS", "PHASER"], "def": 0},
    "cp.depth":      {"fmt": "pct", "min": 0, "max": 127, "def": 64, "cc": 93},
    "cp.speed":      {"fmt": "lfohz", "min": 0, "max": 127, "def": 40},
    "cp.fdbk":       {"fmt": "pct", "min": 0, "max": 127, "def": 40, "label_by_type": {"CHORUS": "WIDTH", "PHASER": "FDBK"}},
    "cp.mix":        {"fmt": "pct", "min": 0, "max": 127, "def": 127},
    "dl.type":       {"fmt": "enum", "names": ["OFF", "D.DLY", "A.DLY"], "def": 0},
    "dl.depth":      {"fmt": "pct", "min": 0, "max": 127, "def": 50},
    "dl.time":       {"fmt": "time_or_div", "min": 0, "max": 127, "def": 70},
    "dl.fdbk":       {"fmt": "pct", "min": 0, "max": 120, "def": 50},
    "dl.sync":       {"fmt": "enum", "names": ["OFF", "1/4", "1/8D", "1/8", "1/8T", "1/16"], "def": 0},
    "rv.depth":      {"fmt": "pct", "min": 0, "max": 127, "def": 40, "cc": 91},
    "ep.tone":       {"fmt": "bipct", "min": -64, "max": 63, "def": 0, "label": "TONE"},
    "ep.hammer":     {"fmt": "pct", "min": 0, "max": 127, "def": 64},
    "ep.bell":       {"fmt": "pct", "min": 0, "max": 127, "def": 48},
    "ep.velcurve":   {"fmt": "enum", "names": ["SOFT", "MED", "HARD", "FIXED"], "def": 1},
    "ep.decay":      {"fmt": "time", "min": 0, "max": 127, "def": 90},
    "ep.release":    {"fmt": "time", "min": 0, "max": 127, "def": 30},
    "ep.keyoff":     {"fmt": "pct", "min": 0, "max": 127, "def": 32},
    "ep.tune":       {"fmt": "int", "min": -50, "max": 50, "def": 0, "unit": "ct"},
    "scl.mode":      {"fmt": "enum", "names": ["OFF", "SNAP", "DEGREES"], "def": 0},
    "scl.scale":     {"fmt": "enum", "names": ["MAJ", "MIN", "DOR", "MIX", "PEN", "MPEN", "HARM", "PHRY", "LYD", "LOC", "MEL", "BLUES", "WHOLE"], "def": 0},
    "scl.root":      {"fmt": "note", "min": 0, "max": 11, "def": 0},
    "scl.trans":     {"fmt": "semi", "min": -24, "max": 24, "def": 0},
    "tempo.bpm":     {"fmt": "bpm", "min": 40, "max": 240, "def": 120},
    "tempo.clock":   {"fmt": "enum", "names": ["INT", "USB"], "def": 0}
  },
  "pages": {
    "PANEL": {
      "button": "BTN_HOME",
      "columns": [
        {"id": "VOICE",    "switch": "voice.type (ENC_ALGORITHM)", "knobs": ["voice.drive"]},
        {"id": "TREM/WAH", "button": "BTN_LFO", "switch": "tw.type", "knobs": ["tw.depth", "tw.rate"]},
        {"id": "CHO/PHA",  "button": "BTN_FX",  "switch": "cp.type", "knobs": ["cp.depth", "cp.speed"]},
        {"id": "DELAY",    "button": "BTN_ARP", "switch": "dl.type", "knobs": ["dl.depth", "dl.time"]},
        {"id": "REVERB",   "knobs": ["rv.depth"]}
      ],
      "controls": {
        "ENC_KNOB1": "focused column knob 1 (DEPTH)",
        "ENC_KNOB2": "focused column knob 2 (RATE/SPEED/TIME)",
        "ENC_KNOB3": "voice.drive",
        "ENC_KNOB4": "rv.depth",
        "column button tap": "focus; tap again on the focused column = switch OFF->A->B->OFF",
        "column button hold": "layer: K1..K4 = the column's four params"
      },
      "default_focus": "TREM/WAH"
    },
    "LAYER_TREM_WAH": {"hold": "BTN_LFO", "ENC_KNOB1": "tw.depth", "ENC_KNOB2": "tw.rate", "ENC_KNOB3": "tw.x", "ENC_KNOB4": "tw.sync"},
    "LAYER_CHO_PHA":  {"hold": "BTN_FX",  "ENC_KNOB1": "cp.depth", "ENC_KNOB2": "cp.speed", "ENC_KNOB3": "cp.fdbk", "ENC_KNOB4": "cp.mix"},
    "LAYER_DELAY":    {"hold": "BTN_ARP", "ENC_KNOB1": "dl.depth", "ENC_KNOB2": "dl.time", "ENC_KNOB3": "dl.fdbk", "ENC_KNOB4": "dl.sync"},
    "VOICING":   {"button": "BTN_EDIT", "ENC_KNOB1": "ep.tone",  "ENC_KNOB2": "ep.hammer", "ENC_KNOB3": "ep.bell",   "ENC_KNOB4": "ep.velcurve", "graph": "velocity curve"},
    "VOICING_2": {"button": "BTN_ENV",  "ENC_KNOB1": "ep.decay", "ENC_KNOB2": "ep.release", "ENC_KNOB3": "ep.keyoff", "ENC_KNOB4": "ep.tune"},
    "SCALE":     {"button": "BTN_SEL",  "ENC_KNOB1": "scl.mode", "ENC_KNOB2": "scl.scale", "ENC_KNOB3": "scl.root",  "ENC_KNOB4": "scl.trans", "combo": "hold BTN_SEL + key = scl.root", "leds": "root lit, scale notes dim"},
    "TEMPO":     {"button": "BTN_GLO",  "ENC_KNOB1": "tempo.bpm", "ENC_KNOB2": "tempo.clock", "ENC_KNOB3": "tw.sync", "ENC_KNOB4": "dl.sync", "tap": "BTN_PLAY"},
    "SAVE":      {"button": "BTN_SAVE", "ENC_PRESETS": "slot", "ENC_KNOB1": "slot", "BTN_OCT_UP": "save (then name)", "BTN_OCT_DOWN": "cancel", "keys": "name entry"},
    "MENU":      {"button": "hold BTN_HOME", "ENC_ALGORITHM": "tab", "ENC_PRESETS": "row", "ENC_KNOB1-4": "value", "rows": ["LEDS", "COLOR", "KNOB ACCEL", "HOLD TIME", "MIDI CH", "HELP"]}
  },
  "storage": {
    "current_sound_and_globals": "Dinghy settings record (256 B), saved 2 s after change when silent, skip if unchanged",
    "factory_presets": "const table, 8-16 entries",
    "user_presets": {"slots": 16, "record_bytes": 48, "store": "Felucca storage.c A/B object, new sector pair (widen FL_RANGE_OK)"}
  }
}
```
