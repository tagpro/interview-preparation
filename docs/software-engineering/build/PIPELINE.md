# Build pipeline for the Backend Ladder series

Seven pages. Four are assembled from fragments; two carry no code; the hub is
hand-maintained. Three post-processing passes run over the **built** HTML.

Node dependencies are in `package.json` (`npm install`); the print checks also
need `pymupdf` (`pip install -r requirements.txt`). Nothing else does.

## Order

    python3 build_go.py / build_py.py / build_java.py / build_aws.py   # if fragments changed
    node   hl_inject.mjs      # syntax highlighting  -> <!-- highlight --> block
    node   print_inject.mjs   # print stylesheet      -> <!-- print --> block
    python3 gloss_inject.py   # abbreviation glossary -> <!-- glossary --> block
    node   site_build.mjs ..  # wrap as standalone HTML and write the site
    node   sw_build.mjs ../.. # regenerate the offline cache

All three passes are re-runnable and strip their own previous block instead of
stacking a second one, so running them again is always safe. `hl_inject.mjs`
and `print_inject.mjs` place their blocks *before* the glossary marker, so
`gloss_inject.py` (which rewrites everything from its marker to end of file)
cannot clobber them, and the order among the three does not matter.

**A rebuild drops all three blocks and the highlight spans. Re-run every pass
after any `build_*.py`.**

The three passes also have to compose to a fixed point. Each splices its block
in ahead of the next marker, so left to themselves they leapfrog and the file
grows a newline every full run; all three normalise the gap before a marker
identically to prevent it. `./pipeline_check.sh` runs the whole pipeline twice
in a scratch copy and asserts the second run changes nothing.

## Syntax highlighting

`@tanstack/highlight` v0.0.10, run at build time only. The pages ship plain
`<span>` markup plus one block of CSS and load no highlighter at runtime, so the
artifact CSP is untouched and the reader downloads no extra JavaScript.

| File | What it is |
| --- | --- |
| `hl_langs.mjs` | Go, Java, go.mod, Terraform and console definitions, plus the `withCodas` wrapper |
| `hl_detect.mjs` | Per-block language detection, page defaults, fingerprint overrides |
| `hl_theme.mjs` | Light and dark token palettes drawn from the series' own `--l1/--l2/--l3` |
| `hl_inject.mjs` | The pass itself |
| `hl_report.mjs` | Prints the language assigned to all 244 blocks |
| `hl_contrast.mjs` | Asserts every token colour clears 4.5:1 (3.5:1 for comments) |
| `hl_verify_dim.mjs` | Asserts no text the pages used to dim lost its dimming |

| Print file | What it is |
| --- | --- |
| `print.css` | The stylesheet, one `@media print` block |
| `print_theme.mjs` | Print palette, derived from `hl_theme.mjs` |
| `print_inject.mjs` | The pass itself |
| `print_ink.mjs` | Asserts Chrome's print pipeline writes the colour that was asked for |
| `print_pdf.mjs` | Renders all seven to PDF the way Ctrl-P would |
| `print_check.py` | Asserts nothing is clipped and no page came out blank |
| `print_contrast.py` | Reads the colours back out of the PDF and checks them against white |
| `print_same.py` | Asserts a dark-themed browser prints the same ink as a light one |
| `print_sheet.py` / `print_page.py` | Contact sheet and single-page renders, for looking at it |
| `fonts_local.mjs` | Self-hosts the site's fonts, keeping only the subsets it uses |

| Site file | What it is |
| --- | --- |
| `site_build.mjs` | Wraps the fragments as standalone HTML and rewrites cross-links |
| `site_check.mjs` | Loads every built page and checks structure, links and the passes |
| `sw_build.mjs` | Generates the service worker, its cache named by a content hash |
| `sw_check.mjs` | Installs it, stops the server, and walks every page |
| `offline_check.mjs` | Asserts no page reaches for the network in the first place |
| `pipeline_check.sh` | Asserts the three passes compose to a fixed point |
| `manifest.txt` | The files this directory needs; the rest of the working tree is scratch |

### Why there are custom languages

The bundled set is web-oriented and ships neither Go nor Java, which together
cover 117 of the 244 blocks; `go.mod` and Terraform appear once each. The
bundled `shell` is written for shell *scripts* and lexes a quote as opening a
string that runs to the next quote anywhere later in the block, so an apostrophe
in prose output ("the compiler's own lint") swallowed every comment after it.
`console` replaces it: comments win first, strings cannot cross a line, and
output lines are dimmed as whole lines the way these pages have always shown
them.

`withCodas` handles the series' habit of appending a short coda in another
language to a snippet -- a YAML setting after a Java class, a JPA mapping after
a SQL migration -- introduced by a `#` or `//` comment the host language does
not recognise. It adds those comments to every language after that language's
own tokenizer has run, and never touches a `#` inside a string.

### Checks

`hl_inject.mjs` asserts per block that the decoded code text is unchanged by the
round trip; it refuses to write a block that fails. Run the three verifiers
after any change:

    node hl_contrast.mjs && node hl_verify_dim.mjs && node audit2.mjs

## Print

`print_inject.mjs` gives every page an `@media print` block: about 6 KB of CSS
and no markup change. `print.css` is the stylesheet; `print_theme.mjs` holds the
palette and derives from `hl_theme.mjs`, so the screen and print token sets
cannot drift apart.

What it has to deal with, in the order the stylesheet addresses it:

| Problem | What print does |
| --- | --- |
| A printer has no dark mode | Pins every design token to its light value. Chrome prints with "Background graphics" off by default, so a page printed from a dark theme would otherwise be pale text on unprinted white |
| Chrome darkens light *text* so it survives on paper | Nothing -- but `print_ink.mjs` checks it, because it rewrites some mid-tone colours too, and `--th-type` was landing at half its brightness |
| The sticky bar, the progress meter and the tooltip mean nothing on paper | Dropped |
| The contents rail is a fixed side rail, last in the DOM | Becomes front matter: the body is a flex column purely to reorder it after the title page |
| A scroll bar is a clip on paper | `pre` wraps, figures and table wrappers stop scrolling |
| `auto-fit` grids were sized for a desktop width | Column counts pinned. Chrome will not split a grid row across pages, so a three-card set that becomes 2 + 1 spills half a page of white -- this alone took the Python page from 99 pages to 69 |
| Auto table layout starves the prose column | The key column asks for the narrowest fit; snippets in later columns may wrap |
| The abbreviation expansions live in a tooltip | Spelled out inline at each first mention, from the same `data-full` the tooltip reads |
| The AWS page hides half its snippets behind a switch in the bar | Prints what is on screen, and says which half on the title page |

### Checks

    node print_ink.mjs                 # every print colour survives Chrome's print pipeline
    node print_pdf.mjs                 # render all seven the way Ctrl-P would
    node print_pdf.mjs --dark          # ... from a dark-themed browser
    node print_pdf.mjs --bg            # ... with background graphics on
    node print_pdf.mjs --letter        # ... on US Letter
    python3 print_check.py  'pdf/*.pdf'   # nothing clipped, no blank or near-blank pages
    python3 print_contrast.py 'pdf/*.pdf' # every colour that reached the paper, against white
    python3 print_sheet.py pdf/x.pdf out.png 8   # contact sheet, for looking at it

    python3 print_same.py                 # a dark-themed browser prints the same ink

`print_pdf.mjs` serves the site's own faces from `docs/fonts/` rather than the
network, because font metrics decide where code lines wrap and a fallback mono
would measure the wrong thing. Pass a different stylesheet as an argument to
override it.

## The site

`site_build.mjs` turns the seven built pages into a standalone static site.

The pages are artifact *fragments*: no `<!doctype>`, no `<html>`, no `<head>` --
the artifact host supplies those and puts the whole file in `<body>`. The pass
lifts only the `<title>` and the three font links into a real head and leaves
everything else in the order the host renders it, so what ships matches what was
verified. It also rewrites the series cross-links, which point at
`claude.ai/code/artifact/...` because the pages are published as artifacts too,
and fails if any URL is left unresolved.

| Page | File |
| --- | --- |
| The Backend Ladder | `index.html` |
| The Machine Room | `foundations.html` |
| Reading Go | `go.html` |
| From Account to Pod | `cloud.html` |
| Python, End to End | `python.html` |
| Java, Then Spring | `java.html` |
| AWS, Service by Service | `aws.html` |

Adding a page means adding it to `PAGES` in `site_build.mjs` and to the
`toc-series` block each page carries.

### Offline

The served site loads nothing over the network. Its only external resource was
the Google Fonts stylesheet, and `fonts_local.mjs` replaces it: the same faces,
self-hosted under `docs/fonts/`, trimmed to the unicode subsets the pages
actually render.

Those subsets are counted from the **rendered DOM**, not the source. The pages
are written with HTML entities, and several glyphs -- the contents tick, the run
marker -- exist only as CSS generated content; counting the source alone drops
the greek subset that the pages need for lambda and rho.

The stylesheet's `url()`s are relative to itself, so one copy serves every page
whatever its depth, from a web server or straight off disk. The artifacts keep
the Google link, since that is the only host their CSP allows.

    node fonts_local.mjs ../..        # refresh docs/fonts/ from upstream
    node offline_check.mjs ../..      # every page loads with the network blocked

### The offline cache

`sw_build.mjs` generates `docs/sw.js`. It is generated rather than written for
one reason: a service worker's cache name has to change whenever any cached file
changes, or a visitor is served the old site forever. The name here is a hash of
the contents of everything it precaches, so it cannot drift from what it holds.

The site is small and entirely static, so the worker precaches all of it on
install -- 22 files, 2.8 MB. One visit to the front page makes all seven deep
dives readable offline, not just the pages that happened to be opened. Requests
are served cache-first; a navigation to something never cached gets the site's
own 404 page rather than the browser's error screen.

There is no manifest and no install prompt: the site is a set of documents to
read offline, not an app to install.

    node sw_build.mjs ../..           # regenerate after ANY change to a served file
    node sw_check.mjs ../..           # install it, stop the server, walk every page

`sw_check.mjs` takes the network away by **shutting the server down**, not by
asking the browser to pretend. Playwright's offline emulation does not reliably
reach a service worker's own fetches -- under it, pages still being served over
the network looked like cache hits. With the server stopped, nothing but the
cache can answer.


    node site_check.mjs ..    # loads every built page: structure, links, passes
