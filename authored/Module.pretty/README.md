# Module.pretty

`XIAO-RP2040-SMD.kicad_mod` — copied VERBATIM (2026-08-27) from Seeed's official library:
https://github.com/Seeed-Studio/OPL_Kicad_Library — `Seeed Studio XIAO Series Library/XIAO-RP2040-SMD.kicad_mod`.
Pin map from the same repo's `Seeed_Studio_XIAO_Series.kicad_sym`, symbol `XIAO-RP2040-SMD`:
1-11 = D0-D10, 12 = 3V3_OUT, 13 = GND, 14 = VBUS, 15 SWDIO, 16 SWCLK, 17 EN, 18 GND, 19 VIN, 20 GND.
Not upstream KiCad, so it lives here rather than in the kicad-footprints mirror.

`XIAO-RP2350-SMD.kicad_mod` — copied (2026-10-16) from the same repo at b0035c5,
`Seeed Studio XIAO Series Library/XIAO-RP2350-SMD.kicad_mod`, with only a `descr` line added (provenance,
origin, pin map). Pin map from `Seeed_Studio_XIAO_Series.kicad_sym`, symbol `XIAO-RP2350-SMD`:
1-11 = D0-D10, 12 = 3V3_OUT, 13 = GND, 14 = VBUS, 15-22 = D11-D18, 23 SWDIO, 24 SWDCLK, 25 EN, 26 GND,
27 BOOT, 28 3V3_OUT, 29 VBAT, 30 GND. Pads 15-30 are underside pads inside the module outline.
Pins 1-14 match the RP2040 electrically; the two footprints differ in orientation and origin (the
RP2350 one is centred on its pad field, USB-C toward +x; the RP2040 one is Seeed's uncentred frame).
Both sources are fetched by `tools/fetch-references.sh`.

Known problem (2026-10-16): `XIAO-RP2040-SMD.kicad_mod` is KiCad 10 format (`version 20260206`) and
kicad-cli 9.0.9 on this machine refuses to load it ("Unable to load library"). The RP2350 file is KiCad 9.
