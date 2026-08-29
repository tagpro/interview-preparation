# The Backend Ladder

Eight long-form HTML pages on backend engineering, served by GitHub Pages at
`study.jaspreet.info/software-engineering/`, plus the toolchain that builds them
in `build/`.

## Layout

    *.html          the published site -- GENERATED, never edit by hand
    README.md       what the series is, for github.com
    build/          sources, build scripts, the three passes, the checks
    build/PIPELINE.md   how the build works, in detail

`index.html` is the hub page (`build/backend-go-ladder.html`), not a listing.

One level up: `../fonts/` holds the site's self-hosted typefaces and `../sw.js`
its offline cache -- both **generated**, by `build/fonts_local.mjs` and
`build/sw_build.mjs`. `../index.html` and `../404.html` are the site's front page
and error page; they are **hand-written, not generated** -- they belong to the site
rather than to this series, and nothing regenerates them. `node
build/docs_check.mjs ..` checks their links and structure. Adding a page here
means adding a card to `../index.html` by hand.

## What is source and what is generated

The eight `build/*.html` **pages** are the source of truth for their prose and
markup. Five of them are also assembled from fragments (`build_py.py`,
`build_java.py`, `build_aws.py`, `build_dsa.py` read `py_*.html`, `java_*.html`,
`aws_*.html`, `dsa_*.html`; `build_go.py` rebuilds `pillar-b-go.html` from
itself). The three pillar pages have no fragments -- they *are* the source.

The cross-link rail every page carries is generated from `series.py`, which is
the one list of pages in the series. `series_sync.py` writes it into all eight,
including the three that have no build script.

The eight files at the top of this directory are output. Editing them is always
wrong: the next `site_build.mjs` overwrites them.

## Building

    cd build
    npm install                       # once
    pip install -r requirements.txt   # pymupdf, for the print checks only
    python3 build_go.py && python3 build_py.py && python3 build_java.py
    python3 build_aws.py && python3 build_dsa.py
    python3 series_sync.py            # the cross-link rail, from series.py
    node hl_inject.mjs                # syntax highlighting
    node print_inject.mjs             # print stylesheet
    python3 gloss_inject.py           # abbreviation glossary
    node site_build.mjs ..            # wrap as standalone HTML, write the site
    node sw_build.mjs ../..           # the offline cache -- always last

A rebuild from fragments drops all three injected blocks, so the passes always
run after `build_*.py`. Each pass strips its own previous block instead of
stacking, and the three together reach a fixed point -- `./pipeline_check.sh`
asserts that, and it is the check that catches a pass quietly growing the file.

## Checks

Run what the change touches; run all of them before publishing.

    ./pipeline_check.sh               # the passes converge
    node hl_contrast.mjs              # every token colour clears 4.5:1
    node hl_verify_dim.mjs            # no text that used to be dimmed lost it
    node audit2.mjs                   # SVG geometry -- must print TOTAL: 0
    node verify_gloss.mjs             # glossary wraps, misplaced: 0
    node verify_aws.mjs               # the Go/Python switch covers every pair
    python3 series_sync.py --check    # no page's rail has drifted from series.py
    node site_check.mjs ..            # the built site: links, passes, structure
    node offline_check.mjs ../..      # no page reaches for the network at all
    node sw_check.mjs ../..           # install the cache, stop the server, walk every page
    node print_ink.mjs                # print colours survive Chrome's pipeline
    node print_pdf.mjs && python3 print_check.py 'pdf/*.pdf'

`print_pdf.mjs` uses the site's own faces from `../fonts/`, because font metrics
decide where code lines wrap and the fallback mono measures a different
document.

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
- **Chrome rewrites some colours on the way to the printer.** `#6F42AF` lands at
  half its brightness. Never add a print colour without `print_ink.mjs`.
- **The site pass rewrites the series links.** Pages carry `claude.ai/code/...`
  URLs because they are also published as artifacts; `site_build.mjs` maps them
  to local filenames and fails if one is unrecognised. Adding a page means one
  entry in `series.py`, one run of `series_sync.py`, one entry in `PAGES` in
  `site_build.mjs`, `hl_detect.mjs` and `gloss_inject.py`, and one card in
  `../index.html`.
- **Nothing on the algorithms page autoplays, and that is load-bearing.** Its
  eleven figures are precomputed traces with a fixed opening frame, so the
  printed page does not depend on when Chrome took the snapshot -- which is what
  lets `print_same.py` compare two renders at all. A figure that started itself
  would also be noise beside the paragraph explaining it.
- **`build/` is served too.** It sits inside the Pages directory, so anything
  added there is publicly fetchable. Keep credentials out of it.
