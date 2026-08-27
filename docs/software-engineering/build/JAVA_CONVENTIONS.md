# House style for the Java + Spring Boot artifact — "Java, Then Spring"

You are writing ONE HTML fragment file. It is assembled later into a full page by a
build script that supplies `<head>`, all CSS, the topbar, the contents rail and the
scripts. **Write only the `<section class="part">` blocks in your brief.**
No `<html>`, `<head>`, `<style>`, `<script>`, no doctype.

## Page identity — READ THIS, IT DIFFERS FROM THE SIBLINGS
Title: "Java, Then Spring". A TUTORIAL page: the reader learns Java and Spring Boot
by actually running every block of code locally. Sixth sibling of a series about
backend foundations, Go, AWS/Kubernetes and Python — cross-references to "the same
idea in Go/Python" are welcome where genuinely true.

**The ladder is the page, not the section.** Unlike the sibling pages there are NO
per-topic L1/L2/L3 level-card grids — do NOT write `<div class="levels">` or
`<article class="lvl ...">` anywhere. Instead the whole page climbs from beginner
(part one) to advanced (part ten). Assume the reader has read every part before
yours and nothing after. It is fine — encouraged — for one topic to merge two or
three related concepts of the same level into a single narrative.

**Tutorial voice.** Code blocks may be long (up to ~40 lines) when they form a
complete, runnable step. Every topic must leave the reader with something they can
run. Directions to run are mandatory, in this exact shape:

```html
<div class="note run">
  <h4>Run it</h4>
  <p>One or two sentences: what to do and what you should see.</p>
</div>
<pre class="l1">$ sdk install java 21.0.5-tem
$ java --version
<span class="c">openjdk 21.0.5 2024-10-15 LTS   &larr; what success looks like</span></pre>
```
Shell blocks use `$ ` prefixes; expected output lines go in `<span class="c">…</span>`.

## The running example (parts 6–9 share it — keep it EXACT)
A task-tracker service, package `dev.ladder.tasks`, artifact `tasks`.
Domain: `Task(UUID id, String title, boolean done, Instant createdAt)`.
Endpoints: `POST /tasks`, `GET /tasks`, `GET /tasks/{id}`, `PATCH /tasks/{id}/done`.
Toolchain: **Java 21 (Temurin via sdkman)**, **Spring Boot 3.5.x**, Maven.
Part five uses plain `mvn` (installed via `sdk install maven`) on a small library
project; parts six onward use `./mvnw` from the generated Spring project. Postgres
runs via `docker compose` (image `postgres:16`); migrations via Flyway.
Mention once (part one) that Java 25 is the newest LTS and 21 is what most
production runs; write everything against 21.

## Exact structure of a part

```html
<section class="part" id="PART-ID">
  <div class="shell">
    <div class="part-head">
      <span class="kicker">Part one</span>
      <h2>Part title</h2>
      <p class="stage s1">L1 &middot; Beginner</p>
      <p>One short paragraph framing the part.</p>
    </div>

    <section class="topic" id="TOPIC-ID">
      <div class="topic-head">
        <span class="kicker">Java &middot; 00</span>
        <h3>Topic title</h3>
        <p class="lede">One or two sentences. Say the mechanism, not a definition.</p>
      </div>

      <figure> ...inline SVG... <figcaption><b>Lead-in.</b> Why it matters.</figcaption></figure>
      <pre class="l2">...code...</pre>
      <div class="note run"><h4>Run it</h4><p>...</p></div>
      <pre class="l1">$ ...</pre>
      ...more prose/notes/tables/code as the tutorial needs...
    </section>
  </div>
</section>
```

- `<p class="stage s1|s2|s3">` — the part's rung: `s1` = L1, `s2` = L2, `s3` = L3.
  Text like `L1 &middot; Beginner` or `L2 &rarr; L3` for bridge parts. CSS exists.
- **Leave kickers as `Part one` / `Java &middot; 00`** — renumbered automatically later.
- Every topic MUST have: topic-head, at least one `<figure>` with an SVG, at least
  one substantial code block, and at least one "Run it" pair. 6–14&nbsp;KB per topic.

## Other blocks you may use (CSS already exists)
- `<div class="tablewrap"><table><thead>…</thead><tbody>…</tbody></table></div>`
- `<div class="note"><h4>..</h4><p>..</p></div>` and `<div class="note warn">..</div>`
- `<div class="callout"><h4>..</h4><p>..</p></div>`
- `<div class="pair">` — two side-by-side `.note` blocks
- `<ol class="steps"><li><b>Lead</b> rest.</li></ol>`

## SVG rules — a geometry audit WILL fail you
- `<svg viewBox="0 0 900 H" role="img" aria-label="A sentence describing the picture.">`
  Width always 900; H typically 240–400.
- Colour ONLY via wrapper groups `<g class="svg-l1|svg-l2|svg-l3">` +
  `fill="currentColor"`/`stroke="currentColor"`. **Zero literal hex colours.**
  svg-l1 = good/normal path · svg-l2 = neutral/secondary · svg-l3 = hazard/cost.
- Fonts: `font-family="IBM Plex Mono, monospace"` for code/labels (sizes 8–10.5),
  `"IBM Plex Sans, sans-serif"` for prose (10–12),
  `"Bricolage Grotesque, sans-serif"` for a bold in-figure heading (12–14).
- Arrow marker id must be globally unique — use YOUR ASSIGNED PREFIX:
  `<defs><marker id="PREFIX-1" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" fill="currentColor"/></marker></defs>`
- A `<rect>` drawn over an earlier line gets `class="plate"` (background fill).
- **Text must fit**: mono ≈ 5.7 units/char at size 9.5; sans ≈ 5.3 at 11. Keep every
  `<text>` inside the viewBox and its own box; break long sentences into several
  `<text>` lines; never let two texts on one baseline touch; never run a line
  through text. One diagram per topic is enough — show a MECHANISM (a flow, a
  before/after, a lifecycle), not decorative labelled boxes.

## Escaping — non-negotiable
In prose and SVG: `&mdash; &ndash; &rarr; &larr; &middot; &times; &ldquo; &rdquo;
&rsquo; &hellip;`; never a bare `&` or `<`. Apostrophes as `&rsquo;`.
In `<pre>`: escape `<` `>` `&` as `&lt; &gt; &amp;` — Java generics
(`List&lt;String&gt;`), lambdas (`-&gt;`), `&amp;&amp;`. Comments/annotations inside
pre use `<span class="c">// …</span>` (Java) or `<span class="c"># …</span>` (shell/yaml).
Pre classes: `l1` for shell/run blocks and plain basics, `l2` for the main tutorial
code, `l3` for gotcha/trap demonstrations.

## Voice
British spelling. Declarative and specific. Numbers where real. No emoji, no
"simply". Prefer "here is what bites you" over definitions. The reader can already
program (they have read the Python and Go pages); teach Java, not programming.

## Self-check before you finish (run it, fix failures)
```bash
python3 - <<'EOF'
import xml.dom.minidom, re
s = open('YOURFILE', encoding='utf-8').read()
ents = {'&mdash;':'-','&ndash;':'-','&rarr;':'~','&larr;':'~','&middot;':'.','&hellip;':'.',
        '&rsquo;':chr(39),'&ldquo;':chr(34),'&rdquo;':chr(34),'&times;':'x','&nbsp;':' ','&ge;':'~','&le;':'~'}
bad = 0
for i, m in enumerate(re.finditer(r'<svg.*?</svg>', s, re.S)):
    t = m.group(0)
    for k, v in ents.items(): t = t.replace(k, v)
    try: xml.dom.minidom.parseString(t)
    except Exception as e: print('SVG', i, 'FAIL', e); bad += 1
assert not re.findall(r'#[0-9a-fA-F]{3,6}\b', s), 'literal hex colour found'
assert s.count('<pre') == s.count('</pre>')
assert '<div class="levels">' not in s, 'no level-card grids on this page'
for i, m in enumerate(re.finditer(r'<pre[^>]*>(.*?)</pre>', s, re.S)):
    body = re.sub(r'</?span[^>]*>', '', m.group(1))
    st = body.replace('&lt;','').replace('&gt;','').replace('&amp;','').replace('&rarr;','').replace('&mdash;','').replace('&hellip;','')
    assert '<' not in st and '>' not in st, ('raw angle bracket in pre %d' % i)
print('svgs=%d topics=%d pre=%d run=%d bytes=%d bad=%d' % (
  len(re.findall(r'<svg', s)), len(re.findall(r'class="topic"', s)),
  len(re.findall(r'<pre', s)), len(re.findall(r'note run', s)), len(s), bad))
EOF
```
