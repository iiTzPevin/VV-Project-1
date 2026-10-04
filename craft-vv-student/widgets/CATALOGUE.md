# Interactive concept widgets — the catalogue

One misconception per widget, aimed at that week's `reframe` box. Slugs are
frozen here so a lecture deck can cite `\trybox{slug}{...}` before the widget
exists — `scripts/check_refs.py` fails the build once a deck cites a slug with
no file behind it.

## Design rules

1. **One misconception per widget.** Not "a FIFO visualizer" — the specific
   wrong model the week's reframe box names.
2. **Predict, then reveal.** The controls stay locked until the student commits
   to an answer. Mirrors the deck's *Predict First* moment.
3. **Every widget can reach the state that contradicts the naive model.** If it
   cannot show you being wrong, it is decoration.
4. **No login, no score, no record.** `localStorage` only for remembering a
   configuration.
5. **`?present=1`** enlarges type and hides prose, so one file is both the
   projected visual and the study tool.
6. **Self-contained.** Vanilla JS, inline CSS, no CDN, no build step. Works from
   the student distribution with no network.

## The set

| Slug | Wk | Misconception it breaks | Tier |
|------|---:|-------------------------|:----:|
| `observability` | 1 | "If it's wrong, a test will fail." Plant a bug at a node; watch it stay invisible at every output until an observation point is added. | 2 |
| `spec-ambiguity` | 2 | "The spec says what it means." Highlight a phrase; see two conforming implementations produce different outputs. | 2 |
| `delta-sampler` | 3 | "Sequential Python is sequential hardware time." Drag the sample point across a clock edge; compare `RisingEdge`, `ReadOnly`, bare `Timer`. | **1** |
| `scoreboard-race` | 4 | "A bug shows up immediately." Plant the silent-drop-when-full bug; count cycles until the reference queue diverges. | 2 |
| `constraint-sandbox` | 5 | "I wrote the constraint, so the stimulus is shaped." Per-phase drift vs. histogram vs. seed sweep. | **1** · shipped |
| `coverage-closure` | 6 | "100% coverage means correct." Watch bins fill, then find the planted bug inside a bin already covered. | **1** |
| `sva-vacuity` | 7 | "It passed, so the property holds." Scrub a waveform; see where the antecedent never fires and the pass is vacuous. | **1** |
| `bmc-induction` | 8 | "I ran it a million cycles." Bad state at depth 9: k=8 says PASS, k=9 finds it. Then a true-but-not-inductive property, and the strengthening invariant. | **1** |
| `uvm-phases` | 9 | "UVM is a big new framework." Build in the wrong phase or leave an analysis port unconnected, and watch what happens. | 2 |
| `reg-policy` | 10 | "Registers are just more signals." Exercise RO / RW / W1C / locked; flip the policy mutant and watch a locked register accept a write. | 2 |
| `cdc-hazard` | 10 | "Simulation would have caught it." A domain crossing with no synchronizer; add two flops and watch it resolve. | 3 |
| `survivors` | 3–13 | "A high score means a good suite." Per-mutant: which test catches it, at which cycle, and what condition would make a survivor observable. | 2 |
| `trigger-space` | 8 · capstone | "Random testing will find it eventually." The trigger as a vanishing region of the reachable state space. | 2 |
| `found-total` | all | — Score-to-grade calculator under the course threshold. Removes a recurring question. | 3 |

**Tier 1** are the five concepts that are hardest to convey statically and where
a widget earns the most. Build those first.

## Serving them

Three paths, one file:

- **Portal** — `web/app.py` serves `/widgets/<slug>`; this is what the QR code on
  the slide points at. Set `\widgetbase` in `common/craftbeamer.sty` to your host.
- **Distribution** — the whole directory ships in the student packet; students
  open `web/widgets/<slug>.html` from disk with no network.
- **Canvas** — upload the file; it needs nothing external.
