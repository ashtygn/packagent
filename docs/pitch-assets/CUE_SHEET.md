# Video ⇄ deck lineup — cue sheet

The deck (`presentation.html`) is the timing ground truth. Its `SCENES` array
auto-advances at exactly these boundaries (script headers in `PITCH_SCRIPT.md` are
±3 s approximations — align to THESE numbers):

| Cut point | Deck time | Scene entered | VO line that must start just after the cut |
|---|---|---|---|
| start | 0:00 | S1 HOOK | "AI has automated almost every stage…" |
| 1 | **0:28** | S2 LOOP | "The agent is OpenAI's Codex — and it isn't running a script…" |
| 2 | **0:52** | S3 FIX | "Here's the reasoning. The agent looks at the curve…" |
| 3 | **1:27** | S4 REFEREE | "But here's what makes it trustworthy…" |
| 4 | **2:00** | S5 RECEIPTS | "And none of this is a demo mockup…" |
| 5 | **2:35** | S6 VISION | "Solve. Reason. Edit. Verify. Refuse." |
| end | **3:00** | hold on closer | — |

## The two silences (do not fill)

- **S1 tail (~0:22 → 0:28):** VO ends on "Watch." — red curve sits alone until the
  0:28 cut.
- **S3 tail (~1:20 → 1:27):** VO ends on "…*before* it ran the solver." — hold on
  the green curve until the 1:27 cut.

## Alignment workflow

1. Screen-record the deck exactly once: open `presentation.html`, F11, press
   SPACE, capture the full 180 s (the title holds until SPACE, so trim the
   recording to start at the SPACE press — that instant is 0:00).
2. In the editor, drop the VO track against it and slide it so the five lines
   above start 0.5–1.0 s AFTER their cut (visual leads voice).
3. In-scene sync points: S3 "watch the copper appear" must land as the plane
   animates in (~1:00–1:08 in-deck); S4's three REFUSED stamps land one per
   sentence of the refusal list.
4. If VO runs long in a scene, cut per the script's delivery notes (S1 clause,
   S5 last sentence) rather than shifting boundaries — the deck won't wait.

Silent companion piece: `slideshow.html` (auto-looping, no audio) shows every
plot/asset with its locked caption — for a booth screen or B-roll.
