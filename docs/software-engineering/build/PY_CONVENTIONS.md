# House style for the Python foundations artifact

You are writing ONE HTML fragment file. It is assembled later into a full page by a
build script that supplies `<head>`, all CSS, the topbar, the contents rail and the
scripts. **Write only the `<section class="part">` blocks described in your brief.**
No `<html>`, `<head>`, `<style>`, `<script>`, no doctype.

## Page identity
Title: "Python, End to End". A beginner-to-advanced foundations page for an engineer
who already programs and needs Python specifically. It is the fourth sibling of a
series about backend foundations, Go, and AWS/Kubernetes — so cross-references to
"the same idea in Go" or "this is the backpressure problem again" are welcome where
they are genuinely true, and never forced.

## Exact structure of a part

```html
<section class="part" id="PART-ID">
  <div class="shell">
    <div class="part-head">
      <span class="kicker">Part one</span>
      <h2>Part title</h2>
      <p>One short paragraph framing the part.</p>
    </div>

    <section class="topic" id="TOPIC-ID">
      <div class="topic-head">
        <span class="kicker">Python &middot; 00</span>
        <h3>Topic title</h3>
        <p class="lede">One or two sentences. Say the mechanism, not a definition.</p>
      </div>

      <figure> ...inline SVG... <figcaption><b>Lead-in.</b> Why it matters.</figcaption></figure>

      <pre class="l2">...optional code block...</pre>

      <div class="levels">
        <article class="lvl l1">
          <span class="badge"><span class="dot"></span>L1 &middot; Beginner</span>
          <h4>Short imperative heading</h4>
          <ul>
            <li><strong>Term</strong> &mdash; what it is, in one clause.</li>
            <li>4&ndash;6 items total.</li>
          </ul>
        </article>
        <article class="lvl l2">
          <span class="badge"><span class="dot"></span>L2 &middot; Intermediate</span>
          <h4>...</h4><ul>...</ul>
        </article>
        <article class="lvl l3">
          <span class="badge"><span class="dot"></span>L3 &middot; Advanced</span>
          <h4>...</h4><ul>...</ul>
        </article>
      </div>
    </section>

    <!-- more topics -->
  </div>
</section>
```

**Leave the kicker number as `Python &middot; 00`** — it is renumbered automatically later.
Every topic MUST have: topic-head, one `<figure>` with an SVG, and the three level cards.
A `<pre>` code block is optional but strongly encouraged where code is clearer than a picture.

## Other blocks you may use (CSS already exists for all of them)
- `<div class="tablewrap"><table><thead><tr><th>..</th></tr></thead><tbody>..</tbody></table></div>`
- `<div class="note"><h4>..</h4><p>..</p></div>` and `<div class="note warn">..</div>`
- `<div class="callout"><h4>..</h4><p>..</p></div>`
- `<div class="pair">` — two side-by-side `.note` blocks
- `<ol class="steps"><li><b>Lead</b> rest.</li></ol>`

## SVG rules — a geometry audit WILL fail you
- `<svg viewBox="0 0 900 H" role="img" aria-label="A sentence describing what the picture shows.">`
  Width is always 900. Pick H for the content (typical 240&ndash;400).
- Colour ONLY through wrapper groups: `<g class="svg-l1">`, `svg-l2`, `svg-l3`, and
  `fill="currentColor"` / `stroke="currentColor"`. **Zero literal hex colours.**
  Convention across the series: `svg-l1` = the good/normal path, `svg-l2` = the neutral
  or secondary path, `svg-l3` = the hazard, the cost, or the thing that bites.
- Fonts: `font-family="IBM Plex Mono, monospace"` for code and labels,
  `"IBM Plex Sans, sans-serif"` for prose, `"Bricolage Grotesque, sans-serif"` for a
  bold sub-heading inside the figure. Sizes 8.5&ndash;14.
- Arrow marker (id must be globally unique — use YOUR ASSIGNED PREFIX):
  `<defs><marker id="PREFIX-1" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" fill="currentColor"/></marker></defs>`
- If a box sits on top of a line you drew earlier, add `class="plate"` to the `<rect>` so
  it is filled with the page background and the line does not show through the text.
- Escape entities: `&mdash; &ndash; &rarr; &larr; &middot; &times; &ldquo; &rdquo; &lsquo; &rsquo; &hellip; &micro;`.
  Never a bare `&` or `<` anywhere. Apostrophes as `&rsquo;`.
- **Text must fit.** Mono is about 5.7 units per character at font-size 9.5; sans about
  5.3 at font-size 11. Keep every `<text>` inside the viewBox and inside its own box.
  Break long sentences into several `<text>` lines. Never let two texts on the same
  baseline overlap or touch, and never let a line or divider run through text.
- The diagram must show a MECHANISM — a flow, a before/after, a lifecycle, a comparison
  where you can point at the difference. Not a decorative list of labelled boxes.

## Code blocks
`<pre class="l1">` / `l2` / `l3` sets the left rule colour. Inside, escape `<` `>` `&`
as `&lt; &gt; &amp;`. Use `<span class="c">// comment</span>` for comments — but write
Python comments with `#`. Keep blocks under about 18 lines. Real, runnable-looking code.

## Voice
British spelling. Declarative and specific. Numbers where they are real. No marketing
language, no emoji, no "simply" or "just". Prefer "here is what bites you" over
"here is a definition". Write for someone who can already program.
