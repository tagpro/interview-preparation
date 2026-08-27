# The Backend Ladder

Seven long-form HTML pages on backend engineering, served by GitHub Pages at
`study.jaspreet.info/software-engineering/`, plus the toolchain that builds them
in `build/`.

## Layout

    *.html          the published site -- GENERATED, never edit by hand
    README.md       what the series is, for github.com
    build/          sources, build scripts, the three passes, the checks
    build/PIPELINE.md   how the build works, in detail

`index.html` is the hub page (`build/backend-go-ladder.html`), not a listing.

One level up, `../index.html` and `../404.html` are the site's front page and
error page. They are **hand-written, not generated** -- they belong to the site
rather than to this series, and nothing regenerates them. `node
build/docs_check.mjs ..` checks their links and structure. Adding a page here
means adding a card to `../index.html` by hand.

## What is source and what is generated

The seven `build/*.html` **pages** are the source of truth for their prose and
markup. Four of them are also assembled from fragments (`build_py.py`,
`build_java.py`, `build_aws.py` read `py_*.html`, `java_*.html`, `aws_*.html`;
`build_go.py` rebuilds `pillar-b-go.html` from itself). The three pillar pages
have no fragments -- they *are* the source.

The seven files at the top of this directory are output. Editing them is always
wrong: the next `site_build.mjs` overwrites them.

## Building

    cd build
    npm install                       # once
    pip install -r requirements.txt   # pymupdf, for the print checks only
    python3 build_go.py && python3 build_py.py && python3 build_java.py && python3 build_aws.py
    node hl_inject.mjs                # syntax highlighting
    node print_inject.mjs             # print stylesheet
    python3 gloss_inject.py           # abbreviation glossary
    node site_build.mjs ..            # wrap as standalone HTML, write the site

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
    node site_check.mjs ..            # the built site: links, passes, structure
    node print_ink.mjs                # print colours survive Chrome's pipeline
    node print_pdf.mjs && python3 print_check.py 'pdf/*.pdf'

`node fonts_fetch.mjs` first if you are rendering PDFs -- font metrics decide
where code lines wrap, and the fallback mono measures a different document.

## Constraints that are easy to break

- **No runtime dependencies.** Highlighting happens at build time; the pages
  ship spans and CSS. Nothing is fetched but the Google Fonts stylesheet.
- **Both themes, always.** Every colour token is defined on bare `:root` and
  redefined for `prefers-color-scheme: dark` and `[data-theme="dark"]`. A colour
  whose only definition sits inside a media query is a bug.
- **Chrome rewrites some colours on the way to the printer.** `#6F42AF` lands at
  half its brightness. Never add a print colour without `print_ink.mjs`.
- **The site pass rewrites the series links.** Pages carry `claude.ai/code/...`
  URLs because they are also published as artifacts; `site_build.mjs` maps them
  to local filenames and fails if one is unrecognised. Adding a page means
  adding it to `PAGES` there and to the `toc-series` block in each page.
- **`build/` is served too.** It sits inside the Pages directory, so anything
  added there is publicly fetchable. Keep credentials out of it.
