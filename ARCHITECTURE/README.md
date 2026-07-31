# electronics-lib — architecture

**This folder is the spec the content has to match.** If a comment, a filename or a
README sentence disagrees with this file, this file is right and the other thing is
wrong. Read it before adding a part or writing a tool that reads from here.

`electronics-lib` is the workspace's single source of `.kicad_mod` footprints. It is
not a project and it builds nothing. Its whole job is to answer one question — *where
does the authoritative footprint for this part live* — with exactly one answer.

---

## The partitions

Three, and the split is by **what would happen if the directory were deleted**. That
is the only axis that matters here, because getting it wrong is what has already cost
this workspace a near-loss of original work.

```
electronics-lib/
├── authored/<Category>.pretty/    IRREPLACEABLE   -> tracked in git
├── kicad-footprints/              REPRODUCIBLE    -> gitignored, pinned, pristine
└── tools/                         CODE            -> tracked in git
```

### 1. `authored/` — footprints this workspace drew

**Pattern: one file per part, tracked, with its provenance inside it.**

* Directory naming mirrors KiCad's own `<Category>.pretty` so the two trees compose
  and a reader never has to learn a second taxonomy.
* Every file's `descr` field names the **primary source** it was drawn from — a
  manufacturer datasheet with a URL and a revision, and the page number of the
  recommended-layout drawing. "Adapted from a similar part" is not a source.
* Every file is **normalised to the part's functional datum** before it lands here.
  See the rule below; it is not optional and it is not a call-site concern.
* Deleting a file here destroys work. This partition is committed, always.

### 2. `kicad-footprints/` — the upstream mirror

**Pattern: a pinned, pristine, gitignored sparse checkout. Read-only, forever.**

* It is a sparse checkout of `github.com/KiCad/kicad-footprints` pinned to one commit,
  rebuildable byte-for-byte from the recipe in `../README.md`.
* **Nothing in this tree may ever be edited, added to, or renamed.** The invariant is
  mechanical and you can check it:

  ```bash
  git -C kicad-footprints status --porcelain   # MUST print nothing
  ```

  Non-empty output means something irreplaceable is hiding in a directory whose
  documented maintenance procedure is `rm -rf`. Move it to `authored/` immediately.
* Consequence: this partition needs no backup, no review and no version control of its
  own. That is the entire benefit of keeping it separate, and it only holds while the
  invariant above holds.

### 3. `tools/` — code that operates on footprints

**Pattern: standalone Python scripts, no shared package, no implicit state.**

Each script takes explicit paths and raises on anything it does not understand. There
is no config file and no discovery: if a tool needs a path, it is an argument or a
named module-level constant, never a search.

---

## The contract with consuming projects

A consuming project resolves a footprint through **one of two roots, named
separately**, and the names must make the distinction visible at the call site:

| Root | Kind | If it vanishes |
|---|---|---|
| `electronics-lib/authored/` | irreplaceable | work is lost |
| `electronics-lib/kicad-footprints/` | reproducible | re-run the recipe |

Rules on the contract:

1. **Two constants, never one.** A consumer must not define a single
   `FOOTPRINT_ROOT` that both trees hang off. Collapsing them is precisely the mistake
   that hid an authored file inside a disposable mirror for a day.
2. **Name the constants by kind, not by convenience.** `press` uses
   `IRREPLACEABLE_AUTHORED_FOOTPRINT_ROOT` and
   `REPRODUCIBLE_UPSTREAM_KICAD_MIRROR_ROOT`. Long and specific beats short and vague.
3. **A missing footprint raises.** No default footprint, no nearest match, no skip, no
   warning-and-continue. A `FileNotFoundError` naming the absolute path is the correct
   and only behaviour.
4. **Reference first; vendor only with a stated reason.** Per `/workspace/CLAUDE.md`,
   projects reference this library and add to it. A project that instead keeps its own
   copy must say *in the code, at the path* why that copy diverges from the library —
   "this one carries a board-specific modification" is a reason; "for convenience" is
   not.
5. **Adding a part is a commit here, not a copy there.** If a project needs a
   footprint the library does not have, it is authored into `authored/` and committed,
   and the project points at it. It does not get authored into the project.

---

## The ingest rule: normalise to the functional datum

**A footprint's origin is arbitrary until someone decides what it means. Decide once,
here, at ingest — never at each call site.**

The origin of every footprint entering `authored/` is placed on the part's
**functional datum**: the feature that the rest of the mechanical design is positioned
against.

| Part kind | Functional datum |
|---|---|
| rotary encoder, potentiometer | shaft axis |
| pushbutton, tact switch | plunger axis |
| LED | emitting surface centre |
| connector | mating face / mating axis |
| screw / mounting hole | hole axis |

Why this is a rule and not a preference: an origin on the functional datum makes the
panel aperture, the keepout, the nut clearance and the elevation all readable straight
off the placement coordinate. An origin on pad 1 — which is what many upstream
footprints use — forces every consumer to carry its own correction offset, and the
moment two consumers carry different offsets for the same part, the part has two
geometries.

Upstream footprints in `kicad-footprints/` are **not** normalised and must not be
edited to make them so (partition 2 is read-only). A consumer that needs an upstream
part's datum records the offset in its own code, once, next to the entry.

---

## Violations, current

* `tools/pdf_vector_probe.py` has no caller anywhere in the workspace. It is kept
  deliberately — it is how datasheet linework was cross-read — but an uncalled tool is
  a partition-3 member with no contract. Either give it one or delete it.
* `acoustics/`, `synth/` and `hifi/` hold vendored footprint copies predating rule 4.
  Migrating them is a separate, deliberate decision and is not blocked on anything
  here.
