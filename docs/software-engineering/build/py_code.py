# -*- coding: utf-8 -*-
"""One worked code block for each Python topic that did not already have one."""

BLOCKS = {

"packaging": r"""<pre class="l2"><span class="c"># what `import payments.charge` actually does, once per process</span>
import sys
sys.path       <span class="c"># searched in order; "" means the current directory, first</span>
sys.modules    <span class="c"># the cache — every later import is just a dict lookup</span>

<span class="c"># payments/config.py — a module body runs exactly once, at first import</span>
print("configuring")        <span class="c"># printed once, however many modules import it</span>
SETTINGS = load_settings()  <span class="c"># module-level state is a singleton by accident</span>

<span class="c"># the guard: this file can be imported as a library AND run as a script</span>
if __name__ == "__main__":
    main()

<span class="c"># circular imports fail halfway through, not at the import line:</span>
<span class="c">#   ImportError: cannot import name 'Order' from partially initialized</span>
<span class="c">#   module 'payments.models' (most likely due to a circular import)</span>
<span class="c"># the fix is a direction, not a trick — move the shared type into its own module</span></pre>""",

"gil": r"""<pre class="l1"><span class="c"># the same work, three pools — the numbers are the whole argument</span>
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

<span class="c"># CPU-bound: threads take turns holding the GIL, so nothing is gained</span>
with ThreadPoolExecutor(8) as ex:
    list(ex.map(tokenise_row, rows))      <span class="c"># 4.1 s on 8 cores -- pure Python</span>

<span class="c"># CPU-bound: separate interpreters, separate GILs, real parallelism</span>
with ProcessPoolExecutor(8) as ex:
    list(ex.map(tokenise_row, rows))      <span class="c"># 0.6 s — and pickling costs</span>

<span class="c"># I/O-bound: the GIL is released around the syscall, so threads are fine</span>
with ThreadPoolExecutor(32) as ex:
    list(ex.map(fetch, urls))             <span class="c"># 32 sockets, one core, no problem</span>

<span class="c"># and from async code, the escape hatch for one blocking call:</span>
row = await asyncio.to_thread(legacy_driver.query, sql)</pre>""",

"choosing": r"""<pre class="l2"><span class="c"># the same fan-out three ways — choose by what the work is waiting on</span>

<span class="c"># 1. waiting on the network, and the library is async-native</span>
results = await asyncio.gather(*(fetch(u) for u in urls))

<span class="c"># 2. waiting on the network, but the library is blocking and you cannot change it</span>
with ThreadPoolExecutor(32) as ex:
    results = list(ex.map(requests.get, urls))

<span class="c"># 3. not waiting at all — burning CPU</span>
with ProcessPoolExecutor() as ex:
    results = list(ex.map(compress, chunks))

<span class="c"># the start method is a real decision, not a detail:</span>
<span class="c">#   fork   — fast, copy-on-write, UNSAFE in a process that has threads</span>
<span class="c">#   spawn  — a fresh interpreter; everything must be picklable</span>
multiprocessing.set_start_method("spawn")   <span class="c"># default on macOS/Windows only; Linux went</span>
<span class="c"># fork -&gt; forkserver in 3.14 -- set it explicitly so every platform agrees</span></pre>""",

"patterns": r"""<pre class="l1"><span class="c"># the rewrites that move the needle, and the one measurement that justifies them</span>
out = "".join(parts)                  <span class="c"># not s += x in a loop — that is quadratic</span>
seen = set(ids)                       <span class="c"># not `x in some_list` — O(n) every check</span>
by_id = {r.id: r for r in rows}       <span class="c"># index once, then look up n times</span>
total = sum(r.amount for r in rows)   <span class="c"># a generator: no intermediate list</span>

<span class="c"># hoisting an attribute lookup out of a hot loop — a real 10-20% on tight loops</span>
append = out.append
for x in data:
    append(transform(x))

<span class="c"># @cache for a pure function called with a small set of arguments</span>
@functools.cache
def tax_rate(country: str, year: int) -&gt; Decimal: ...

<span class="c"># and none of it goes in without this:</span>
<span class="c">#   python -m timeit -s "from mod import f, data" "f(data)"</span></pre>""",

"layout": r"""<pre class="l2"><span class="c"># pyproject.toml — src layout, one package, one source of truth for the version</span>
[project]
name = "payments"
version = "0.4.1"           <span class="c"># read at run time via importlib.metadata</span>

[tool.hatch.build.targets.wheel]
packages = ["src/payments"]

<span class="c"># and the check that tells you which layout you are really in:</span>
<span class="c">#   $ pip install -e . &amp;&amp; python -c "import payments; print(payments.__file__)"</span>
<span class="c">#</span>
<span class="c">#   src layout  → .../site-packages/payments/__init__.py   the installed copy</span>
<span class="c">#   flat layout → ./payments/__init__.py                   the source tree wins</span>
<span class="c">#</span>
<span class="c"># Only the first one is testing what your users will actually install.</span></pre>""",

"libraries": r"""<pre class="l1"><span class="c"># main.py — the entire stack from the diagram, wired once, closed once</span>
from contextlib import asynccontextmanager

engine  = create_async_engine(settings.database_url, pool_size=10, max_overflow=5)
Session = async_sessionmaker(engine, expire_on_commit=False)
client  = httpx.AsyncClient(timeout=httpx.Timeout(2.0))
log     = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("starting", version=__version__)
    yield                                   <span class="c"># the app serves here</span>
    await client.aclose()                   <span class="c"># reverse order, like Go's defer</span>
    await engine.dispose()

app = FastAPI(title="payments", version=__version__, lifespan=lifespan)
app.include_router(orders.router)

<span class="c"># uvicorn main:app                     — development</span>
<span class="c"># uvicorn main:app --workers 4         — production: uvicorn manages its own workers</span></pre>""",

"idioms": r"""<pre class="l3"><span class="c"># before — every flag from the diagram above, in one eight-line function</span>
def process(data):
    result = []
    for i in range(len(data)):
        if data[i] != None:
            if data[i]["status"] == "ok":
                result.append(data[i]["value"] * 2)
    return result</pre>

      <pre class="l1"><span class="c"># after — same behaviour; the name says what it returns and the types hold</span>
def doubled_ok_values(rows: Iterable[Row | None]) -&gt; list[int]:
    return [r.value * 2 for r in rows if r is not None and r.status == "ok"]

<span class="c"># what actually changed:</span>
<span class="c">#   range(len(x))  → iterate the thing        != None → is not None</span>
<span class="c">#   nested ifs     → one filter               dicts   → a typed record</span>
<span class="c">#   "process"      → a name that says the answer, not the verb</span></pre>""",

"checklist": r"""<pre class="l2"><span class="c"># the sixty seconds before you open the pull request</span>
uv run ruff format . &amp;&amp; uv run ruff check --fix .   <span class="c"># half the list, automatically</span>
uv run mypy .
uv run pytest -q -x --ff              <span class="c"># --ff: last run's failures first</span>
uv run pytest --cov --cov-report=term-missing | tail -20

<span class="c"># then read your own diff — these three greps catch what the tools do not:</span>
git diff --cached | grep -nE 'print\(|breakpoint\(|TODO|XXX'
git diff --cached | grep -nE 'except (Exception|BaseException):\s*$'
git diff --cached | grep -nE 'def \w+\([^)]*=\s*(\[\]|\{\}|set\(\))'</pre>""",

}
