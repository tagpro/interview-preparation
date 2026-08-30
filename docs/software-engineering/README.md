# The Backend Ladder

Nine pages on backend engineering, written to be read in order or dipped into.
Published at **[study.jaspreet.info/software-engineering/](https://study.jaspreet.info/software-engineering/)**.

| Page | What it covers |
| --- | --- |
| [The Backend Ladder](index.html) | The overview, and the map of the other seven |
| [The Machine Room](foundations.html) | Latency, concurrency, caching, storage, failure, capacity |
| [Reading Go](go.html) | Slices, escape analysis, context, the timeouts a server is missing |
| [From Account to Pod](cloud.html) | An AWS account, a VPC, a container, and the path a request takes |
| [Python, End to End](python.html) | The object model, the GIL, typing, packaging, production |
| [Java, Then Spring](java.html) | The JVM, the language, the build, and Spring Boot on top |
| [AWS, Service by Service](aws.html) | What each service does when your code calls it, in Go and Python |
| [Data Structures, In Motion](algorithms.html) | Every structure and algorithm worth knowing, with figures that run, in Go, Python and Java |
| [Prompt to Production](ai-engineering.html) | The concepts an AI engineer is hired for &mdash; tokens, retrieval, agents, evaluation, serving, cost &mdash; with fifteen interactive figures, in Python, TypeScript and Go |

Each page is one self-contained HTML file: no build step, no framework, and no
JavaScript beyond the contents rail, the glossary tooltips, the language switch
on the AWS, algorithms and AI pages, and the twenty-six interactive figures
on the algorithms and AI pages. No library is loaded at runtime, on any page. The site loads nothing over the network -- the typefaces
are served from `../fonts/` and everything else is inline -- and a service worker
caches the whole thing on first visit, so once you have opened it, it works
offline.

They carry a print stylesheet, so **Ctrl-P** or *Save as PDF* gives a properly
paginated document — light palette whatever your theme, code wrapped rather than
clipped, contents at the front, and every abbreviation spelled out where the
tooltip would have been. The interactive figures print too: the controls are
dropped and each figure prints the state it opens in, which is fixed, so two
copies of the same page are identical.
