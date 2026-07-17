# AIF (Artwork Interchange Format) — reference notes

Source (fetched 2026-07-17):
- https://www.artwork.com/package/aif/index.htm
- https://www.artwork.com/package/aif/what_is_in_aif.htm

AIF is a simple INI-style ASCII interchange format describing a die, or a BGA
bondshell including the die. Amkor Technology adopted it as its preferred die-exchange
format. A conformant parser **skips over any section it does not recognize** — the
extensibility guarantee we honor by preserving unknown sections losslessly.

## Sections
Required:
- `[DATABASE]` — file format version and database units.
- `[DIE]` — die outline dimensions and naming.
- `[PADS]` — pad-type/padstack definitions for die openings, bond fingers, ball pads.
- `[NETLIST]` — nets with associated die pads, fingers, balls, and coordinates.

Optional: `[RINGS]`, `[BONDABLE_RING_AREA]`, `[BGA]`, `[WIRE]`, `[FIDUCIALS]`,
`[DIE_LOGO]`, and vendor-specific sections.

## Interpretation notes (flagged)
The fetched pages describe the section catalog but not the exact per-row column layout
of `[NETLIST]`. `src/pkgtk/ingest/aif.py` therefore uses a documented, simplified
whitespace-delimited row layout for `[NETLIST]`:

    <net> <die_pad> <die_x> <die_y> <ball> <ball_x> <ball_y>

This is sufficient for the netlist-stage connectivity the verifier needs (die_pad and
ball tiers + the net between them). If a real AIF's NETLIST layout differs, adapt the
row parser; the section-skipping / extras-preservation contract is layout-independent.
See docs/PHASE-NOTES.md.
