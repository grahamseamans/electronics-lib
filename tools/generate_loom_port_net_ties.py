#!/usr/bin/env python3
"""Generate the LOOM PORT net-tie footprints into authored/NetTie.pretty/.

A loom PORT is the junction where a module's boundary net leaves the module. Per
/workspace/loom/docs/loom.md L59-69 it is a via-like thing that carries a DIFFERENT net
inside the module than outside it, and it is a TRUE FOOTPRINT taken from a small library of
sizes that a net's netclass rounds up into.

The only mechanism KiCad has for "one copper island, two nets" is a NET TIE: a footprint whose
pads are declared shorted by `(net_tie_pad_groups "1,2")`, so DRC accepts the deliberate
different-net copper contact instead of reporting a short. So each tier here is TWO round
THROUGH-HOLE via pads joined by a copper BRIDGE drawn inside the footprint:

    pad "1" = the INSIDE (module) terminal, at -y  (design-local: toward the module interior)
    pad "2" = the OUTSIDE (loom) terminal,  at +y  (design-local: toward the loom; KiCad y is
              DOWN, and loom.md puts the port row on the module's BOTTOM = MAX y)

Through-hole (not an F.Cu test point) because the loom is parallel wires that tunnel under one
another to reach ports — a via port lets a trace enter or leave on ANY copper layer.

GEOMETRY RULE (one home, here). The first cut butted the two vias together so their annular
rings OVERLAPPED, which is the usual net-tie trick. MEASURED with `kicad-cli pcb drc` 9.0.3 on a
real exported board, that construction fails: KiCad's HOLE CLEARANCE rule is hole-to-COPPER, not
hole-to-hole, so each drill sat 0.05 mm from the other terminal's annular ring against a 0.25 mm
constraint — 4 errors on a 4-port board. Overlap and that rule cannot both hold with round vias
(overlap needs `gap < pad`, the rule needs `gap >= clearance + drill/2 + pad/2`, and the second is
always the larger).

So the drills are SPACED to satisfy the rule and the copper is joined explicitly:

    centre_gap = HOLE_CLEARANCE_MM + drill_diameter/2 + pad_diameter/2
    bridge     = a pad-wide copper line between the two centres, on EVERY outer copper layer

`docs/loom.md` L63 asks for ports "spaced naturally in accordance with their netclass spacing",
which is exactly a clearance-derived gap rather than the tightest thing that still touches. Same
board, same DRC: 4 hole-clearance errors -> 0, with no new clearance or short violations.

The bridge is real plotted copper, so the tie is a solid electrical short on the fab board; the
`net_tie_pad_groups` token is what stops DRC calling that short a defect.

The COURTYARD (which is what loom reads as the part's keep-out body box) is the copper extent
plus a fixed margin.

Datum: the footprint origin is the TIE CENTRE — the midpoint of the two vias. That is the
port's anchor: the thing the annealer positions and the thing both routers aim at.

Run:  uv run python electronics-lib/tools/generate_loom_port_net_ties.py
"""

from __future__ import annotations

import os

# The two roots are named by KIND, never collapsed into one (electronics-lib ARCHITECTURE rule 1).
IRREPLACEABLE_AUTHORED_FOOTPRINT_ROOT = "/workspace/electronics-lib/authored"

OUTPUT_LIBRARY_DIRECTORY = os.path.join(IRREPLACEABLE_AUTHORED_FOOTPRINT_ROOT, "NetTie.pretty")

# KiCad's default HOLE CLEARANCE: the minimum distance from a drilled hole to any copper of a
# different net. Measured against `kicad-cli pcb drc` 9.0.3, which reports it as
# "board setup constraints hole clearance 0.2500 mm". This is hole-to-COPPER, which is why the two
# terminals cannot simply be butted together (see the module docstring).
HOLE_CLEARANCE_MM = 0.25

# Courtyard inflation (mm) beyond the copper extent.
COURTYARD_MARGIN_MM = 0.15
COURTYARD_STROKE_WIDTH_MM = 0.05
SILKSCREEN_STROKE_WIDTH_MM = 0.12

# The outer copper layers the bridge is drawn on. A through-hole barrel already ties every layer
# together, so bridging the two outer layers shorts the tie on any stackup.
OUTER_COPPER_LAYERS = ("F.Cu", "B.Cu")

# The pad numbers. Pad "1" is the INSIDE (module) terminal, pad "2" the OUTSIDE (loom) terminal.
# These same two numbers are loom-core's PORT_INSIDE_PAD_NUMBER / PORT_OUTSIDE_PAD_NUMBER.
INSIDE_PAD_NUMBER = "1"
OUTSIDE_PAD_NUMBER = "2"

# THE SHELF. Each entry is (entry_name, via_pad_diameter_mm, via_drill_diameter_mm). The sizes
# mirror the proven netclass via padstacks a board uses: signal 0.6/0.3, power 0.8/0.4,
# power_heavy 1.8/1.1. A net rounds UP into the smallest tier whose via meets its netclass.
PORT_TIER_SHELF = (
    ("loom_port_small", 0.6, 0.3),
    ("loom_port_medium", 0.8, 0.4),
    ("loom_port_large", 1.8, 1.1),
)


def tie_centre_gap_mm(via_pad_diameter_mm: float, via_drill_diameter_mm: float) -> float:
    """Centre-to-centre distance between the two vias: the TIGHTEST spacing at which each drill
    still clears the OTHER terminal's copper by `HOLE_CLEARANCE_MM`.

    This is the whole care point of the geometry, and it is the number `loom-core`'s
    `PortTier::resolve_footprint` re-derives so a tier that would DRC-error is refused at load."""
    return HOLE_CLEARANCE_MM + via_drill_diameter_mm / 2.0 + via_pad_diameter_mm / 2.0


def render_port_net_tie_footprint(
    entry_name: str, via_pad_diameter_mm: float, via_drill_diameter_mm: float
) -> str:
    """The `.kicad_mod` text for one shelf tier."""
    centre_gap_mm = tie_centre_gap_mm(via_pad_diameter_mm, via_drill_diameter_mm)
    hole_to_other_terminal_copper_mm = (
        centre_gap_mm - via_drill_diameter_mm / 2.0 - via_pad_diameter_mm / 2.0
    )
    inside_pad_centre_y_mm = -centre_gap_mm / 2.0
    outside_pad_centre_y_mm = centre_gap_mm / 2.0
    copper_half_height_mm = centre_gap_mm / 2.0 + via_pad_diameter_mm / 2.0
    copper_half_width_mm = via_pad_diameter_mm / 2.0
    courtyard_half_height_mm = copper_half_height_mm + COURTYARD_MARGIN_MM
    courtyard_half_width_mm = copper_half_width_mm + COURTYARD_MARGIN_MM

    def copper_bridge(
        bridge_width_mm: float, from_centre_y_mm: float, to_centre_y_mm: float
    ) -> str:
        """The copper that actually SHORTS the two terminals — a pad-wide line from one via centre
        to the other, drawn on every OUTER copper layer. It is real plotted copper, so the tie is a
        solid electrical joint on the fab board; `net_tie_pad_groups` is only what stops DRC calling
        that deliberate joint a defect. Without this the two spaced vias would be separate islands
        and the port would be an OPEN circuit."""
        return "\n".join(
            f'  (fp_line (start 0 {from_centre_y_mm:.6g}) (end 0 {to_centre_y_mm:.6g}) '
            f'(layer "{layer}") (stroke (width {bridge_width_mm:g}) (type solid)))'
            for layer in OUTER_COPPER_LAYERS
        )

    def box(layer: str, half_width_mm: float, half_height_mm: float, stroke_mm: float) -> str:
        corners = [
            (-half_width_mm, -half_height_mm),
            (half_width_mm, -half_height_mm),
            (half_width_mm, half_height_mm),
            (-half_width_mm, half_height_mm),
        ]
        lines = []
        for index, start in enumerate(corners):
            end = corners[(index + 1) % len(corners)]
            lines.append(
                f'  (fp_line (start {start[0]:.6g} {start[1]:.6g}) '
                f'(end {end[0]:.6g} {end[1]:.6g}) '
                f'(layer "{layer}") (stroke (width {stroke_mm:g}) (type solid)))'
            )
        return "\n".join(lines)

    return f"""(footprint "{entry_name}" (version 20240108) (generator loom) (layer "F.Cu")
  (descr "loom PORT net tie, {via_pad_diameter_mm:g} mm via / {via_drill_diameter_mm:g} mm drill. \
Source: /workspace/loom/docs/loom.md L59-69 (the ports section) — this is loom's own geometry, \
not a manufactured part, so its primary source is the spec that defines it. Two through-hole \
vias {centre_gap_mm:g} mm apart, joined by a {via_pad_diameter_mm:g} mm wide copper BRIDGE on \
every outer copper layer. That spacing is the tightest at which each drill still clears the other \
terminal's copper by KiCad's {HOLE_CLEARANCE_MM:g} mm hole clearance \
({hole_to_other_terminal_copper_mm:g} mm actual) — butting the vias until their rings overlapped \
instead is what KiCad 9 DRC rejects, and the two constraints cannot both hold with round vias. \
Pad 1 = INSIDE (module net, -y); pad 2 = OUTSIDE (loom net, +y); loom.md puts the port row on the \
module's bottom, and KiCad y is DOWN. Origin = the tie centre (the port anchor). Regenerate with \
electronics-lib/tools/generate_loom_port_net_ties.py.")
  (tags "loom port net tie via")
  (attr through_hole exclude_from_pos_files exclude_from_bom)
  (net_tie_pad_groups "{INSIDE_PAD_NUMBER},{OUTSIDE_PAD_NUMBER}")
  (fp_text reference "REF**" (at 0 {-courtyard_half_height_mm - 0.6:.6g}) (layer "F.SilkS")
    (effects (font (size 0.8 0.8) (thickness 0.12))))
  (fp_text value "{entry_name}" (at 0 {courtyard_half_height_mm + 0.6:.6g}) (layer "F.Fab")
    (effects (font (size 0.8 0.8) (thickness 0.12))))
{box("F.CrtYd", courtyard_half_width_mm, courtyard_half_height_mm, COURTYARD_STROKE_WIDTH_MM)}
{box("F.Fab", copper_half_width_mm, copper_half_height_mm, SILKSCREEN_STROKE_WIDTH_MM)}
{copper_bridge(via_pad_diameter_mm, inside_pad_centre_y_mm, outside_pad_centre_y_mm)}
  (pad "{INSIDE_PAD_NUMBER}" thru_hole circle (at 0 {inside_pad_centre_y_mm:.6g}) \
(size {via_pad_diameter_mm:g} {via_pad_diameter_mm:g}) (drill {via_drill_diameter_mm:g}) \
(layers "*.Cu" "*.Mask"))
  (pad "{OUTSIDE_PAD_NUMBER}" thru_hole circle (at 0 {outside_pad_centre_y_mm:.6g}) \
(size {via_pad_diameter_mm:g} {via_pad_diameter_mm:g}) (drill {via_drill_diameter_mm:g}) \
(layers "*.Cu" "*.Mask"))
)
"""


def main() -> None:
    os.makedirs(OUTPUT_LIBRARY_DIRECTORY, exist_ok=True)
    for entry_name, via_pad_diameter_mm, via_drill_diameter_mm in PORT_TIER_SHELF:
        text = render_port_net_tie_footprint(
            entry_name, via_pad_diameter_mm, via_drill_diameter_mm
        )
        output_path = os.path.join(OUTPUT_LIBRARY_DIRECTORY, f"{entry_name}.kicad_mod")
        with open(output_path, "w", encoding="utf-8") as handle:
            handle.write(text)
        print(f"wrote {output_path}")


if __name__ == "__main__":
    main()
