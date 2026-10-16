#!/usr/bin/env bash
# Fill references/: the primary sources the authored/ footprints and the upstream-datum offsets were
# drawn from. references/ is gitignored (fetched content, not ours); THIS SCRIPT is the record of what
# was fetched and from where, and re-running it rebuilds the folder.
#
#   tools/fetch-references.sh            # fetches anything missing; never overwrites a file
#
# Each line: <subdirectory> <file name> <URL>. A non-200 answer, an HTML page where a PDF/DXF/kicad
# file was expected, or an empty file stops the script with the URL that failed (ಠ_ಠ).
set -euo pipefail

LIBRARY_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REFERENCES_DIRECTORY="$LIBRARY_ROOT/references"
BROWSER_USER_AGENT="Mozilla/5.0 (X11; Linux x86_64)"
SEEED_OPL_PINNED_COMMIT="b0035c51eb0348bb3e165fdb2f2765fa3d1d17bd"
SEEED_XIAO="https://raw.githubusercontent.com/Seeed-Studio/OPL_Kicad_Library/$SEEED_OPL_PINNED_COMMIT/Seeed%20Studio%20XIAO%20Series%20Library"

SOURCES=(
    # XIAO RP2350: Module.pretty/XIAO-RP2350-SMD (copied) and its pin map (the symbol)
    "seeed-xiao XIAO-RP2350-SMD.kicad_mod $SEEED_XIAO/XIAO-RP2350-SMD.kicad_mod"
    "seeed-xiao Seeed_Studio_XIAO_Series.kicad_sym $SEEED_XIAO/Seeed_Studio_XIAO_Series.kicad_sym"
    # Neutrik PCB XLRs: checks the upstream Connector_Audio footprints and gives loom's datum offsets
    "neutrik st-nc3fah2.pdf https://www.neutrik.com/media/8292/download/st-nc3fah2.PDF?v=2"
    "neutrik st-nc3fah2.dxf https://www.neutrik.com/media/11729/download/st-nc3fah2.dxf?v=2"
    "neutrik nc3mah-2.pdf https://www.neutrik.com/media/8308/download/nc3mah-2.pdf?v=1"
    "neutrik nc3mah-3.dxf https://www.neutrik.com/media/11746/download/nc3mah-3.dxf?v=1"
    # class-D output inductor (Inductor_THT.pretty/L_Coilcraft_MA5172-AE_...)
    "coilcraft ma5172.pdf https://www.coilcraft.com/pdfs/ma5172.pdf"
    # Faston tab (Connector.pretty/Faston_Keystone_1287_...): Keystone catalog page M65p59;
    # keyelco.com answers 403 to scripts, so this is a distributor's copy of Keystone's own page
    "keystone keystone-catalog-M65p59-pc-quick-fit-male-tabs.pdf https://cdn.components.ru/media/PDF/412259.pdf"
    # TI: the ICs whose upstream footprints were checked against TI's land patterns, and the
    # TPA3255 output-filter sources (SLAA788A Table 1, TPA3255EVM guide and BOM)
    "ti tpa3255.pdf https://www.ti.com/lit/ds/symlink/tpa3255.pdf"
    "ti dir9001.pdf https://www.ti.com/lit/ds/symlink/dir9001.pdf"
    "ti thvd1450.pdf https://www.ti.com/lit/ds/symlink/thvd1450.pdf"
    "ti pcm5102a.pdf https://www.ti.com/lit/ds/symlink/pcm5102a.pdf"
    "ti slaa788a.pdf https://www.ti.com/lit/pdf/slaa788"
    "ti slou441-tpa3255evm-users-guide.pdf https://www.ti.com/lit/pdf/slou441"
    "ti slar130-tpa3255evm-bom.pdf https://www.ti.com/lit/pdf/slar130"
)

for source in "${SOURCES[@]}"; do
    read -r subdirectory file_name url <<<"$source"
    destination="$REFERENCES_DIRECTORY/$subdirectory/$file_name"
    if [ -s "$destination" ]; then continue; fi
    mkdir -p "$REFERENCES_DIRECTORY/$subdirectory"
    partial="$destination.partial"
    http_status="$(curl -sS -L -A "$BROWSER_USER_AGENT" -o "$partial" -w '%{http_code}' "$url")"
    if [ "$http_status" != "200" ] || [ ! -s "$partial" ]; then
        echo "error: $url answered HTTP $http_status (or nothing) (ಠ_ಠ)" >&2; rm -f "$partial"; exit 1
    fi
    if head -c 512 "$partial" | grep -qi '<html\|<!doctype html'; then
        echo "error: $url returned an HTML page, not $file_name (ಠ_ಠ)" >&2; rm -f "$partial"; exit 1
    fi
    mv "$partial" "$destination"
    echo "fetched $subdirectory/$file_name"
done
echo "references/: ${#SOURCES[@]} sources present (ﾉ◕ヮ◕)ﾉ"
