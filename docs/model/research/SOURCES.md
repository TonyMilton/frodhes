# Research sources

The research notes (`0*.md`) are our own write-ups. The material they were made from lives in `sources/`. Only
code whose licence clearly allows redistribution is committed. Everything else stays on disk only (git-ignored)
and is listed here so it can be fetched again.

## Committed

| Folder | What | Licence |
| --- | --- | --- |
| `sources/06-felucca/Felucca` | Felucca firmware, commit in `Felucca.COMMIT` (engines submodule not included) | GPL-3.0-only; bundled parts per its `LICENSING.md` / `LICENSES/` |
| `sources/04-code-rdpiano-stk/stk` | The Synthesis ToolKit (STK) | STK licence (MIT-style), see its `LICENSE` |
| `sources/04-code-rdpiano-stk/STKAudioKit` | AudioKit wrapper of STK | MIT |

## Not committed (fetch locally)

| Folder | Source | Why not committed |
| --- | --- | --- |
| `sources/01-dafx17/` | Pfeifle, DAFx-17 paper 79: <https://www.dafx.de/paper-archive/2017/papers/DAFx17_paper_79.pdf> | Paper copyright |
| `sources/02-sonderbo-thesis/` | Sønderbo, AAU master's thesis: <https://projekter.aau.dk/projekter/files/719175589/Master_Thesis_Real_time_physical_model_of_the_Rhodes_Electric_Piano_Tobias_Sonderbo.pdf>; code <https://github.com/TSonderbo/EPiano> (commit in `repo/EPiano.COMMIT`) | Thesis needs the author's agreement; code has no licence |
| `sources/03-falaize-phs/` | Falaize & Hélie: <https://hal.science/hal-01390534/>, <http://recherche.ircam.fr/anasyn/falaize/fr/applis/rhodes/>, <https://afalaize.github.io/posts/rhodes/>; PyPHS | Paper copyright; the 2016 code and UVI recordings have no licence |
| `sources/04-code-rdpiano-stk/rdpiano/` | <https://github.com/giulioz/rdpiano> | Contains Roland ROM images and firmware disassemblies; the chorus code may be derived from Roland's |
| `sources/09-reference-samples/` | Text copies fetched by research note 09 (licence pages, thesis/paper text, ETI ROADS listings); see `09-reference-samples.md` for each URL | Third-party copyright |
| `sources/07-reface-manual/` | Yamaha reface CS/DX/CP/YC Owner's Manual (Yamaha support site), used by review 03 | Yamaha copyright |
| `sources/05-empirical-jrhodes-epmk1/` | <https://github.com/sfzinstruments/jlearman.jRhodes3d>, <https://github.com/MikeMorenoDSP/EP-MK1>, <https://mikemorenoaudio.wordpress.com/2019/01/10/ep-mk1-physical-modeled-electric-piano-vst/> | jRhodes and EP-MK1 state conflicting licences; blog pages are copyrighted |

## Rules

- **Code:** port only from the committed, licence-compatible code (Felucca GPL-3.0, STK MIT), keeping the
  notices. For everything else, take ideas and published facts only, never code.
- **Reference recordings:** used for analysis only. Commit only derived numbers (T60s, ratios), never the audio.
