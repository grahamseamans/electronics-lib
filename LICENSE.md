# Licences

Two files in `authored/` are copied from, or adapted from, third-party libraries licensed
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/legalcode). They are redistributed
here under that same licence, with attribution:

| file | source | licence | changes |
|---|---|---|---|
| `authored/Module.pretty/XIAO-RP2040-SMD.kicad_mod` | Seeed Studio, [OPL_Kicad_Library](https://github.com/Seeed-Studio/OPL_Kicad_Library), `Seeed Studio XIAO Series Library/XIAO-RP2040-SMD.kicad_mod` | CC BY-SA 4.0 (that repo's `LICENSE`, checked 2026-10-12 at b0035c5) | none, copied verbatim 2026-08-27 |
| `authored/Display.pretty/OLED_HS13L03W2C01_MidBoard_JST_SH_SM04B-SRSS-TB_Socket.kicad_mod` | KiCad libraries, [kicad-footprints](https://gitlab.com/kicad/libraries/kicad-footprints) 7ebfa6b, `Connector_JST.pretty/JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal.kicad_mod` | CC BY-SA 4.0 with the KiCad libraries exception (`kicad-footprints/LICENSE.md`) | socket translated by (0, −23.0), mounting pads renamed MP_1 / MP_2, screen geometry added (see the file's `descr`) |

`kicad-footprints/` itself is not in this repo (gitignored, rebuilt from the recipe in
`README.md`), so its licence travels with that checkout.

Everything else in this repo is authored here. No licence is granted for it yet.
