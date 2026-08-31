# -*- coding: utf-8 -*-
"""Page-level chrome unique to the interview map.

The other pages teach one subject in depth, so their components are cards and
figures. This one is a syllabus: its job is to be *exhaustive* and still
readable, which needs three devices the shared design system does not have.

  .syl    a sub-topic and the one line saying what it is actually testing
  .chips  the flat wall of every term under a heading -- the "nothing left
          behind" device; a reader scans it and finds the word they do not know
  .ask    real questions, each with the signal the interviewer is listening for

Nothing here is interactive. The page ships no JavaScript of its own.
"""

CSS = """
<style>
/* ---------- syllabus grid: a sub-topic and what it tests ---------- */
/* Two columns, not three. These carry a paragraph each rather than a line, and
   at three columns a card is 48 characters wide -- a measure that reads as a
   list even when the content is prose. */
.syl{display:grid;grid-template-columns:repeat(auto-fit,minmax(430px,1fr));gap:10px;margin:24px 0}
.syl > div{background:var(--surface);border:1px solid var(--line);
  border-left:3px solid var(--sc,var(--l2));padding:11px 14px}
/* The term. A direct child, so a <b> used for emphasis inside the body below
   does not inherit the mono-uppercase treatment and become a heading. */
.syl > div > b{display:block;font-family:"IBM Plex Mono",monospace;font-size:0.71rem;
  letter-spacing:0.06em;text-transform:uppercase;color:var(--ink);font-weight:600}
.syl i{display:block;font-style:normal;font-size:0.88rem;color:var(--ink-soft);
  margin-top:6px;line-height:1.55}
.syl i b{display:inline;font-family:inherit;font-size:inherit;letter-spacing:normal;
  text-transform:none;color:var(--ink);font-weight:600}
.syl i + i{margin-top:9px}
.syl i code{font-size:0.86em}
.syl.s1 > div{--sc:var(--l1)}
.syl.s2 > div{--sc:var(--l2)}
.syl.s3 > div{--sc:var(--l3)}

/* ---------- the term wall ---------- */
.chips-h{font-family:"IBM Plex Mono",monospace;font-size:0.66rem;letter-spacing:0.1em;
  text-transform:uppercase;color:var(--ink-faint);margin:24px 0 0}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin:10px 0 24px}
.chips span{font-family:"IBM Plex Mono",monospace;font-size:0.71rem;color:var(--ink-soft);
  background:var(--surface-2);border:1px solid var(--line);padding:3px 8px;line-height:1.35}
.chips span.hot{background:var(--surface);border-color:var(--l3);color:var(--l3);font-weight:600}

/* ---------- questions, and the signal behind each ---------- */
.ask{list-style:none;padding:0;margin:24px 0;border-top:1px solid var(--line)}
.ask li{border-bottom:1px solid var(--line);padding:12px 0}
.ask q{font-size:0.95rem;color:var(--ink);quotes:"\\201C" "\\201D"}
.ask em{display:block;font-style:normal;font-size:0.875rem;color:var(--ink-soft);
  margin-top:6px;line-height:1.5}
.ask em::before{content:"Listening for ";font-family:"IBM Plex Mono",monospace;
  font-size:0.66rem;letter-spacing:0.09em;text-transform:uppercase;color:var(--ink-faint)}

/* ---------- the atlas at the top of the page ---------- */
.atlas{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:8px;margin:26px 0 0}
.atlas a{display:block;background:var(--surface);border:1px solid var(--line);
  border-top:3px solid var(--sc,var(--l2));padding:10px 13px;text-decoration:none}
.atlas a:hover{border-color:var(--accent);border-top-color:var(--accent)}
.atlas .n{font-family:"IBM Plex Mono",monospace;font-size:0.63rem;letter-spacing:0.1em;
  text-transform:uppercase;color:var(--ink-faint)}
.atlas .t{display:block;font-family:"Bricolage Grotesque",sans-serif;font-size:0.98rem;
  font-weight:600;color:var(--ink);margin-top:3px;line-height:1.25}
.atlas .d{display:block;font-size:0.8rem;color:var(--ink-soft);margin-top:5px;line-height:1.4}
.atlas a:nth-child(3n+1){--sc:var(--l1)}
.atlas a:nth-child(3n+3){--sc:var(--l3)}

/* the page's title is long, so the bar carries a short form for a narrow screen.
   The other pages that do this keep the rule beside their language switch; this
   page has no switch, so the rule lives here. */
.m-short{display:none}
@media (max-width:760px){
  .m-full{display:none}
  .m-short{display:inline}
}
@media (max-width:640px){.syl{grid-template-columns:1fr}}
</style>
"""
