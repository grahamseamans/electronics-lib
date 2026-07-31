# electronics-lib — shared offline hardware assets

Shared, offline-first assets for the hardware projects in this workspace. Right now it
holds one thing: an **official KiCad footprint library**, sparse-fetched so that atopile
projects have a local, reproducible source of standard `.kicad_mod` footprints without
hitting EasyEDA/LCSC at build time.

```
electronics-lib/
├── README.md              ← you are here (versionable — committed)
├── .gitignore             ← ignores kicad-footprints/ (fetched content, not source)
└── kicad-footprints/      ← GITIGNORED. Reproducible from the commands below.
    ├── README.md          ← same reproduction commands (convenience copy, not committed)
    ├── LICENSE.md         ← CC-BY-SA 4.0 + KiCad library exception
    └── *.pretty/          ← the sparse-checked-out footprint libraries
```

## Why this exists

atopile atomic parts (`is_atomic_part<footprint="...">`) need a real `.kicad_mod` file on
disk. For jellybean packages (SOIC, SOT-23, TO-220-11, DO-41, radial caps, screw terminals,
tact switches, …) the authoritative geometry is the KiCad official footprint library. Rather
than fetch each one ad-hoc from EasyEDA, we keep a local pinned checkout and **vendor** copies
into each project.

## How projects consume it — VENDORING (important)

**Projects do not reference this directory at build time.** Each atopile project stays
self-contained: it carries its own copy of every footprint it uses inside its own
`parts/<PART>/` directory (mirroring how `hifi/ab-comparator/hardware/parts/` works). Those
vendored copies **are committed** with the project.

This shared library is only the **source** you copy *from* when adding a new part. Consequence:
a missing or unfetched `kicad-footprints/` never blocks building an existing project — it only
matters when you are creating a new part. Consumers today:

- `/workspace/acoustics/active-bass-trap/pcb/` — DIY AVAA cell board (atopile 0.15.7)
- `/workspace/hifi/ab-comparator/hardware/` — reference only; already fully vendored

### Vendoring recipe (legacy → modern format)

The KiCad official library ships **legacy** `(module …)` s-expression footprints with unquoted
pad numbers. atopile/faebryk consumes the **modern** `(footprint "lib:name" …)` format (quoted
pad numbers, quoted layers) — the same format `faebryk_convert` emits. So you cannot just `cp`
the file; convert it. We use [`kiutils`](https://pypi.org/project/kiutils/) (pure Python):

```python
from kiutils.footprint import Footprint
fp = Footprint.from_file("kicad-footprints/Package_SO.pretty/SOIC-8_3.9x4.9mm_P1.27mm.kicad_mod")
fp.libraryNickname = "Texas_Instruments_TL072CDR"   # = the part-dir name
fp.entryName       = "SOIC-8_TL072CDR"               # = the .ato footprint= basename
fp.models = []                                        # drop the ${KICAD..}/*.wrl 3D ref (not vendored)
fp.to_file(".../parts/Texas_Instruments_TL072CDR/SOIC-8_TL072CDR.kicad_mod")
```

Then verify the footprint pad count / pad numbers match the part's `.ato` `signal ~ pin N` map.
The internal `(footprint "<part-dir>:<basename>" …)` nickname must match the pattern the other
vendored parts use.

## Rebuilding kicad-footprints/ from scratch (it is GITIGNORED)

`kicad-footprints/` is intentionally **not committed** (thousands of files). It is fully
reproducible. Deleting it and running the following rebuilds it **identically** — pinned to a
commit so the geometry never drifts:

```bash
cd /workspace/electronics-lib
rm -rf kicad-footprints

# Blobless, no-checkout clone of the GitHub mirror of the official KiCad footprint repo
git clone --filter=blob:none --no-checkout \
  https://github.com/KiCad/kicad-footprints.git kicad-footprints
cd kicad-footprints

# Pin to the exact commit this library was built from (reproducibility)
git checkout 7ebfa6b23cc292a56f751b7b5f4a0e12eeef69dd

# Sparse-checkout ONLY the libraries we use (not the full ~1 GB repo)
git sparse-checkout init --no-cone
git sparse-checkout set --no-cone \
  Package_SO.pretty Package_TO_SOT_SMD.pretty Package_TO_SOT_THT.pretty \
  Capacitor_THT.pretty Diode_SMD.pretty Diode_THT.pretty LED_SMD.pretty LED_THT.pretty \
  Connector_JST.pretty Connector_IDC.pretty Connector_PinHeader_2.54mm.pretty \
  TerminalBlock.pretty TerminalBlock_Phoenix.pretty Button_Switch_THT.pretty \
  Potentiometer_THT.pretty Resistor_THT.pretty
git sparse-checkout add '/LICENSE.md' '/fp-lib-table' '/README.md'
git checkout
```

Result: 16 `*.pretty` libraries, ~23 MB. Add more `.pretty` dirs to the `set` list as new
package families are needed.

## Provenance & license

- **Source:** <https://github.com/KiCad/kicad-footprints> — the GitHub mirror of the official
  KiCad footprint library (upstream is GitLab: `gitlab.com/kicad/libraries/kicad-footprints`).
- **Pinned commit:** `7ebfa6b23cc292a56f751b7b5f4a0e12eeef69dd`
- **License:** Creative Commons **CC-BY-SA 4.0** *with the KiCad library exception* (full text
  in `kicad-footprints/LICENSE.md`). The exception explicitly waives copyleft for **designs that
  use** the footprints — so vendoring these `.kicad_mod` files into a PCB project imposes **no**
  license obligation on the project. (Redistributing the *library collection itself* in modified
  form would still be CC-BY-SA + attribution — but that is not what vendoring does.)
