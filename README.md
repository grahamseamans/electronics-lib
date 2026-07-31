# electronics-lib — the workspace's footprint library

The one place `.kicad_mod` footprints live. Projects **reference** it and **add to** it;
they do not each go and find their own. Per `/workspace/CLAUDE.md`:

> use the electronics-lib for footprints. if it doesnt have something that you need get
> it and add it to there. also normalise the part so that it's not offset

`ARCHITECTURE/README.md` is the spec this directory has to match. If this file and that
one disagree, that one is right.

```
electronics-lib/
├── ARCHITECTURE/README.md     the spec: partitions, contract, rules
├── README.md                  you are here
├── .gitignore                 ignores kicad-footprints/ and nothing else that matters
├── authored/                  TRACKED. Footprints drawn here. Irreplaceable.
│   └── Rotary_Encoder.pretty/
│       └── RotaryEncoder_Bourns_PEC11R-4215F-S0024_Vertical_ThreadedM7Bushing.kicad_mod
├── kicad-footprints/          GITIGNORED. Pinned upstream mirror. Reproducible.
│   ├── LICENSE.md   README.md   fp-lib-table
│   └── *.pretty/              21 libraries, 3,117 footprints, 21 MB
└── tools/
    └── pdf_vector_probe.py    UNUSED - see "Tools" below
```

---

## The two trees, and why they are versioned differently

They look alike. They are not alike. The difference is **what happens if you delete
them**, and that is the only question worth asking about a directory of assets.

| | `authored/` | `kicad-footprints/` |
|---|---|---|
| Origin | drawn here, from a datasheet | fetched from upstream KiCad |
| If deleted | **work is gone** | re-run the recipe below |
| Git | **tracked and committed** | gitignored |
| Editable | yes, that is the point | **never** — read-only mirror |
| Normalised to functional datum | **yes, on ingest** | no, upstream's choice stands |

**This split is not cosmetic — it is a repair.** Until 2026-07-31 the single authored
footprint in this workspace, the Bourns PEC11R threaded encoder, was an untracked file
sitting inside `kicad-footprints/`. That directory is gitignored, and its own README
told you it was disposable and could be rebuilt identically. It could not: the rebuild
recipe starts with `rm -rf`. One `.kicad_mod` derived pad-by-pad from a manufacturer
drawing was one documented maintenance step away from being deleted with no copy in any
repository. It is now at `authored/Rotary_Encoder.pretty/` and committed.

The invariant that keeps this from recurring is mechanical. Check it any time:

```bash
git -C kicad-footprints status --porcelain    # MUST print nothing
```

Non-empty output means something of ours is hiding in the disposable tree. Move it to
`authored/`. As of the pinned commit the mirror is byte-pristine, including its own
upstream `README.md` — this file is the only documentation of the library, so there is
one copy of the rebuild recipe rather than two that can drift apart.

---

## Ingest rule: normalise to the FUNCTIONAL DATUM

**A footprint's origin is arbitrary. Fix it once, here, on the way in — never at each
call site.**

Every footprint entering `authored/` has its origin placed on the feature the
mechanical design is positioned against:

| Part kind | Origin goes on |
|---|---|
| rotary encoder, potentiometer | the **shaft axis** |
| pushbutton, tact switch | the **plunger axis** |
| LED | the **emitting surface centre** |
| connector | the **mating face / mating axis** |
| screw, standoff, mounting hole | the **hole axis** |

The Bourns encoder is the worked example. Its origin is on the shaft axis; the Alps
part it replaced put the origin 7.5, 2.5 mm away on the pad field. With the shaft on
the origin, the panel aperture centre, the M7 nut clearance and the shaft-height
elevation are all read straight off the placement coordinate, and the consumer's
body-centre offset for that entry is `(0, 0)`.

The failure mode this prevents: with an arbitrary origin, every consumer carries its
own correction offset, and the first time two consumers carry *different* offsets for
the same part, that part has two geometries and one of them is wrong. Upstream
footprints in `kicad-footprints/` are not normalised and **must not be edited** to make
them so — a consumer that needs an upstream part's datum records the offset once, in
its own code, next to the entry.

Alongside the origin, an authored footprint carries its provenance in its own `descr`:
the manufacturer, the datasheet URL, the revision, and the page number of the
recommended-layout drawing the pads came from. "Adapted from a similar part" is not a
provenance.

---

## Who consumes this library

Verified 2026-07-31 by grepping every top-level directory in `/workspace` and by
checking the `(generator …)` tag on all 231 `.kicad_mod` files outside this repo.

**Build-time / runtime readers — resolve paths into this directory when they run:**

- **`/workspace/press`** — the only one. Two modules under `press/spike/`:
  - `spike_stack_mechanical_data.py` defines both roots as separate named constants,
    `REPRODUCIBLE_UPSTREAM_KICAD_MIRROR_ROOT` and
    `IRREPLACEABLE_AUTHORED_FOOTPRINT_ROOT`, and maps **10** entries onto them in
    `FOOTPRINT_SOURCE_PATH_BY_ENTRY_NAME`: **6** from the mirror (`MountingHole`,
    `LED_SMD`, `Package_SO`, `Resistor_SMD`, `Capacitor_SMD`,
    `Connector_PinHeader_2.54mm`), **1** from `authored/` (the Bourns encoder),
    **2** deliberately project-local and saying so at the path (a VBUS-bridged USB-C
    receptacle and a panel support post, both under `press/spike/footprints/`), and
    **1** that resolves into `/workspace/acoustics/active-bass-trap/pcb/parts/` — see
    "Known gaps".
  - `spike_board_build.py` imports the mirror root from the module above (it used to
    keep a second literal of its own).
  - Runtime note: the spike modules need **kiutils**, which lives in
    `press/spike/.venv`, *not* in `press/.venv`.

**Authoring-time vendorer — reads this library, writes a converted copy into itself:**

- **`/workspace/synth/nodalred-controller`** — `hardware/tools/vendor_footprints.py`
  is the only committed, working vendoring tool in the workspace. It reads 6 upstream
  footprints from `kicad-footprints/`, converts legacy `(module …)` to the modern
  `(footprint "lib:name" …)` form that atopile/faebryk 0.15.7 requires, renames the
  library nickname and entry, drops the 3D `(model …)` refs, then **re-reads what it
  wrote and asserts the pad-name set**. No fallbacks; a mismatch raises. It is not
  invoked by any build. Its docstring's `pip install kiutils` recipe needs network;
  offline, run it with `/workspace/press/spike/.venv/bin/python`.

**Historic vendorer — copied out of here once, no longer reads it:**

- **`/workspace/acoustics/active-bass-trap`** — 20 footprints under `pcb/parts/`
  tagged `(generator "kicad-footprints-vendored")`, taken from this mirror at the
  pinned commit and renamed per part. Done ad hoc; no vendoring script was kept. Its
  other 79 footprints came from the atopile/EasyEDA picker, not from here.

**Not a consumer, despite what this file used to claim:**

- **`/workspace/hifi/ab-comparator`** — has **never** consumed this library. A grep for
  `electronics-lib` across the whole project returns nothing. Its 118 footprints are
  107 `faebryk_convert` (EasyEDA/LCSC) plus 11 hand-written. Beware one trap: two of
  its files are named `SOIC-8_3.9x4.9mm_P1.27mm.kicad_mod`, the exact upstream KLC
  name, but they are hand-written with different pad geometry. Name collision only.
- Nothing in `loom`, `studio`, `daw`, `hilo-control`, `controller-system` or `archive`
  reads or vendors from here. No `fp-lib-table`, `.kicad_pro` or `.kicad_pcb` anywhere
  in the workspace points into this directory.

---

## Adding a part

1. **Look in the mirror first.** 3,117 footprints across 21 libraries; the part is
   often already there. If it is, reference it — do not copy it.
2. **If it is not there, author it into `authored/<Category>.pretty/`**, using KiCad's
   category name so the two trees compose. Pads come from the manufacturer's own
   recommended-layout drawing, not from an adjacent part.
3. **Normalise the origin to the functional datum** (table above) before saving.
4. **Write the provenance into `descr`**: manufacturer, datasheet URL, revision, page.
5. **Commit it here.** The point of `authored/` is that it is under version control.
6. **Point the project at it.** Two separate named constants, one per root; a missing
   footprint raises with the absolute path. See `ARCHITECTURE/README.md` for the
   contract.

Widening the mirror instead (a new upstream `.pretty`) means adding the directory to
the `git sparse-checkout set` list below **and** to the recipe in this file, in the
same change. The recipe going stale is how it came to claim 16 when 21 were on disk.

---

## Rebuilding `kicad-footprints/` from scratch

`kicad-footprints/` is gitignored and fully reproducible. This recipe rebuilds it
**identically**, pinned so the geometry never drifts.

> **Corrected 2026-07-31.** The recipe that used to be here — in this file *and* in a
> second copy inside the mirror — listed **16** `.pretty` directories and claimed
> "Result: 16 libraries, ~23 MB". There are **21**. Running the old recipe would have
> silently deleted 5 libraries and **379 upstream footprints** (380 counting the
> authored Bourns encoder that was living among them): `Rotary_Encoder` (8),
> `Resistor_SMD` (62), `Capacitor_SMD` (100), `MountingHole` (166), `Connector_USB`
> (43). Three of those five — `Resistor_SMD`, `Capacitor_SMD`, `MountingHole` — are
> among the 6 upstream libraries `press` resolves at runtime; `Rotary_Encoder` is where
> the authored Bourns encoder was living; `Connector_USB` is what press's vendored
> USB-C receptacle was derived from. The list below is verified against
> `git sparse-checkout list` and against what is actually on disk; the two agree
> exactly.

```bash
cd /workspace/electronics-lib
rm -rf kicad-footprints

# Blobless, no-checkout clone of the GitHub mirror of the official KiCad library
git clone --filter=blob:none --no-checkout \
  https://github.com/KiCad/kicad-footprints.git kicad-footprints
cd kicad-footprints

# Pin to the exact commit this library is built from (reproducibility)
git checkout 7ebfa6b23cc292a56f751b7b5f4a0e12eeef69dd

# Sparse-checkout ONLY the 21 libraries we use (not the full ~1 GB repo)
git sparse-checkout init --no-cone
git sparse-checkout set --no-cone \
  Button_Switch_THT.pretty Capacitor_SMD.pretty Capacitor_THT.pretty \
  Connector_IDC.pretty Connector_JST.pretty Connector_PinHeader_2.54mm.pretty \
  Connector_USB.pretty Diode_SMD.pretty Diode_THT.pretty \
  LED_SMD.pretty LED_THT.pretty MountingHole.pretty \
  Package_SO.pretty Package_TO_SOT_SMD.pretty Package_TO_SOT_THT.pretty \
  Potentiometer_THT.pretty Resistor_SMD.pretty Resistor_THT.pretty \
  Rotary_Encoder.pretty TerminalBlock.pretty TerminalBlock_Phoenix.pretty
git sparse-checkout add '/LICENSE.md' '/fp-lib-table' '/README.md'
git checkout
```

**Result: 21 `*.pretty` libraries, 3,117 footprints, 21 MB working tree (+3.8 MB
`.git`).** Verify:

```bash
cd /workspace/electronics-lib/kicad-footprints
diff <(git sparse-checkout list | grep '\.pretty$' | sort) <(ls -d *.pretty | sort)
find . -name '*.kicad_mod' -not -path './.git/*' | wc -l    # 3117
git status --porcelain                                       # empty
```

### The 21 libraries

| Library (`.pretty`) | count | used for |
|---|---:|---|
| Button_Switch_THT | 87 | 6 mm tactile pushbutton |
| Capacitor_SMD | 100 | 0402 / 0603 decoupling — **read live by press** |
| Capacitor_THT | 375 | CP_Radial (4700 µF electrolytic) |
| Connector_IDC | 161 | 2x13 box header (Nucleo ribbon) |
| Connector_JST | 508 | JST PH B2B-PH-K (mic headers) |
| Connector_PinHeader_2.54mm | 278 | generic 2.54 mm headers — **read live by press** |
| Connector_USB | 43 | USB-C receptacle (HRO TYPE-C-31-M-12) |
| Diode_SMD | 73 | SOD-123 (Zener, 1N4148W) |
| Diode_THT | 108 | DO-41 (UF4007) |
| LED_SMD | 68 | 0805 indicator, SK6805 EC15 — **read live by press** |
| LED_THT | 82 | THT indicator LEDs |
| MountingHole | 166 | M3 pads and plain holes — **read live by press** |
| Package_SO | 303 | SOIC-8/14/16 (TL072, NE555, LM339, 74HCT) — **read live by press** |
| Package_TO_SOT_SMD | 128 | SOT-23 (2N7002, MMBT3904) |
| Package_TO_SOT_THT | 236 | TO-220-11 staggered (LM3886TF) |
| Potentiometer_THT | 104 | Bourns 3296W trimmer |
| Resistor_SMD | 62 | 0603, R_Array_Convex_4x0603 — **read live by press** |
| Resistor_THT | 104 | axial power resistor (Stackpole MR5, 5 W) |
| Rotary_Encoder | 8 | Alps EC11E/EC12E only — **no threaded part exists upstream**, which is why the Bourns is in `authored/` |
| TerminalBlock | 9 | 5.08 mm screw terminals |
| TerminalBlock_Phoenix | 114 | Phoenix screw terminals |

---

## Tools

- **`tools/pdf_vector_probe.py` — UNUSED.** Nothing in the workspace calls it. It reads
  a datasheet PDF's content streams and transforms the path operators into page space,
  which is how the Bourns drawing was cross-read against its own rendered image. Kept
  deliberately, as a known quantity, not because anything depends on it.

The only working vendoring tool lives in the consuming project, not here:
`/workspace/synth/nodalred-controller/hardware/tools/vendor_footprints.py`. If a second
project needs to vendor, promote that script into `tools/` rather than copying it.

---

## Known gaps

- **`press` reads one footprint out of `acoustics`, not out of this library**:
  `SW_TACT_6MM_THT` resolves to
  `/workspace/acoustics/active-bass-trap/pcb/parts/Generic_Tactile_Pushbutton/`. That
  copy has its pads renumbered `1,1,2,2 → 1,2,3,4` relative to upstream
  (`acoustics/.../pcb/SHORTCUTS.md §B`), so it is not interchangeable with
  `Button_Switch_THT.pretty/SW_PUSH_6mm`. A cross-project footprint dependency is a
  contract violation and the entry is under separate review; it is untouched here.
- **`acoustics`, `synth` and `hifi` hold vendored copies** predating the
  reference-and-add doctrine. Migrating them is a separate, deliberate decision.
- **No `.kicad_sym` symbols and no `.step` models** are mirrored — footprints only.

---

## Provenance & license of the mirror

- **Source:** <https://github.com/KiCad/kicad-footprints> — the GitHub mirror of the
  official KiCad footprint library (upstream is GitLab:
  `gitlab.com/kicad/libraries/kicad-footprints`).
- **Pinned commit:** `7ebfa6b23cc292a56f751b7b5f4a0e12eeef69dd`
- **License:** Creative Commons **CC-BY-SA 4.0** *with the KiCad library exception*
  (full text in `kicad-footprints/LICENSE.md`). The exception explicitly waives copyleft
  for **designs that use** the footprints, so referencing or vendoring these
  `.kicad_mod` files into a PCB project imposes **no** license obligation on the
  project. Redistributing the *library collection itself* in modified form would still
  be CC-BY-SA plus attribution — which is another reason the mirror stays pristine and
  our own work lives in `authored/`.
- **`authored/` is ours**, and is not derived from the KiCad library. It carries no
  CC-BY-SA obligation.
