# -*- coding: utf-8 -*-
"""One worked code block for each Go topic that did not already have one."""

BLOCKS = {

"zero": r"""<pre class="l1">var (
	i  int            <span class="c">// 0</span>
	s  string         <span class="c">// "" — a string is never nil</span>
	p  *User          <span class="c">// nil</span>
	m  map[string]int <span class="c">// nil: reads work, writes panic</span>
	sl []int          <span class="c">// nil: len 0, and append still works</span>
	ch chan int       <span class="c">// nil: send and receive block forever</span>
	mu sync.Mutex     <span class="c">// ready to use — that is the whole point</span>
)

fmt.Println(m["missing"])   <span class="c">// 0, no panic — reads of a nil map are fine</span>
m["k"] = 1                  <span class="c">// panic: assignment to entry in nil map</span>
sl = append(sl, 1)          <span class="c">// fine: append allocates on first use</span>

<span class="c">// so this struct is usable with no constructor at all …</span>
type Counter struct {
	mu sync.Mutex
	n  int
}
var c Counter; c.mu.Lock()  <span class="c">// … which is why NewCounter() often earns nothing</span></pre>""",

"text": r"""<pre class="l2">s := "café"
len(s)                      <span class="c">// 5 — bytes, not characters</span>
utf8.RuneCountInString(s)   <span class="c">// 4 — characters</span>
s[3]                        <span class="c">// 195 — one byte, mid-rune, almost never useful</span>

for i, r := range s {       <span class="c">// range over a string yields runes …</span>
	fmt.Printf("%d %c\n", i, r)   <span class="c">// … and i is the BYTE offset: 0 1 2 3</span>
}

b := []byte(s)              <span class="c">// a copy</span>
r := []rune(s)              <span class="c">// a copy — 4 runes of 4 bytes each</span>

<span class="c">// the only right way to build a string in a loop; += is quadratic</span>
var sb strings.Builder
sb.Grow(len(parts) * 8)     <span class="c">// one allocation if you know the size</span>
for _, p := range parts {
	sb.WriteString(p)
}
return sb.String()          <span class="c">// no copy: Builder hands over its buffer</span></pre>""",

"structs": r"""<pre class="l1">type Audit struct {
	CreatedAt time.Time `json:"created_at"`
	CreatedBy string    `json:"created_by"`
}

type Order struct {
	Audit                            <span class="c">// embedded: o.CreatedAt works directly</span>
	ID     uuid.UUID `json:"id"`
	Secret string    `json:"-"`      <span class="c">// never marshalled</span>
	Note   string    `json:"note,omitempty"`
	Total  Money     `json:"total,string"`
}

var o Order
o.CreatedAt = time.Now()             <span class="c">// promoted field, not inheritance</span>

<span class="c">// embedding promotes methods too — and a method on Order SHADOWS the</span>
<span class="c">// embedded one rather than overriding it: Audit's own methods still call</span>
<span class="c">// Audit's version. There is no virtual dispatch here.</span>

<span class="c">// tags are just strings; the compiler does not check them. A typo in</span>
<span class="c">// `json:"crated_at"` is a silent wrong field name at run time.</span></pre>""",

"copies": r"""<pre class="l3">type Big struct{ Data [1024]int }        <span class="c">// an array, not a slice: 8 KB</span>

func byValue(b Big)    { b.Data[0] = 1 } <span class="c">// copies 8 KB, mutates nothing</span>
func byPointer(b *Big) { b.Data[0] = 1 } <span class="c">// copies 8 bytes, mutates the caller's</span>

<span class="c">// the range-copy trap — the single most common Go bug in review</span>
for _, o := range orders {
	o.Status = "sent"                    <span class="c">// o is a COPY; this is discarded</span>
}
for i := range orders {
	orders[i].Status = "sent"            <span class="c">// this one actually writes</span>
}

<span class="c">// method sets are the same rule wearing a different hat</span>
func (o Order) Cancel()  { o.Status = "cancelled" }   <span class="c">// silently useless</span>
func (o *Order) Cancel() { o.Status = "cancelled" }   <span class="c">// what you meant</span>

<span class="c">// and a struct containing a sync.Mutex must never be copied at all —</span>
<span class="c">// `go vet` will tell you: passes lock by value</span></pre>""",

"escape": r"""<pre class="l2"><span class="c">// go build -gcflags='-m' ./...   prints every decision the compiler made</span>

func stays() int {
	x := 42
	return x            <span class="c">// stack: freed by moving the stack pointer</span>
}

func escapes() *int {
	x := 42
	return &amp;x           <span class="c">// ./main.go:9:2: moved to heap: x</span>
}

func alsoEscapes(w io.Writer) {
	buf := make([]byte, 64)
	w.Write(buf)        <span class="c">// escapes: it is passed to an interface method,</span>
}                       <span class="c">// and the compiler cannot see the implementation</span>

<span class="c">// the useful fix is usually reuse, not avoidance:</span>
var bufs = sync.Pool{New: func() any { return new(bytes.Buffer) }}

b := bufs.Get().(*bytes.Buffer)
b.Reset()
defer bufs.Put(b)       <span class="c">// measure first — a pool can easily be slower</span></pre>""",

"context": r"""<pre class="l1"><span class="c">// ctx is the first parameter, always named ctx, never stored in a struct</span>
func (s *Service) Get(ctx context.Context, id string) (Order, error) {
	ctx, cancel := context.WithTimeout(ctx, 2*time.Second)
	defer cancel()          <span class="c">// always — skipping it leaks the timer until it fires</span>

	select {
	case &lt;-ctx.Done():
		return Order{}, ctx.Err()     <span class="c">// Canceled or DeadlineExceeded</span>
	case r := &lt;-s.results:
		return r, nil
	}
}

<span class="c">// values are for request-scoped data only, with an unexported key type</span>
type ctxKey struct{}                  <span class="c">// unexported: nobody else can collide</span>

ctx = context.WithValue(ctx, ctxKey{}, reqID)
id, _ := ctx.Value(ctxKey{}).(string) <span class="c">// always comma-ok; it can be missing</span>

<span class="c">// a deadline is inherited, never extended: a child can only be stricter</span></pre>""",

"sync-vs-chan": r"""<pre class="l2"><span class="c">// shared state that several goroutines read: a mutex is simply clearer</span>
type Cache struct {
	mu sync.RWMutex                <span class="c">// RW: many readers, occasional writer</span>
	m  map[string]Entry
}

func (c *Cache) Get(k string) (Entry, bool) {
	c.mu.RLock()
	defer c.mu.RUnlock()           <span class="c">// defer here costs ~1 ns and never leaks</span>
	e, ok := c.m[k]
	return e, ok
}

<span class="c">// a channel is right when OWNERSHIP moves, not when state is shared</span>
jobs := make(chan Job, 64)         <span class="c">// the buffer size IS the queue depth</span>
for range 8 {                      <span class="c">// 1.22+: range over an int</span>
	go func() {
		for j := range jobs {      <span class="c">// ends when the channel is closed</span>
			handle(j)
		}
	}()
}
close(jobs)                        <span class="c">// the SENDER closes; a receiver never does</span></pre>""",

"iface-layout": r"""<pre class="l3"><span class="c">// an interface value is two words: (type, value). Both must be nil to be nil.</span>
type MyErr struct{}

func (e *MyErr) Error() string { return "boom" }

func bad() error {
	var e *MyErr        <span class="c">// nil *MyErr</span>
	return e            <span class="c">// interface holds (*MyErr, nil) — NOT nil</span>
}

func good() error {
	return nil          <span class="c">// interface holds (nil, nil) — nil</span>
}

if bad() != nil  { <span class="c">/* fires — the classic typed-nil bug */</span> }
if good() != nil { <span class="c">/* does not fire */</span> }

<span class="c">// so a function that can fail returns a bare nil, never a typed nil pointer:</span>
func find(id string) (*Order, error) {
	o, err := lookup(id)
	if err != nil {
		return nil, err          <span class="c">// literal nil, not a nil *Order variable</span>
	}
	return o, nil
}</pre>""",

"generics-syntax": r"""<pre class="l1">func Map[T, U any](in []T, f func(T) U) []U {
	out := make([]U, 0, len(in))     <span class="c">// pre-sized: one allocation</span>
	for _, v := range in {
		out = append(out, f(v))
	}
	return out
}

<span class="c">// a constraint is an interface used as a type set. ~ means "underlying type",</span>
<span class="c">// so a `type Celsius float64` satisfies it too.</span>
type Number interface{ ~int | ~int64 | ~float64 }

func Sum[T Number](xs []T) T {
	var total T                      <span class="c">// the zero value of whatever T is</span>
	for _, x := range xs {
		total += x
	}
	return total
}

ids := Map(orders, func(o Order) uuid.UUID { return o.ID })  <span class="c">// T, U inferred</span>
n   := Sum([]float64{1.5, 2.5})                              <span class="c">// 4.0</span></pre>""",

"generics": r"""<pre class="l2"><span class="c">// good: one algorithm, many element types, no interface{} and no reflection</span>
func Keys[K comparable, V any](m map[K]V) []K

<span class="c">// bad: a type parameter where an ordinary interface says it better</span>
func Handle[T Handler](h T)      <span class="c">// just take the Handler interface</span>

<span class="c">// bad: generics to avoid writing two clear functions once</span>
func Get[T any](url string) (T, error)   <span class="c">// the caller must now annotate T</span>

<span class="c">// and most of what you were about to write already exists:</span>
slices.Sort(xs)
slices.Contains(xs, x)
slices.SortFunc(orders, func(a, b Order) int {
	return cmp.Compare(a.Total, b.Total)     <span class="c">// -1, 0, +1</span>
})
idx, found := slices.BinarySearch(sorted, target)
keys := slices.Collect(maps.Keys(m))         <span class="c">// 1.23+: an iterator, materialised</span></pre>""",

"time": r"""<pre class="l1"><span class="c">// measuring: monotonic, and immune to NTP steps and DST</span>
start := time.Now()
defer func() { metrics.Observe(time.Since(start)) }()

<span class="c">// wall-clock arithmetic: a different thing entirely</span>
t := time.Now().UTC()        <span class="c">// store and compare in UTC, always</span>
t.Add(24 * time.Hour)        <span class="c">// exactly 24h — NOT "tomorrow" across a DST change</span>
t.AddDate(0, 0, 1)           <span class="c">// calendar-aware "tomorrow"</span>

<span class="c">// durations are a type, so the units are checked at compile time</span>
timeout := 500 * time.Millisecond   <span class="c">// not the integer 500</span>

<span class="c">// a ticker holds a runtime timer until you stop it</span>
tk := time.NewTicker(time.Second)
defer tk.Stop()

<span class="c">// t1 == t2 compares the monotonic reading too; use Equal for wall clocks</span>
t1.Equal(t2)                 <span class="c">// and t.Round(0) strips the monotonic part</span></pre>""",

"modules": r"""<pre class="l2"><span class="c">// go.mod — the module path is also the import prefix</span>
module github.com/acme/payments

go 1.24                          <span class="c">// language version AND the toolchain floor</span>

require (
	github.com/jackc/pgx/v5 v5.6.0    <span class="c">// v2+ puts the major in the path</span>
	golang.org/x/sync v0.8.0
)

<span class="c">// minimal version selection: you get the HIGHEST version any dependency</span>
<span class="c">// asks for — not the newest published. Builds are reproducible by default.</span>

<span class="c">//  $ go mod tidy            add what is used, drop what is not, rewrite go.sum</span>
<span class="c">//  $ go get -u ./...        bump minors deliberately, in their own commit</span>
<span class="c">//  $ go mod why -m &lt;mod&gt;    who actually pulled this in</span>
<span class="c">//  $ go mod graph           the whole thing, when why is not enough</span>
<span class="c">//  GOFLAGS=-mod=readonly    in CI: fail rather than silently edit go.mod</span></pre>""",

"http-timeouts": r"""<pre class="l3">srv := &amp;http.Server{
	Addr:              ":8080",
	Handler:           mux,
	ReadHeaderTimeout: 5 * time.Second,   <span class="c">// header trickle — the Slowloris one</span>
	ReadTimeout:       15 * time.Second,  <span class="c">// headers + body</span>
	WriteTimeout:      30 * time.Second,  <span class="c">// end of headers → end of response</span>
	IdleTimeout:       60 * time.Second,  <span class="c">// keep-alive between requests</span>
	MaxHeaderBytes:    1 &lt;&lt; 20,
}

<span class="c">// one route legitimately needs longer than the rest:</span>
mux.Handle("/report", http.TimeoutHandler(reportHandler, 60*time.Second, "timed out"))

<span class="c">// none of the above reaches your database call. Only this does:</span>
func handler(w http.ResponseWriter, r *http.Request) {
	ctx, cancel := context.WithTimeout(r.Context(), 3*time.Second)
	defer cancel()
	rows, err := db.QueryContext(ctx, q)   <span class="c">// cancelled when the client hangs up</span>
	<span class="c">// …</span>
}</pre>""",

"testing": r"""<pre class="l1">func BenchmarkParse(b *testing.B) {
	data := load()
	b.ReportAllocs()
	b.ResetTimer()               <span class="c">// exclude the setup above from the timing</span>
	for b.Loop() {               <span class="c">// 1.24+: replaces for i := 0; i &lt; b.N; i++</span>
		_, _ = Parse(data)
	}
}

func FuzzParse(f *testing.F) {
	f.Add([]byte(`{"id":1}`))              <span class="c">// a seed corpus entry</span>
	f.Fuzz(func(t *testing.T, in []byte) {
		_, _ = Parse(in)                   <span class="c">// the property: it must never panic</span>
	})
}

<span class="c">//  $ go test -race -cover ./...              the two flags CI must always pass</span>
<span class="c">//  $ go test -run TestPlace/empty_basket     one subtest, by name</span>
<span class="c">//  $ go test -bench=. -benchmem -count=10 | benchstat -</span>
<span class="c">//  $ go test -fuzz=FuzzParse -fuzztime=60s   findings land in testdata/</span></pre>""",

"pprof": r"""<pre class="l2"><span class="c">// register the handlers on a private listener — never on your public mux</span>
import _ "net/http/pprof"

go func() {
	_ = http.ListenAndServe("localhost:6060", nil)   <span class="c">// localhost only</span>
}()

<span class="c">//  heap, live objects — for a leak:</span>
<span class="c">//  $ go tool pprof -http=:8080 localhost:6060/debug/pprof/heap</span>
<span class="c">//</span>
<span class="c">//  CPU, 30 seconds under load — for a hot path:</span>
<span class="c">//  $ go tool pprof localhost:6060/debug/pprof/profile?seconds=30</span>
<span class="c">//</span>
<span class="c">//  goroutines — the count climbing is a leaked body or an unclosed channel:</span>
<span class="c">//  $ curl -s 'localhost:6060/debug/pprof/goroutine?debug=1' | head -40</span>
<span class="c">//</span>
<span class="c">//  and the only honest way to claim an improvement:</span>
<span class="c">//  $ go tool pprof -base before.pb.gz after.pb.gz</span></pre>""",

"checklist": r"""<pre class="l1"><span class="c"># the sixty seconds before you open the pull request</span>
gofmt -l .                 <span class="c"># anything printed is unformatted</span>
go vet ./...               <span class="c"># the compiler's own lint: printf args, lock copies</span>
go test -race -count=1 ./...   <span class="c"># -count=1 defeats the test result cache</span>
staticcheck ./...          <span class="c"># the one third-party linter worth the dependency</span>
govulncheck ./...          <span class="c"># CVEs in the module graph, filtered by call graph</span>

<span class="c"># then read your own diff — these catch what the tools do not:</span>
git diff --cached | grep -nE 'context\.(TODO|Background)\(\)'
git diff --cached | grep -nE '_ = err|err != nil \{\s*\}'
git diff --cached | grep -nE 'go func' <span class="c">   # who waits for it, and what cancels it?</span></pre>""",

}
