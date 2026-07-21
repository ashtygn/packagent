#!/usr/bin/env python3
"""Build a single self-contained cinematic pitch presentation.

Reads the source PNGs, base64-embeds them inline, and emits
presentation.html (fully offline: no CDN, no external fonts, vanilla
JS + SVG + CSS + canvas). Run: python build_pitch.py

The whole deck is authored inside a fixed 1280x720 (16:9) "stage" that is
uniformly scaled to fit any viewport (letterbox). That makes clipping
impossible at 1366x768, 1280x720, 1920x1080 or any other size.
"""
import base64
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "presentation.html")

# Regenerate the package-geometry schematic that lives next to the deck.
try:
    import make_pkg_geometry
    make_pkg_geometry.render(os.path.join(HERE, "pkg_geometry.png"))
except Exception as e:  # pragma: no cover - build still proceeds if PNG exists
    print("WARN: could not regenerate pkg_geometry.png:", e)

IMAGES = {
    "baseline": r"C:\scratch\open-demo\stage\loop-visuals\1_baseline_fail.png",
    "beforeafter": r"C:\scratch\open-demo\stage\loop-visuals\3_before_after.png",
    "refused": r"C:\scratch\open-demo\stage\loop-visuals\4_round2_refused_tradeoff.png",
    "cavity": r"C:\Users\MTVPhotonicsPackagin\packagent\packagent\demo\graphs\cavity_vs_siwave.png",
    # Establishing "this is an IC package" shot (PHOTON-X1 synthetic ballmap).
    "ballmap": r"C:\scratch\open-demo\stage\graphs\ballmap_photonx1.png",
    # The design the agent actually edited (the 1824 -> 74 ohm one).
    "pkggeo": os.path.join(HERE, "pkg_geometry.png"),
}


def embed(path):
    if not os.path.isfile(path):
        sys.exit("MISSING SOURCE IMAGE: %s" % path)
    with open(path, "rb") as f:
        b = f.read()
    return "data:image/png;base64," + base64.b64encode(b).decode("ascii")


def main():
    data = {k: embed(v) for k, v in IMAGES.items()}
    html = TEMPLATE
    for k, v in data.items():
        html = html.replace("{{%s}}" % k, v)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    size = os.path.getsize(OUT)
    print("WROTE %s  (%.2f MB)" % (OUT, size / 1024.0 / 1024.0))
    if size > 8 * 1024 * 1024:
        sys.exit("ERROR: output exceeds 8 MB")


TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>packagent — the agent that does package engineering</title>
<style>
:root{
  --bg:#0b0e14; --ink:#e8edf4; --dim:#8a97ab; --cyan:#39c5cf; --amber:#e3b341;
  --red:#f0556a; --red2:#ef4b62; --line:rgba(57,197,207,.10); --panel:#0f141d;
}
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%;background:#05070b;color:var(--ink);
  font-family:"Segoe UI Variable Display","Segoe UI",Roboto,-apple-system,BlinkMacSystemFont,"Helvetica Neue",Arial,sans-serif;
  -webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility;overflow:hidden}
body{position:relative}

/* ================================================================
   FIXED 16:9 LETTERBOX STAGE
   Everything is authored at exactly 1280x720 px and uniformly
   scaled by JS (#viewport transform) to fit any viewport. This makes
   edge-clipping impossible at 1366x768 / 1280x720 / 1920x1080 / etc.
   ================================================================ */
#viewport{position:fixed;top:50%;left:50%;width:1280px;height:720px;
  transform-origin:center center;
  transform:translate(-50%,-50%) scale(var(--scale,1));
  background:var(--bg);overflow:hidden;
  box-shadow:0 0 0 100vmax #05070b, 0 30px 120px rgba(0,0,0,.7)}

/* ---- blueprint grid backdrop (inside stage) ---- */
.grid{position:absolute;inset:0;z-index:0;pointer-events:none;
  background-color:var(--bg);
  background-image:
    linear-gradient(rgba(57,197,207,.05) 1px,transparent 1px),
    linear-gradient(90deg,rgba(57,197,207,.05) 1px,transparent 1px),
    linear-gradient(rgba(57,197,207,.09) 1px,transparent 1px),
    linear-gradient(90deg,rgba(57,197,207,.09) 1px,transparent 1px);
  background-size:28px 28px,28px 28px,140px 140px,140px 140px;
  background-position:center center;}
.vignette{position:absolute;inset:0;z-index:1;pointer-events:none;
  background:radial-gradient(120% 100% at 50% 42%,transparent 42%,rgba(0,0,0,.55) 100%);}

/* ---- progress + timer chrome (inside stage) ---- */
#topbar{position:absolute;top:0;left:0;right:0;height:4px;z-index:40;background:rgba(255,255,255,.05)}
#topfill{height:100%;width:0%;background:linear-gradient(90deg,var(--cyan),var(--amber));
  box-shadow:0 0 12px rgba(57,197,207,.7);transition:width .12s linear}
#chrome{position:absolute;z-index:40;top:16px;left:24px;right:24px;display:flex;justify-content:space-between;
  align-items:center;font-size:12px;letter-spacing:.18em;color:var(--dim);text-transform:uppercase;
  font-variant-numeric:tabular-nums}
#brand{color:var(--cyan);font-weight:700}
#brand b{color:var(--amber)}
#timer{font-variant-numeric:tabular-nums}
#scenetag{position:absolute;z-index:40;bottom:16px;left:24px;font-size:12px;letter-spacing:.2em;
  color:var(--dim);text-transform:uppercase}
#dots{position:absolute;z-index:40;bottom:16px;left:50%;transform:translateX(-50%);display:flex;gap:10px}
#dots i{width:8px;height:8px;border-radius:50%;background:rgba(255,255,255,.16);transition:all .4s}
#dots i.on{background:var(--cyan);box-shadow:0 0 10px var(--cyan);transform:scale(1.25)}
#hint{position:absolute;z-index:40;bottom:14px;right:24px;font-size:12px;letter-spacing:.14em;color:var(--dim)}
#agentcredit{position:absolute;z-index:40;top:16px;left:50%;transform:translateX(-50%);
  font-size:11px;letter-spacing:.18em;text-transform:uppercase;color:var(--dim);opacity:.5;
  font-weight:600;pointer-events:none;white-space:nowrap}
#agentcredit b{color:var(--cyan);font-weight:700}
kbd{background:#1a2230;border:1px solid #2a3547;border-radius:5px;padding:2px 7px;color:var(--ink);
  font:inherit;font-size:11px}

/* ---- stage / scenes ---- */
#stage{position:absolute;inset:0;z-index:10;height:100%;width:100%}
/* Safe area: 40px side / 56px top-bottom gutter keeps content off the edges.
   justify-content:center + overflow:hidden guarantees vertical fit. */
.scene{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;
  padding:56px 48px;opacity:0;transform:scale(1.03);pointer-events:none;
  transition:opacity .9s ease,transform 1.2s cubic-bezier(.2,.7,.2,1);text-align:center}
.scene.active{opacity:1;transform:scale(1);pointer-events:auto}
.scene.prev{opacity:0;transform:scale(.985)}

/* generic reveal utility */
.rise{opacity:0;transform:translateY(24px);transition:opacity .8s ease,transform .9s cubic-bezier(.2,.7,.2,1)}
.scene.active .rise.show{opacity:1;transform:none}
.d1{transition-delay:.15s}.d2{transition-delay:.4s}.d3{transition-delay:.7s}
.d4{transition-delay:1s}.d5{transition-delay:1.35s}.d6{transition-delay:1.7s}

h1.title{font-size:64px;font-weight:800;line-height:1.03;letter-spacing:-.02em;
  max-width:16ch;background:linear-gradient(180deg,#fff,#b9c6d8);-webkit-background-clip:text;
  -webkit-text-fill-color:transparent;background-clip:text}
.sub{margin-top:18px;font-size:22px;color:var(--dim);max-width:44ch;line-height:1.4}
.eyebrow{font-size:13px;letter-spacing:.34em;text-transform:uppercase;color:var(--cyan);margin-bottom:16px;font-weight:700}
.caption{font-size:21px;line-height:1.4;max-width:60ch;color:var(--ink)}
.caption .k{color:var(--cyan);font-weight:700}
.caption .a{color:var(--amber);font-weight:700}
.caption .r{color:var(--red2);font-weight:700}
.mono{font-family:"Cascadia Mono",Consolas,"Courier New",monospace}

/* framed plot -- capped by height so it never overruns the caption room */
.plotwrap{position:relative;margin-top:18px;width:auto;max-width:88%;
  border:1px solid rgba(57,197,207,.28);border-radius:14px;overflow:hidden;
  box-shadow:0 30px 80px rgba(0,0,0,.6),0 0 0 1px rgba(0,0,0,.4) inset;background:#fff}
.plotwrap img{display:block;width:auto;height:auto;max-width:100%;max-height:340px}
.plotwrap.kb img{animation:kenburns 14s ease-out both}
@keyframes kenburns{from{transform:scale(1.005)}to{transform:scale(1.03)}}
/* two-up image row (establishing shot + curve) */
.split{display:flex;gap:20px;align-items:center;justify-content:center;max-width:96%}
.split .plotwrap{max-width:none}
.corner{position:absolute;width:16px;height:16px;border:2px solid var(--cyan);opacity:.85}
.corner.tl{top:8px;left:8px;border-right:none;border-bottom:none}
.corner.tr{top:8px;right:8px;border-left:none;border-bottom:none}
.corner.bl{bottom:8px;left:8px;border-right:none;border-top:none}
.corner.br{bottom:8px;right:8px;border-left:none;border-top:none}

/* callout chip */
.callout{position:absolute;z-index:5;background:rgba(11,14,20,.92);border:1px solid var(--cyan);
  border-radius:12px;padding:10px 15px;font-size:16px;font-weight:700;
  box-shadow:0 12px 40px rgba(0,0,0,.6);opacity:0;transform:translateY(10px) scale(.96);
  transition:opacity .6s ease,transform .7s cubic-bezier(.2,.7,.2,1)}
.scene.active .callout.show{opacity:1;transform:none}
.callout .big{font-size:1.35em}

/* ---- S2 pipeline ---- */
.pipe{width:1120px;max-width:92%;margin-top:8px}
.pipe .node rect{fill:var(--panel);stroke:#26313f;stroke-width:1.5;rx:12}
.pipe .node.lit rect{stroke:var(--cyan);filter:drop-shadow(0 0 10px rgba(57,197,207,.6))}
.pipe .node.lit.ref rect{stroke:var(--amber);filter:drop-shadow(0 0 12px rgba(227,179,65,.7))}
.pipe .node text{fill:var(--dim);font-weight:700;letter-spacing:.04em}
.pipe .node.lit text{fill:#fff}
.pipe .node text.sm{fill:#5f6d80;font-weight:600}
.pipe .node.lit text.sm{fill:var(--cyan)}
.pipe .conn{stroke:#26313f;stroke-width:3;fill:none;stroke-linecap:round}
.pipe .conn.lit{stroke:var(--cyan);stroke-dasharray:8 8;animation:flow 1s linear infinite}
@keyframes flow{to{stroke-dashoffset:-16}}
.pipe .arrow{fill:#26313f}.pipe .arrow.lit{fill:var(--cyan)}
.loopback{stroke:var(--amber);stroke-width:2.5;fill:none;stroke-dasharray:6 6;opacity:0;
  transition:opacity .6s}.loopback.show{opacity:.8;animation:flow 1.1s linear infinite}

/* ---- S5 stat cards ---- */
.cards{display:flex;flex-wrap:wrap;gap:14px;justify-content:center;margin-top:6px;max-width:1000px}
.card{background:linear-gradient(180deg,#111823,#0c1119);border:1px solid #223042;border-radius:12px;
  padding:14px 20px;min-width:150px;opacity:0;transform:translateY(20px) scale(.97);
  transition:opacity .6s ease,transform .7s cubic-bezier(.2,.7,.2,1)}
.scene.active .card.show{opacity:1;transform:none}
.card .num{font-size:34px;font-weight:800;color:var(--cyan);
  font-variant-numeric:tabular-nums;line-height:1}
.card.amberc .num{color:var(--amber)}
.card .lbl{margin-top:8px;font-size:12px;letter-spacing:.06em;color:var(--dim);text-transform:uppercase}

/* ---- REFUSED stamps ---- */
.stamps{display:flex;gap:28px;flex-wrap:wrap;justify-content:center;margin-top:16px}
.stamp{font-family:"Cascadia Mono",Consolas,monospace;font-weight:800;letter-spacing:.12em;
  font-size:26px;color:var(--red2);border:4px solid var(--red2);border-radius:10px;
  padding:6px 18px;transform:rotate(-8deg) scale(1.5);opacity:0;
  box-shadow:0 0 26px rgba(239,75,98,.35);text-shadow:0 0 18px rgba(239,75,98,.5);
  transition:opacity .32s ease,transform .42s cubic-bezier(.3,1.6,.5,1)}
.stamp.show{opacity:.94;transform:rotate(-8deg) scale(1)}
.stamp:nth-child(2){transform:rotate(6deg) scale(1.5)}
.stamp:nth-child(2).show{transform:rotate(6deg) scale(1)}
.stamp:nth-child(3){transform:rotate(-4deg) scale(1.5)}
.stamp:nth-child(3).show{transform:rotate(-4deg) scale(1)}

/* ---- S6 vision closer ---- */
#s6bg{position:absolute;inset:0;background-size:cover;background-position:center;opacity:.14;
  filter:saturate(.6);z-index:0;animation:kenburns 22s ease-out both}
.verbs{display:flex;gap:8px;flex-wrap:wrap;justify-content:center;margin-bottom:20px}
.verbs span{font-size:22px;font-weight:800;letter-spacing:.02em;color:var(--dim);
  opacity:0;transform:translateY(10px);transition:opacity .5s,transform .6s}
.scene.active .verbs span.show{opacity:1;transform:none;color:var(--cyan)}
.verbs span.amberv.show{color:var(--amber)}
.verbs .dot{color:#33404f}
.finaltag{margin-top:24px;font-size:56px;font-weight:800;letter-spacing:-.01em;color:#fff}
.finaltag b{color:var(--cyan)}
.gh{margin-top:14px;font-size:19px;color:var(--amber);font-weight:700;letter-spacing:.04em}

/* ================================================================
   TITLE SLIDE (pre-roll hold) -- lives INSIDE the 1280x720 stage so
   it scales/letterboxes exactly like the scenes and cannot clip.
   Shows first, holds indefinitely; SPACE/click starts the 180s.
   ================================================================ */
#title{position:absolute;inset:0;z-index:30;display:flex;flex-direction:column;align-items:center;
  justify-content:center;text-align:center;padding:56px 72px;cursor:pointer;
  transition:opacity .8s ease;pointer-events:auto;
  /* OPAQUE self-contained backdrop: solid dark base + blueprint grid, so no
     scene content can ever bleed through (even under reduced-motion). */
  background-color:var(--bg);
  background-image:
    radial-gradient(120% 100% at 50% 42%,transparent 42%,rgba(0,0,0,.55) 100%),
    linear-gradient(rgba(57,197,207,.05) 1px,transparent 1px),
    linear-gradient(90deg,rgba(57,197,207,.05) 1px,transparent 1px),
    linear-gradient(rgba(57,197,207,.09) 1px,transparent 1px),
    linear-gradient(90deg,rgba(57,197,207,.09) 1px,transparent 1px);
  background-size:cover,28px 28px,28px 28px,140px 140px,140px 140px;
  background-position:center center}
#title.gone{opacity:0;pointer-events:none}
/* while the title holds, hide the 6-scene playback chrome (it has not begun),
   but keep the topbar, brand+timer, and Agent credit visible/consistent. */
body.pretitle #scenetag,body.pretitle #dots,body.pretitle #hint{opacity:0;pointer-events:none}
/* slow accent halo behind the wordmark */
#title::before{content:"";position:absolute;z-index:0;width:760px;height:340px;
  border-radius:50%;filter:blur(60px);pointer-events:none;
  background:radial-gradient(closest-side,rgba(57,197,207,.20),transparent 72%);
  animation:titleglow 6s ease-in-out infinite}
@keyframes titleglow{0%,100%{opacity:.55;transform:scale(1)}50%{opacity:1;transform:scale(1.06)}}
#title>*{position:relative;z-index:1}
.t-eyebrow{font-size:13px;letter-spacing:.36em;text-transform:uppercase;color:var(--cyan);
  font-weight:700;opacity:0;transform:translateY(16px);
  animation:titlerise .9s cubic-bezier(.2,.7,.2,1) .2s forwards}
.t-word{margin-top:18px;font-size:132px;font-weight:800;line-height:.98;letter-spacing:-.03em;
  opacity:0;transform:translateY(22px);
  animation:titlerise 1s cubic-bezier(.2,.7,.2,1) .45s forwards;
  background:linear-gradient(180deg,#fff,#c3d0e2);-webkit-background-clip:text;
  -webkit-text-fill-color:transparent;background-clip:text}
.t-word b{color:var(--cyan);-webkit-text-fill-color:var(--cyan);
  text-shadow:0 0 40px rgba(57,197,207,.45)}
.t-rule{margin:22px 0 0;width:120px;height:2px;border:0;opacity:0;
  background:linear-gradient(90deg,transparent,var(--cyan),transparent);
  animation:titlerise .9s ease .7s forwards}
.t-tag{margin-top:22px;font-size:27px;font-weight:600;color:var(--ink);max-width:34ch;line-height:1.35;
  opacity:0;transform:translateY(18px);
  animation:titlerise 1s cubic-bezier(.2,.7,.2,1) .85s forwards}
.t-tag .k{color:var(--cyan);font-weight:700}
.t-codex{margin-top:16px;font-size:15px;letter-spacing:.22em;text-transform:uppercase;font-weight:700;
  color:var(--cyan);opacity:0;transform:translateY(14px);
  animation:titlerise 1s cubic-bezier(.2,.7,.2,1) 1.15s forwards}
#title .t-hint{position:absolute;z-index:2;bottom:40px;left:0;right:0;text-align:center;
  font-size:14px;letter-spacing:.14em;color:var(--dim);
  opacity:0;animation:titlehint 1s ease 1.7s forwards}
.t-hint kbd{background:#1a2230;border:1px solid #2a3547;border-radius:5px;padding:2px 9px;
  color:var(--ink);font:inherit;font-size:12px}
.t-hint .pulse-dot{display:inline-block;width:7px;height:7px;border-radius:50%;background:var(--cyan);
  margin-right:10px;vertical-align:middle;box-shadow:0 0 10px var(--cyan);
  animation:pulse 2.6s ease-in-out infinite}
@keyframes titlerise{to{opacity:1;transform:none}}
@keyframes titlehint{from{opacity:0}to{opacity:.85}}
@keyframes pulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.55;transform:scale(1.25)}}
/* freeze motion for ?still / reduced-motion / ?title: show final title frame.
   The global ".still *{animation:none}" strips animation-name, so set the
   end-state (opacity/transform) directly instead of relying on the keyframes.
   ".titlefreeze" freezes ONLY the title (used by ?title capture) without
   touching scene .rise elements, so the hook does not bleed through. */
.still .t-eyebrow,.still .t-word,.still .t-rule,.still .t-tag,.still .t-codex,
.titlefreeze .t-eyebrow,.titlefreeze .t-word,.titlefreeze .t-rule,
.titlefreeze .t-tag,.titlefreeze .t-codex{
  opacity:1 !important;transform:none !important;animation:none !important}
.still .t-hint,.titlefreeze .t-hint{opacity:.85 !important;animation:none !important}
.still #title::before,.titlefreeze #title::before{
  opacity:.8 !important;transform:none !important;animation:none !important}

/* progressive enhancement: no-JS = stacked readable scenes */
.nojs #viewport{position:static;width:100%;height:auto;transform:none;box-shadow:none;overflow:visible}
.nojs #stage{height:auto;overflow:visible}
.nojs .scene{position:relative;opacity:1;transform:none;min-height:100vh;border-bottom:1px solid var(--line);
  pointer-events:auto}
.nojs .rise{opacity:1;transform:none}
.nojs .callout,.nojs .card,.nojs .stamp,.nojs .verbs span{opacity:1;transform:none}
.nojs #title,.nojs #topbar,.nojs #dots,.nojs #hint{display:none}
.nojs body{overflow:auto}

/* reduced-motion / ?still: freeze animations, show final frames */
.still *{animation:none !important;transition:none !important}
.still .rise{opacity:1 !important;transform:none !important}
.still .callout,.still .card,.still .stamp,.still .verbs span{opacity:1 !important;transform:none !important}
@media (prefers-reduced-motion:reduce){
  .rise,.scene{transition:none}
}
</style>
</head>
<body class="nojs">
<script>document.body.classList.remove('nojs');</script>

<!-- fixed 16:9 stage; JS scales it to fit any viewport (letterbox) -->
<div id="viewport">

<div class="grid"></div>
<div class="vignette"></div>

<div id="topbar"><div id="topfill"></div></div>
<div id="chrome">
  <div id="brand">pack<b>agent</b></div>
  <div id="timer">0:00 / 3:00</div>
</div>
<div id="agentcredit">Agent: <b>OpenAI Codex</b></div>
<div id="scenetag">Scene 1 / 6</div>
<div id="dots"><i class="on"></i><i></i><i></i><i></i><i></i><i></i></div>
<div id="hint"><kbd>Space</kbd> play &nbsp; <kbd>&larr;</kbd><kbd>&rarr;</kbd> seek &nbsp; <kbd>R</kbd> restart</div>

<main id="stage">

  <!-- S1 HOOK -->
  <section class="scene" data-scene="0">
    <div class="eyebrow rise d1">Silicon-package power integrity &middot; closed-loop</div>
    <h1 class="title rise d1" style="font-size:46px;max-width:30ch">The agent that does package engineering</h1>
    <div class="split rise d3" style="margin-top:14px">
      <div class="plotwrap kb" style="margin-top:0;max-width:none">
        <span class="corner tl"></span><span class="corner tr"></span>
        <span class="corner bl"></span><span class="corner br"></span>
        <img src="{{ballmap}}" alt="Top view of an IC package ball map"
             style="max-height:266px">
      </div>
      <div class="plotwrap" style="margin-top:0;max-width:none">
        <span class="corner tl"></span><span class="corner tr"></span>
        <span class="corner bl"></span><span class="corner br"></span>
        <img src="{{baseline}}" alt="Baseline impedance curve breaching the mask"
             style="max-height:266px">
      </div>
    </div>
    <p class="caption rise d5" style="margin-top:14px;font-size:19px">This is an <span class="k">IC package</span>.
      Its power network resonates at <span class="r">1824&nbsp;&Omega;</span> &mdash;
      nine times over the <span class="a">200&nbsp;&Omega;</span> limit.</p>
  </section>

  <!-- S2 THE LOOP -->
  <section class="scene" data-scene="1">
    <div class="eyebrow rise d1">The loop</div>
    <h1 class="title rise d1" style="font-size:52px">It reasons. It edits. It proves.</h1>
    <svg class="pipe" viewBox="0 0 1180 210" id="pipeSvg" aria-hidden="true">
      <defs></defs>
      <!-- connectors -->
      <g id="conns"></g>
      <!-- nodes injected by JS -->
      <g id="pnodes"></g>
      <!-- loopback -->
      <path class="loopback" id="loopback" d="M 1090 150 C 1090 205, 90 205, 90 150"></path>
    </svg>
    <div class="rise d4" style="margin-top:6px;font-size:13px;letter-spacing:.22em;
      text-transform:uppercase;font-weight:700;color:var(--cyan)">Driven by OpenAI Codex</div>
    <p class="caption rise d5" style="margin-top:16px">It doesn't just run commands. It
      <span class="k">reasons from the physics</span>, <span class="k">edits the design</span>,
      and <span class="a">proves the fix</span>.</p>
  </section>

  <!-- S3 THE FIX -->
  <section class="scene" data-scene="2">
    <div class="eyebrow rise d1">The fix</div>
    <p class="caption rise d1" style="max-width:74ch">The agent reads the curve:
      <span class="k">0.8&nbsp;pF</span> plate capacitance means <span class="r">no reference plane</span>.
      It draws copper &mdash; a <span class="a">16&times;16&nbsp;mm VDD plane</span> under the via ring,
      inside <span class="a">Allegro</span>, headless. The resonance collapses.</p>
    <div class="split rise d3" style="margin-top:14px">
      <div class="plotwrap kb" style="margin-top:0;max-width:none">
        <span class="corner tl"></span><span class="corner tr"></span>
        <span class="corner bl"></span><span class="corner br"></span>
        <img src="{{pkggeo}}" alt="Top view: agent added a 16x16 mm VDD plane under the ring"
             style="max-height:286px">
      </div>
      <div class="plotwrap" style="margin-top:0;max-width:none">
        <span class="corner tl"></span><span class="corner tr"></span>
        <span class="corner bl"></span><span class="corner br"></span>
        <img src="{{beforeafter}}" alt="Impedance before (red) and after (green): -96% collapse"
             style="max-height:296px">
        <div class="callout" data-cw style="right:14px;top:14px">
          <span class="r mono">1824</span> &rarr; <span class="k mono">74&nbsp;&Omega;</span>
          &nbsp;<span class="big a">(&minus;96%)</span>
        </div>
      </div>
    </div>
    <p class="caption rise d5" style="margin-top:12px;font-size:18px">The design the agent edited &mdash;
      plane capacitance <span class="k">0.8&nbsp;&rarr;&nbsp;61&nbsp;pF</span>, predicted before solving.</p>
  </section>

  <!-- S4 THE REFEREE -->
  <section class="scene" data-scene="3">
    <div class="eyebrow rise d1">The referee</div>
    <p class="caption rise d1" style="max-width:72ch;font-size:19px">It cannot be fooled. Add a conflicting requirement
      and it tries three fixes &mdash; each <span class="r">REFUSED</span> by an independent referee for
      trading one spec against another.</p>
    <div class="plotwrap rise d2" style="margin-top:12px;max-width:none">
      <span class="corner tl"></span><span class="corner tr"></span>
      <span class="corner bl"></span><span class="corner br"></span>
      <img src="{{refused}}" alt="Round-2 refused tradeoff plot" style="max-height:250px">
    </div>
    <div class="stamps" data-stamps>
      <span class="stamp">REFUSED</span>
      <span class="stamp">REFUSED</span>
      <span class="stamp">REFUSED</span>
    </div>
    <p class="caption rise d4" style="margin-top:12px;font-weight:700;font-size:18px">
      The referee &mdash; <span class="a">not the agent</span> &mdash; decides. Three plausible fixes,
      three justified refusals, <span class="r">nothing shipped</span>.</p>
  </section>

  <!-- S5 THE RECEIPTS -->
  <section class="scene" data-scene="4">
    <div class="eyebrow rise d1">The receipts</div>
    <h1 class="title rise d1" style="font-size:50px">None of this is a mockup.</h1>
    <div class="cards" data-cards style="margin-top:18px">
      <div class="card"><div class="num" data-count="26">0</div><div class="lbl">solver-signed result trees</div></div>
      <div class="card amberc"><div class="num" data-det>0</div><div class="lbl">determinism</div></div>
      <div class="card"><div class="num"><span data-count="4">0</span>/4</div><div class="lbl">physics matrix</div></div>
      <div class="card"><div class="num"><span data-count="8">0</span>/8</div><div class="lbl">error-injection</div></div>
      <div class="card amberc"><div class="num"><span data-count="3">0</span>&times;</div><div class="lbl">reproducible, bit-identical</div></div>
    </div>
    <div class="plotwrap kb rise d4" style="margin-top:16px;max-width:none">
      <span class="corner tl"></span><span class="corner tr"></span>
      <span class="corner bl"></span><span class="corner br"></span>
      <img src="{{cavity}}" alt="Analytic cavity oracle vs commercial SIwave solver"
           style="max-height:238px">
    </div>
    <p class="caption rise d5" style="margin-top:12px;font-size:18px">Our open-source physics oracle predicts the commercial
      solver's resonances to within <span class="k">3.68%</span> and <span class="k">1.00%</span>.</p>
  </section>

  <!-- S6 THE VISION -->
  <section class="scene" data-scene="5">
    <div id="s6bg" style="background-image:url('{{ballmap}}')"></div>
    <div class="eyebrow rise d1">The vision</div>
    <div class="verbs" data-verbs>
      <span>Solve.</span><span class="dot">/</span>
      <span>Reason.</span><span class="dot">/</span>
      <span>Edit.</span><span class="dot">/</span>
      <span>Verify.</span><span class="dot">/</span>
      <span class="amberv">Refuse.</span>
    </div>
    <h1 class="title rise d3" style="max-width:20ch">The EDA design loop, closed by an agent.</h1>
    <div class="rise d4" style="margin-top:10px;font-size:15px;letter-spacing:.16em;
      text-transform:uppercase;font-weight:700;color:var(--cyan)">Closed by an OpenAI Codex agent</div>
    <p class="sub rise d4" style="margin-top:12px">Open source. Agent-operable. On GitHub now.</p>
    <div class="finaltag rise d5">pack<b>agent</b></div>
  </section>

</main>

<!-- TITLE SLIDE (pre-roll hold) -- inside the scaled 1280x720 stage -->
<div id="title">
  <div class="t-eyebrow">Silicon-package power integrity &middot; closed-loop</div>
  <div class="t-word">pack<b>agent</b></div>
  <hr class="t-rule">
  <div class="t-tag">Package-design verification &mdash;
    <span class="k">closed-loop</span>, by an AI agent.</div>
  <div class="t-codex">Powered by OpenAI Codex</div>
  <div class="t-hint"><span class="pulse-dot"></span>Press <kbd>Space</kbd> to begin</div>
</div>

</div><!-- /#viewport -->

<script>
(function(){
  "use strict";
  var q=function(s,r){return (r||document).querySelector(s);};
  var qa=function(s,r){return Array.prototype.slice.call((r||document).querySelectorAll(s));};

  // ---- letterbox scaler: fit the fixed 1280x720 stage into any viewport ----
  var STAGE_W=1280, STAGE_H=720, vp=q('#viewport');
  function fit(){
    if(!vp) return;
    var s=Math.min(window.innerWidth/STAGE_W, window.innerHeight/STAGE_H);
    vp.style.setProperty('--scale', s);
  }
  window.addEventListener('resize', fit, {passive:true});
  fit();

  // ?still => reduced motion / final frames
  var STILL = /(?:^|[?&])still(?:=|&|$)/.test(location.search) ||
              (window.matchMedia && window.matchMedia('(prefers-reduced-motion:reduce)').matches);
  if(STILL) document.body.classList.add('still');

  // --- scene timing (seconds). end-start = duration ---
  var SCENES=[
    {start:0,   end:28 },   // S1 HOOK      (28s: +pkg establishing shot)
    {start:28,  end:52 },   // S2 LOOP      (24s)
    {start:52,  end:87 },   // S3 FIX       (35s: +pkg geometry / copper added)
    {start:87,  end:120},   // S4 REFEREE   (33s)
    {start:120, end:155},   // S5 RECEIPTS  (35s)
    {start:155, end:180}    // S6 VISION    (25s)
  ];
  var TOTAL=180;
  var scenes=qa('.scene');
  var dots=qa('#dots i');

  // ---- build S2 pipeline nodes ----
  var PN=[
    {t:'SOLVE',  s:'SIwave'},
    {t:'READ',   s:'physics'},
    {t:'EDIT',   s:'.mcm / Allegro'},
    {t:'RE-SOLVE',s:'SIwave'},
    {t:'REFEREE',s:'independent'}
  ];
  (function buildPipe(){
    var g=q('#pnodes'), c=q('#conns');
    if(!g) return;
    var W=180,H=92,gap=(1180-W*5)/4, y=54;
    for(var i=0;i<5;i++){
      var x=i*(W+gap);
      var isRef=(i===4);
      var node=document.createElementNS('http://www.w3.org/2000/svg','g');
      node.setAttribute('class','node'+(isRef?' ref':''));
      node.setAttribute('data-n',i);
      node.innerHTML=
        '<rect x="'+x+'" y="'+y+'" width="'+W+'" height="'+H+'" rx="12"/>'+
        '<text x="'+(x+W/2)+'" y="'+(y+40)+'" text-anchor="middle" font-size="22">'+PN[i].t+'</text>'+
        '<text class="sm" x="'+(x+W/2)+'" y="'+(y+66)+'" text-anchor="middle" font-size="14">'+PN[i].s+'</text>';
      g.appendChild(node);
      if(i<4){
        var x2=(i+1)*(W+gap);
        var cx1=x+W, cx2=x2, my=y+H/2;
        var path=document.createElementNS('http://www.w3.org/2000/svg','path');
        path.setAttribute('class','conn');path.setAttribute('data-c',i);
        path.setAttribute('d','M '+cx1+' '+my+' L '+(cx2-14)+' '+my);
        c.appendChild(path);
        var ar=document.createElementNS('http://www.w3.org/2000/svg','path');
        ar.setAttribute('class','arrow');ar.setAttribute('data-a',i);
        ar.setAttribute('d','M '+(cx2-14)+' '+(my-7)+' L '+cx2+' '+my+' L '+(cx2-14)+' '+(my+7)+' Z');
        c.appendChild(ar);
      }
    }
  })();

  // ---- state ----
  var playing=false, t0=0, raf=0, cur=-1, manualBase=0, doneAll=false;
  var sceneEntered=[];
  var FREEZE=STILL;   // when true, all per-scene animations jump to final frame

  function fmt(s){s=Math.max(0,Math.floor(s));return Math.floor(s/60)+':'+('0'+(s%60)).slice(-2);}

  function setScene(i,fromTimer){
    if(i===cur) return;
    scenes.forEach(function(el,k){
      el.classList.toggle('active',k===i);
      el.classList.toggle('prev',k<i);
    });
    dots.forEach(function(d,k){d.classList.toggle('on',k===i);});
    q('#scenetag').textContent='Scene '+(i+1)+' / 6';
    cur=i;
    enterScene(i);
  }

  function showRises(scene){
    qa('.rise',scene).forEach(function(el){el.classList.add('show');});
  }

  function enterScene(i){
    var sc=scenes[i];
    // always reveal the rise elements
    if(FREEZE){ showRises(sc); }
    else { setTimeout(function(){showRises(sc);},40); }
    if(sceneEntered[i]) { runSceneAnim(i,sc,true); return; }
    sceneEntered[i]=true;
    runSceneAnim(i,sc,false);
  }

  function runSceneAnim(i,sc,replay){
    if(i===1) animPipe(sc,replay);
    if(i===2) animCallouts(sc);
    if(i===3) animStamps(sc);
    if(i===4) animCards(sc);
    if(i===5) animVerbs(sc);
  }

  // S2 pipeline light-up
  var pipeTimers=[];
  function clearP(){pipeTimers.forEach(clearTimeout);pipeTimers=[];}
  function animPipe(sc,replay){
    clearP();
    var nodes=qa('#pnodes .node'), conns=qa('#conns .conn'), arrs=qa('#conns .arrow');
    nodes.forEach(function(n){n.classList.remove('lit');});
    conns.forEach(function(c){c.classList.remove('lit');});
    arrs.forEach(function(a){a.classList.remove('lit');});
    q('#loopback').classList.remove('show');
    var step= FREEZE?0: (replay?600:1100);
    if(FREEZE){ nodes.forEach(function(n){n.classList.add('lit');});
      conns.forEach(function(c){c.classList.add('lit');});
      arrs.forEach(function(a){a.classList.add('lit');});
      q('#loopback').classList.add('show'); return; }
    nodes.forEach(function(n,k){
      pipeTimers.push(setTimeout(function(){
        n.classList.add('lit');
        if(k>0 && conns[k-1]){conns[k-1].classList.add('lit');arrs[k-1].classList.add('lit');}
      }, 400+k*step));
    });
    pipeTimers.push(setTimeout(function(){q('#loopback').classList.add('show');},400+5*step));
  }

  function animCallouts(sc){
    var cs=qa('[data-cw]',sc);
    cs.forEach(function(c,k){
      if(FREEZE){c.classList.add('show');return;}
      setTimeout(function(){c.classList.add('show');},1400+k*900);
    });
  }

  function animStamps(sc){
    var st=qa('[data-stamps] .stamp',sc);
    st.forEach(function(s,k){
      if(FREEZE){s.classList.add('show');return;}
      setTimeout(function(){s.classList.add('show');},1600+k*700);
    });
  }

  function animCards(sc){
    var cards=qa('[data-cards] .card',sc);
    cards.forEach(function(cd,k){
      var go=function(){
        cd.classList.add('show');
        var cn=q('[data-count]',cd); if(cn) countUp(cn);
        var det=q('[data-det]',cd); if(det) countDet(det);
      };
      if(FREEZE){cd.classList.add('show');
        var cn=q('[data-count]',cd); if(cn) cn.textContent=cn.getAttribute('data-count');
        var det=q('[data-det]',cd); if(det) det.textContent='1.3e-5';
        return;}
      setTimeout(go, 500+k*260);
    });
  }

  function countUp(el){
    var target=parseInt(el.getAttribute('data-count'),10)||0, dur=1000, s=performance.now();
    function tick(now){var p=Math.min(1,(now-s)/dur);var e=1-Math.pow(1-p,3);
      el.textContent=Math.round(target*e);if(p<1)requestAnimationFrame(tick);}
    requestAnimationFrame(tick);
  }
  function countDet(el){
    // animate mantissa toward 1.3e-5
    var dur=1100,s=performance.now();
    function tick(now){var p=Math.min(1,(now-s)/dur);var e=1-Math.pow(1-p,3);
      var m=(1.3*e).toFixed(1);el.textContent=m+'e-5';if(p<1)requestAnimationFrame(tick);}
    requestAnimationFrame(tick);
  }

  function animVerbs(sc){
    var vs=qa('[data-verbs] span:not(.dot)',sc);
    vs.forEach(function(v,k){
      if(FREEZE){v.classList.add('show');return;}
      setTimeout(function(){v.classList.add('show');},300+k*420);
    });
  }

  // ---- timeline driver ----
  function frame(now){
    if(!playing) return;
    var t=manualBase+(now-t0)/1000;
    if(t>=TOTAL){t=TOTAL; playing=false; doneAll=true;}
    // progress + timer
    q('#topfill').style.width=(t/TOTAL*100)+'%';
    q('#timer').textContent=fmt(t)+' / 3:00';
    // which scene
    var idx=SCENES.length-1;
    for(var i=0;i<SCENES.length;i++){ if(t>=SCENES[i].start && t<SCENES[i].end){idx=i;break;} }
    if(t>=TOTAL) idx=SCENES.length-1;
    setScene(idx,true);
    if(playing) raf=requestAnimationFrame(frame);
    else if(doneAll){ setScene(SCENES.length-1,true); } // hold closer
  }

  function play(){
    if(playing) return;
    document.body.classList.remove('pretitle');
    hideStart();
    playing=true; doneAll=false;
    t0=performance.now();
    raf=requestAnimationFrame(frame);
  }
  function pause(){ playing=false; cancelAnimationFrame(raf); manualBase=curTime(); }
  function curTime(){
    var el=q('#topfill'); var w=parseFloat(el.style.width)||0; return w/100*TOTAL;
  }

  function seek(sec){
    playing=false; cancelAnimationFrame(raf);
    manualBase=Math.max(0,Math.min(TOTAL-0.01,sec));
    q('#topfill').style.width=(manualBase/TOTAL*100)+'%';
    q('#timer').textContent=fmt(manualBase)+' / 3:00';
    var idx=SCENES.length-1;
    for(var i=0;i<SCENES.length;i++){ if(manualBase>=SCENES[i].start && manualBase<SCENES[i].end){idx=i;break;} }
    setScene(idx,false);
  }
  function nextScene(){ var i=Math.min(SCENES.length-1,cur+1); seek(SCENES[i].start+0.05); }
  function prevScene(){ var i=Math.max(0,cur-1); seek(SCENES[i].start+0.05); }

  function restart(){
    manualBase=0; sceneEntered=[]; cur=-1; doneAll=false;
    q('#topfill').style.width='0%';
    scenes.forEach(function(el){ qa('.rise',el).forEach(function(r){r.classList.remove('show');}); });
    play();
  }

  var started=false;
  function hideStart(){ var s=q('#title'); if(s) s.classList.add('gone'); }
  function showTitle(){ var s=q('#title'); if(s) s.classList.remove('gone'); }
  function begin(){ if(started)return; started=true;
    document.body.classList.remove('pretitle'); play(); }
  function backToTitle(){
    // pause the 180s, rewind to the very start, re-show the title hold
    playing=false; cancelAnimationFrame(raf); doneAll=false;
    started=false; manualBase=0;
    q('#topfill').style.width='0%';
    q('#timer').textContent='0:00 / 3:00';
    document.body.classList.add('pretitle');
    showTitle();
  }

  // ---- input ----
  document.addEventListener('keydown',function(e){
    var k=e.key;
    if(k===' '||k==='Spacebar'){ e.preventDefault();
      if(!started){begin();} else if(playing){pause();} else {resume();} return; }
    if(k==='ArrowRight'){ e.preventDefault(); if(!started)begin(); nextScene(); return; }
    if(k==='ArrowLeft'){ e.preventDefault();
      if(!started){begin(); return;}
      // from the hook (scene 0), arrow-left returns to the title hold
      if(cur===0){ backToTitle(); return; }
      prevScene(); return; }
    if(k==='r'||k==='R'){ e.preventDefault(); started=true; restart(); return; }
  });
  function resume(){ if(playing)return; playing=true; doneAll=false; t0=performance.now(); raf=requestAnimationFrame(frame); }

  var titleEl=q('#title');
  if(titleEl) titleEl.addEventListener('click',begin);
  document.addEventListener('click',function(e){
    if(!started){begin();return;}
    if(q('#title') && !q('#title').classList.contains('gone')) return;
    // click on stage toggles pause/resume
    if(playing)pause(); else resume();
  });

  // If STILL/reduced-motion: auto-begin and show first scene immediately (no blank)
  if(STILL){
    started=true; hideStart();
    // show all scenes' final states progressively; land on scene 1 for a "title" frame,
    // but ensure every scene has revealed for ?still capture use-cases
    scenes.forEach(function(el,i){ sceneEntered[i]=false; });
    setScene(0,false);
    // reveal each scene's rises so nothing is blank if navigated
    scenes.forEach(function(el){ showRises(el); });
    q('#topfill').style.width='0%';
    q('#timer').textContent='0:00 / 3:00';
  } else {
    // TITLE HOLD: the title slide shows first and holds indefinitely.
    // Prime scene 0 (hook) behind it so playback starts instantly on SPACE.
    document.body.classList.add('pretitle');
    setScene(0,false);
    // hide rises until playback starts
    qa('.rise',scenes[0]).forEach(function(r){r.classList.remove('show');});
  }

  // expose for headless screenshotting: ?goto=N jumps to scene N (0-based) as a frozen still
  var gm=/[?&]goto=(\d)/.exec(location.search);
  if(gm){ started=true; playing=false; FREEZE=true; hideStart();
    document.body.classList.add('still'); document.body.classList.remove('pretitle');
    var gi=Math.max(0,Math.min(5,parseInt(gm[1],10)));
    cur=-1; sceneEntered=[]; setScene(gi,false); showRises(scenes[gi]);
  }

  // ?title => freeze the TITLE slide in its final frame (for headless capture).
  // Use .titlefreeze (not .still) so scene .rise elements stay hidden and the
  // hook does not bleed through the (translucent) title backdrop.
  if(/[?&]title(?:=|&|$)/.test(location.search)){
    document.body.classList.add('titlefreeze','pretitle');
    setScene(0,false);
    qa('.rise',scenes[0]).forEach(function(r){r.classList.remove('show');});
    showTitle();
  }
})();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
