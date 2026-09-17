#!/usr/bin/env python3
# Renders the final Andrea Silveria moonset lockups. Run: python3 build.py
import os, subprocess, pathlib
here = pathlib.Path(__file__).parent.resolve()
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
FONTS = '<link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;1,6..72,300&family=Mulish:wght@600&display=swap" rel="stylesheet">'
CSS = """
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Mulish',sans-serif;display:flex;align-items:center;justify-content:center;overflow:hidden}
.lock{text-align:center;color:var(--ink)}
.lock img{display:block;margin:0 auto;height:var(--mh)}
.name{font-family:'Newsreader',serif;font-weight:400;font-size:var(--ns);letter-spacing:.16em;text-indent:.16em;line-height:1.1;margin-top:var(--gap);white-space:nowrap}
.sub{font-weight:600;font-size:var(--ss);letter-spacing:.36em;text-indent:.36em;opacity:.78;margin-top:var(--sgap);white-space:nowrap}
.sub.ital{font-family:'Newsreader',serif;font-style:italic;font-weight:300;letter-spacing:.02em;text-indent:0;font-size:calc(var(--ss)*1.7);opacity:.72}
/* horizontal (email signature) */
.row{display:flex;align-items:center;gap:var(--gap);color:var(--ink);text-align:left}
.row img{height:var(--mh);display:block}
.row .name{margin-top:0}
.row .sub{margin-top:var(--sgap)}
"""
def page(body, bg, ink, mh, ns, ss, gap, sgap, w=2000, h=1400):
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8">{FONTS}<style>{CSS}
body{{width:{w}px;height:{h}px;background:{bg};--ink:{ink};--mh:{mh}px;--ns:{ns}px;--ss:{ss}px;--gap:{gap}px;--sgap:{sgap}px}}</style></head><body>{body}</body></html>"""

NAVY, CREAM, LIGHTBG = "#1A2430", "#FBF9F4", "#F7F3EA"
def stacked(mark, sub_ital=False):
    sub = 'Coaching &amp; Consulting' if sub_ital else 'COACHING &amp; CONSULTING'
    return f'<div class="lock"><img src="{mark}"><div class="name">ANDREA SILVERIA</div><div class="sub{" ital" if sub_ital else ""}">{sub}</div></div>'
def row(mark):
    return f'<div class="row"><img src="{mark}"><div><div class="name">ANDREA SILVERIA</div><div class="sub">COACHING &amp; CONSULTING</div></div></div>'

jobs = [
 # name, html, width, height, transparent
 ("lockup-dark",    page(stacked("mark-moonset-cream.svg"), NAVY,  CREAM, 340, 76, 24, 38, 22), 2000, 1400, False),
 ("lockup-light",   page(stacked("mark-moonset-navy.svg"),  LIGHTBG, NAVY, 340, 76, 24, 38, 22), 2000, 1400, False),
 ("lockup-dark-italic-sub",  page(stacked("mark-moonset-cream.svg", True), NAVY, CREAM, 340, 76, 18, 38, 12), 2000, 1400, False),
 ("lockup-transparent-navy", page(stacked("mark-moonset-navy.svg"), "transparent", NAVY, 340, 76, 24, 38, 22, 1400, 900), 1400, 900, True),
 ("lockup-transparent-cream",page(stacked("mark-moonset-cream.svg"), "transparent", CREAM, 340, 76, 24, 38, 22, 1400, 900), 1400, 900, True),
 ("avatar-dark",    page('<div class="lock"><img src="mark-moonset-cream.svg"></div>', NAVY, CREAM, 520, 0, 0, 0, 0, 1000, 1000), 1000, 1000, False),
 ("avatar-light",   page('<div class="lock"><img src="mark-moonset-navy.svg"></div>', LIGHTBG, NAVY, 520, 0, 0, 0, 0, 1000, 1000), 1000, 1000, False),
 ("email-signature",page(row("mark-moonset-navy.svg"), "transparent", NAVY, 96, 30, 9, 28, 8, 600, 140), 600, 140, True),
 ("email-signature-dark",page(row("mark-moonset-cream.svg"), NAVY, CREAM, 96, 30, 9, 28, 8, 600, 140), 600, 140, False),
]
for name, html, w, h, transparent in jobs:
    src = here / f"_{name}.html"; src.write_text(html)
    out = here / f"{name}.png"
    args = [CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--allow-file-access-from-files",
            f"--window-size={w},{h}", "--force-device-scale-factor=2", "--virtual-time-budget=8000",
            f"--screenshot={out}"]
    if transparent: args.append("--default-background-color=00000000")
    args.append(f"file://{src}")
    subprocess.run(args, capture_output=True)
    print(name, out.exists())
