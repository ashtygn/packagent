# 3-Minute Pitch — video voiceover script

Deck: `C:\scratch\open-demo\stage\pitch\presentation.html` (press SPACE to play, F11
fullscreen, screen-record). The deck auto-advances on a 180 s timer; the narration
below is timed scene-by-scene to match. Target pace ~145 wpm. Practice once against
the progress bar.

Tone: calm, certain, a little bit awed. You are not selling — you are showing
something that shouldn't exist yet and does. Let the two silences land.

**Two ways to open** (pick per format):
- **3-min video (default):** roll straight into Scene 1 below — the tight hook.
- **Live talk / longer cut:** deliver the full INTRO (appendix at the bottom) as a
  spoken lead-in *before* rolling the video, then start the video at Scene 1.

---

### SCENE 1 — HOOK  (0:00–0:30)

*(opens on the package — the ball map — then the failing |Z| curve)*

> "AI has automated almost every stage of chip design — RTL, verification, layout,
> timing. Almost every stage. Packaging is the one it skipped — right when chiplets
> made packaging the whole ballgame. So we built packagent: a package-design verifier
> so trustworthy you can put an AI on top of it — one that reads the field solver,
> fixes the package, and refuses to ship when the fix isn't real. Watch."

*(let the red curve sit for a beat before Scene 2)*

---

### SCENE 2 — THE LOOP  (0:25–0:50)

> "It isn't running a script. It's closing a loop that, until now, only a human
> could close. It solves the package in Ansys SIwave — a commercial field solver.
> It reads the physics. It edits the actual Cadence design database. It re-solves.
> And then — this is the important part — a referee decides whether the fix is real.
> Not the agent. The referee."

---

### SCENE 3 — THE FIX  (0:52–1:27)  ← the peak, give it air

*(show the package geometry: bare via ring → the agent's copper plane appears under it)*

> "Here's the reasoning. The agent looks at the curve and sees a plate capacitance
> of under one picofarad — which means this design has no working reference planes
> at all. So it computes the size of the planes it needs, and — watch the copper
> appear — it draws them, right here, into the package. Headless, inside Allegro,
> and every single edit is independently verified in a fresh session before anything
> is trusted.
>
> Then it re-solves.
>
> The resonance collapses. Eighteen hundred ohms, down to seventy-four — a
> ninety-six percent drop. And the plane capacitance? Sixty-one picofarads — which
> the agent predicted, in writing, *before* it ran the solver."

*(pause on the green curve)*

---

### SCENE 4 — THE REFEREE  (1:25–2:00)

> "But here's what makes it trustworthy. Give it a second, conflicting requirement,
> and it doesn't fake a win. It tries three different fixes — and the referee
> *refuses* all three, because each one trades one spec away to satisfy another.
>
> Three plausible fixes. Three justified refusals. Nothing shipped. It reports the
> conflict, with the evidence, and stops. An agent you can't bluff is the only kind
> of agent you can put near a tape-out."

---

### SCENE 5 — THE RECEIPTS  (2:00–2:35)

> "And none of this is a demo mockup. Twenty-six solver-signed result files on disk.
> Runs that reproduce bit-for-bit. A robustness matrix that passes four out of four
> on physics and eight out of eight on error injection. And our own open-source
> physics oracle predicts the commercial solver's resonances to within three-point-
> six and one percent. The receipts are real, the physics is real, the edits are
> real."

---

### SCENE 6 — THE VISION  (2:35–3:00)

> "Solve. Reason. Edit. Verify. Refuse. That's the entire EDA design loop — closed,
> for the first time, by an agent. It's open source. It's agent-operable. It's on
> GitHub right now.
>
> This is what it looks like when AI stops answering questions about chips — and
> starts building them."

*(hold on the closer / packagent tag)*

---

## Delivery notes
- **~450 words / 180 s.** If you run long, the two lines to cut are the "senior
  engineer spends days" clause (S1) and the last sentence of S5.
- **The package is on screen** in S1 (ball map + the design), S3 (the geometry, with
  the copper plane appearing as you say "watch the copper appear"), and S6 (ball map
  behind the closer). Time the S3 line to the plane animating in.
- **Two deliberate silences:** end of S1 (red curve), end of S3 (green curve). Do
  not fill them — they are the emotional beats.
- If the LIVE Codex run finishes `fixed: true` before you present, add one
  ad-lib after S3: *"And it just did it again, live, while I was talking."*
- Record: open the deck, F11, SPACE to start, screen-record the 180 s in one take;
  narrate over it or lay the VO in after.

---

## APPENDIX — Full INTRO (live lead-in / extended cut, ~2 min spoken)

Use this as a spoken opener *before* the video for a live talk, or as the narration
for a longer 4–5 min cut. Do not stack it on top of the 180 s video — it replaces
nothing in the tight cut; it precedes it.

> "For two years, AI has swept through chip design — startups on RTL and
> verification, on analog layout, on place-and-route, on timing. Name a stage of the
> digital flow and someone's automating it.
>
> Except one: packaging.
>
> Which is strange, because packaging is where performance comes from now. Moore's
> law stalled, and the answer was chiplets and advanced packaging — UCIe, 2.5D,
> substrates with thousands of balls. The design problem moved into the package; the
> tooling didn't follow. Sign-off is still spreadsheets, tribal rules, and manual
> cross-checking — exactly the work AI should be eating, and almost no one is.
>
> This is packagent.
>
> Our thesis is simple: AI is only useful in packaging if it can't silently lie to
> you. A hallucinated design rule here doesn't cost an afternoon — it costs a mask
> set. So we didn't start with the AI. We started with what makes AI safe: a
> deterministic verification layer — ball-map connectivity, substrate geometry, PDN
> impedance, model gating — where every check is hand-verified against ground truth
> we computed ourselves, and every gap in coverage is flagged out loud instead of
> passing silently.
>
> Then we put AI on top of that layer. It reads the field-solver's verdict, reasons
> about the physics, and edits the package to fix it — and a referee it can't argue
> with decides whether the fix is real. And the best moment in the whole demo is when
> the AI is handed a spec it can't satisfy honestly — and it refuses to ship.
>
> Everything you're about to see is generated live, reproducible from a seed, with
> zero proprietary data. Let's go."
