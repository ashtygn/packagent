# 3-Minute Pitch — video voiceover script

Deck: `C:\scratch\open-demo\stage\pitch\presentation.html` (press SPACE to play, F11
fullscreen, screen-record). The deck auto-advances on a 180 s timer; the narration
below is timed scene-by-scene to match. Target pace ~145 wpm. Practice once against
the progress bar.

Tone: calm, certain, a little bit awed. You are not selling — you are showing
something that shouldn't exist yet and does. Let the two silences land.

---

### SCENE 1 — HOOK  (0:00–0:25)

> "This is a real integrated-circuit package. And its power-delivery network is
> broken — it resonates at 6.1 gigahertz, spiking to eighteen hundred ohms, nine
> times over the limit. Normally, a senior signal-integrity engineer spends days
> chasing a fault like this.
>
> Tonight, an AI agent did it. Watch."

*(let the red curve sit for a beat before Scene 2)*

---

### SCENE 2 — THE LOOP  (0:25–0:50)

> "It isn't running a script. It's closing a loop that, until now, only a human
> could close. It solves the package in Ansys SIwave — a commercial field solver.
> It reads the physics. It edits the actual Cadence design database. It re-solves.
> And then — this is the important part — a referee decides whether the fix is real.
> Not the agent. The referee."

---

### SCENE 3 — THE FIX  (0:50–1:25)  ← the peak, give it air

> "Here's the reasoning. The agent looks at the curve and sees a plate capacitance
> of under one picofarad — which means this design has no working reference planes
> at all. So it computes the size of the planes it needs, and it draws the copper —
> headless, inside Allegro, and every single edit is independently verified in a
> fresh session before anything is trusted.
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
- **~430 words / 180 s.** If you run long, the two lines to cut are the "senior
  engineer spends days" clause (S1) and the last sentence of S5.
- **Two deliberate silences:** end of S1 (red curve), end of S3 (green curve). Do
  not fill them — they are the emotional beats.
- If the LIVE Codex run finishes `fixed: true` before you present, add one
  ad-lib after S3: *"And it just did it again, live, while I was talking."*
- Record: open the deck, F11, SPACE to start, screen-record the 180 s in one take;
  narrate over it or lay the VO in after.
