#!/usr/bin/env bash
# Build kicad-footprints/: the sparse, pinned mirror of upstream KiCad footprints this library
# reads beside authored/. It is gitignored because this script rebuilds it identically. This
# script IS the recipe; README.md ("Rebuilding kicad-footprints/ from scratch") points here.
#
#   tools/fetch-kicad-footprints.sh
#
# It refuses if kicad-footprints/ already exists: it never deletes anything. To rebuild, delete
# that directory yourself first.
set -euo pipefail

LIBRARY_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MIRROR_DIRECTORY="$LIBRARY_ROOT/kicad-footprints"
PINNED_UPSTREAM_COMMIT="7ebfa6b23cc292a56f751b7b5f4a0e12eeef69dd"

# Widening the mirror means adding the library here; nothing else lists them.
SPARSE_LIBRARIES=(
    Button_Switch_THT.pretty Capacitor_SMD.pretty Capacitor_THT.pretty
    Connector_IDC.pretty Connector_JST.pretty Connector_PinHeader_2.54mm.pretty
    Connector_USB.pretty Diode_SMD.pretty Diode_THT.pretty
    LED_SMD.pretty LED_THT.pretty MountingHole.pretty
    Package_SO.pretty Package_TO_SOT_SMD.pretty Package_TO_SOT_THT.pretty
    Potentiometer_THT.pretty Resistor_SMD.pretty Resistor_THT.pretty
    Rotary_Encoder.pretty TerminalBlock.pretty TerminalBlock_Phoenix.pretty
    TestPoint.pretty
)

if [ -e "$MIRROR_DIRECTORY" ]; then
    echo "error: $MIRROR_DIRECTORY already exists — refusing to touch it (ಠ_ಠ)" >&2
    echo "       delete it yourself first if you mean to rebuild it." >&2
    exit 1
fi

git clone --filter=blob:none --no-checkout \
    https://github.com/KiCad/kicad-footprints.git "$MIRROR_DIRECTORY"
cd "$MIRROR_DIRECTORY"
git checkout --quiet "$PINNED_UPSTREAM_COMMIT"
git sparse-checkout init --no-cone
git sparse-checkout set --no-cone "${SPARSE_LIBRARIES[@]}" '/LICENSE.md' '/fp-lib-table' '/README.md'
git checkout --quiet

checked_out_libraries="$(ls -d *.pretty | wc -l | tr -d ' ')"
if [ "$checked_out_libraries" -ne "${#SPARSE_LIBRARIES[@]}" ]; then
    echo "error: asked for ${#SPARSE_LIBRARIES[@]} libraries, got $checked_out_libraries on disk" >&2
    exit 1
fi
echo "kicad-footprints/: $checked_out_libraries libraries at $PINNED_UPSTREAM_COMMIT (ﾉ◕ヮ◕)ﾉ"
