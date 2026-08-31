# The Backend Ladder

Ten long-form HTML pages -- nine on backend engineering and one mapping the
interviews it all gets tested in -- served by GitHub Pages at
`study.jaspreet.info/software-engineering/`, plus the toolchain that builds them
in `build/`.

## Layout

    *.html          the published site -- GENERATED, never edit by hand
    README.md       what the series is, for github.com
    build/          sources, build scripts, the three passes, the checks
    build/PIPELINE.md   how the build works, in detail

`index.html` is the hub page (`build/backend-go-ladder.html`), not a listing.
It is also where the design system lives: `tpl.py` lifts the hub's `<style>`
blocks verbatim so the seven built pages cannot drift from it. A change to a token,
a type rule or a colour therefore has to be made in the hub **and** in the two
other pages with no build script -- `pillar-a-foundations.html` and
`pillar-c-cloud.html` -- which carry their own copy. Prose is set at
`font-weight:500`; `pre` and `code` pin themselves back to 400, so the weight is
a decision about reading prose and not about how code looks.

One level up: `../fonts/` holds the site's self-hosted typefaces and `../sw.js`
its offline cache -- both **generated**, by `build/fonts_local.mjs` and
`build/sw_build.mjs`. `../index.html` and `../404.html` are the site's front page
and error page; they are **hand-written, not generated** -- they belong to the site
rather than to this series, and nothing regenerates them. `node
build/docs_check.mjs ..` checks their links and structure. Adding a page here
means adding a card to `../index.html` by hand.

## What is source and what is generated

The ten `build/*.html` **pages** are the source of truth for their prose and
markup. Seven of them are also assembled from fragments (`build_py.py`,
`build_java.py`, `build_aws.py`, `build_dsa.py`, `build_ai.py`, `build_iv.py`
read `py_*.html`, `java_*.html`, `aws_*.html`, `dsa_*.html`, `ai_*.html`,
`iv_*.html`; `build_go.py` rebuilds `pillar-b-go.html` from itself). The three
pillar pages have no fragments -- they *are* the source.

`build_go.py` is the odd one and the difference matters when editing it. It
explodes the built page and splices two fragments back in. `go_cook.html` is
spliced only if absent, because its blocks were edited on the built page after
that fragment was extracted and the two have drifted -- the page wins.
`go_svc.html` is *replaced* on every build, so it stays the source of truth for
part ten and an edit there actually reaches the page. Edit the right one.

The cross-link rail every page carries is generated from `series.py`, which is
the one list of pages in the series. `series_sync.py` writes it into all ten,
including the three that have no build script.

The ten files at the top of this directory are output. Editing them is always
wrong: the next `site_build.mjs` overwrites them.

## Building

    cd build
    npm install                       # once
    python3 build_go.py && python3 build_py.py && python3 build_java.py
    python3 build_aws.py && python3 build_dsa.py && python3 build_ai.py
    python3 build_iv.py
    python3 series_sync.py            # the cross-link rail, from series.py
    python3 theme_sync.py             # the colour-theme switch, from theme_ui.py
                                      # (writes theme_block.html for site_build)
    node hl_inject.mjs                # syntax highlighting
    node print_inject.mjs             # print stylesheet
    python3 gloss_inject.py           # abbreviation glossary
    node site_build.mjs ..            # wrap as standalone HTML, write the site
    node sw_build.mjs ../..           # the offline cache -- always last

A rebuild from fragments drops all three injected blocks and the rail, so
`series_sync.py` and the injection passes always run after `build_*.py`.
`theme_sync.py` does not touch those pages at all -- see below. Each pass strips its own previous block instead of
stacking, and the three together reach a fixed point -- `./pipeline_check.sh`
asserts that, and it is the check that catches a pass quietly growing the file.

## Checks

Run what the change touches; run all of them before publishing.

    ./pipeline_check.sh               # the passes converge
    node hl_contrast.mjs              # every token colour clears 4.5:1
    node hl_verify_dim.mjs            # no text that used to be dimmed lost it
    node audit2.mjs                   # SVG geometry -- must print TOTAL: 0
    node verify_gloss.mjs             # glossary wraps, misplaced: 0
    python3 esc_pre.py --check ai_*.html iv_*.html py_svc.html java_svc.html \
        go_svc.html                   # no bare < or > inside a code block
    node verify_aws.mjs               # the Go/Python switch covers every pair
    python3 series_sync.py --check    # no page's rail has drifted from series.py
    python3 theme_sync.py --check     # nor has any page's theme switch
    node theme_check.mjs ../..        # the switch changes the page and survives a reload
    node site_check.mjs ..            # the built site: links, passes, structure
    node offline_check.mjs ../..      # no page reaches for the network at all
    node sw_check.mjs ../..           # install the cache, stop the server, walk every page

## Constraints that are easy to break

- **The site fetches nothing.** Highlighting happens at build time; the pages
  ship spans and CSS, and the fonts are served from `../fonts/`. `offline_check.mjs`
  asserts it by aborting every non-file request. The *artifacts* still link
  Google Fonts -- that is the only host their CSP allows and they have nowhere
  to put a file -- so `site_build.mjs` swaps that link when it builds the site,
  and fails if the link it expects is not there.
- **`sw.js` must be regenerated after any change to a served file.** Its cache is
  named by a hash of everything it holds; a stale worker serves the old site
  forever. `sw_build.mjs` is the last step of a build, after `site_build.mjs`.
- **The site is not installable, on purpose.** There is no manifest and no
  install prompt -- these are documents to read offline, not an app.
- **Adding a glyph can mean adding a font subset.** `fonts_local.mjs` keeps only
  the subsets the pages' rendered text uses, counted from the DOM (the pages are
  written with entities, and some glyphs exist only as CSS content). Re-run it
  after adding text in a new script.
- **Both themes, always.** Every colour token is defined on bare `:root` and
  redefined for `prefers-color-scheme: dark` and `[data-theme="dark"]`. A colour
  whose only definition sits inside a media query is a bug.
- **Three theme states, not two.** Bare `:root` is light, the
  `prefers-color-scheme` block guarded as `:root:not([data-theme="light"])`
  follows the system, and `:root[data-theme="dark"]` overrides both. The switch
  in `theme_ui.py` writes that attribute and removes it again for "system"; a
  two-state toggle would throw the follow-the-system behaviour away.
- **The theme switch is a site feature, not a page feature.** The pages are
  also published as artifacts, where the claude.ai host provides its own theme
  control and stamps the same `data-theme` attribute -- two writers for one
  attribute is a fight. So `site_build.mjs` splices the switch in as it writes
  the site, next to the font swap and the service-worker registration, and the
  nine `build/*.html` pages never carry it. `theme_sync.py` writes it into the
  site's two hand-written pages and regenerates `theme_block.html`, which
  `site_build.mjs` reads and refuses to build without.
- **The way home is a site feature too.** These pages are also published as
  artifacts, where there is no front page to go back to, so `site_build.mjs`
  splices the home link into the top bar as it writes the site -- beside the font
  swap, the service-worker registration and the theme switch. It is a plain
  anchor rather than a scripted control, so it survives JavaScript being off, and
  it is sticky to the left edge for the same reason Contents is sticky to the
  right: the bar scrolls sideways on a phone and the two ways out of a page
  should not be what scrolls away. `site_check.mjs` asserts every built page
  carries exactly one and that it resolves to a file that exists.
- **Chrome rewrites some colours on the way to the printer.** `#6F42AF` lands at
  half its brightness, which is why `print_theme.mjs` uses `#6A3FA8` instead.
  That was measured; the tooling that measured it is gone, so a new print colour
  is now an untested guess. Prefer reusing a value already in the palette.
- **The site pass rewrites the series links.** Pages carry `claude.ai/code/...`
  URLs because they are also published as artifacts; `site_build.mjs` maps them
  to local filenames and fails if one is unrecognised. Adding a page means one
  entry in `series.py`, one run of `series_sync.py`, one entry in `PAGES` in
  `site_build.mjs`, `hl_detect.mjs`, `gloss_inject.py` and `verify_gloss.mjs`,
  one card in `../index.html`, one row in `README.md`, and -- if the page brings
  components of its own -- a block of print rules in `print_inject.mjs`, because
  an `auto-fit` grid that was never pinned spills half a page of white.
- **Nothing on the interactive pages autoplays, and that is load-bearing.** The
  twenty-six figures on the algorithms and AI pages are precomputed traces with
  a fixed opening frame, or calculators whose knobs start at fixed values, so
  a run of the build produces the same page twice and a figure is never caught
  mid-animation by a screenshot. A figure that started itself would also be
  noise beside the paragraph explaining it.
- **The player and the figure chrome live in `demo_ui.py`, once.** Both
  interactive pages import it; each supplies only its own stage CSS and its own
  demos. It also generates the language switch, which is why the two pages can
  offer different language sets (`lang-go|py|java` under `ladder-lang`,
  `ai-py|ts|go` under `ai-lang`) without a second copy of the behaviour.
- **Code fragments are written with bare `<`, `>` and `&`, and `esc_pre.py`
  escapes them.** A bare `<` inside a `<pre>` is a tag to every regex-based pass
  downstream; the highlighter silently loses the text after it. The pass is
  idempotent and `--check` fails the build if a fragment was edited without
  re-running it.
- **`build/` is served too.** It sits inside the Pages directory, so anything
  added there is publicly fetchable. Keep credentials out of it.

## The interview map

`interview-map.html` is the tenth page and the only one that is a syllabus
rather than a subject. It brings three components the shared design system does
not have -- `.syl`, `.chips` and `.ask`, all in `iv_ui.py` -- and `build_iv.py`
splices that CSS in ahead of the top bar the way `build_aws.py` splices its
language switch. Two of its own assertions are worth knowing about: the atlas at
the top of the page must name every part in document order, and the topic
kickers are renumbered on every build from a placeholder word, so a topic can be
moved between fragments without being renumbered by hand.
