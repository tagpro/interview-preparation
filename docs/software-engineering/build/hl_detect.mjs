// Language detection for the series' <pre> blocks.
//
// The blocks carry no language marker -- only class="l1|l2|l3" and, on the AWS
// page, data-lang="go|py|java". Everything else is inferred from content. Shared by
// hl_inject.mjs and hl_report.mjs so detection has exactly one implementation.

import { createHash } from 'node:crypto';

export const PAGES = [
  'backend-go-ladder.html', 'pillar-a-foundations.html', 'pillar-b-go.html',
  'pillar-c-cloud.html', 'python-foundations.html', 'java-spring.html',
  'aws-deep-dive.html', 'dsa.html',
];

const ENT = { '&lt;': '<', '&gt;': '>', '&amp;': '&', '&quot;': '"', '&#39;': "'",
              '&rsquo;': '’', '&mdash;': '—', '&nbsp;': ' ' };
export function unent(s) {
  return s.replace(/&(?:lt|gt|amp|quot|#39|rsquo|mdash|nbsp);/g, m => ENT[m]);
}
export function strip(body) { return unent(body.replace(/<[^>]+>/g, '')); }
export function fingerprint(text) {
  return createHash('sha1').update(text).digest('hex').slice(0, 12);
}

// Blocks whose language cannot be inferred honestly -- keyed by a fingerprint of
// the code text so the override survives a rebuild but lapses if the code changes.
export const OVERRIDES = {
  // python-foundations: five lines of GitHub Actions YAML followed by three
  // Dockerfile lines. Genuinely mixed; YAML is the larger half.
  '6cf82d967d2f': 'yaml',
};

// These pages nearly always name the file in the opening comment
// ("// config.go", "# aws.py", "-- V1__create_tasks.sql"). That beats any
// syntax heuristic, so it runs early.
const BY_EXT = {
  go: 'go', py: 'python', java: 'java', sql: 'sql', yml: 'yaml', yaml: 'yaml',
  json: 'json', toml: 'toml', xml: 'html', html: 'html', sh: 'shell',
  ts: 'ts', js: 'js', tf: 'hcl', mod: 'gomod', env: 'env',
  properties: 'env', txt: 'plaintext', md: 'markdown',
};

// Each page is overwhelmingly one language; used only as a last resort.
export const PAGE_DEFAULT = {
  'pillar-b-go.html': 'go', 'backend-go-ladder.html': 'go',
  'python-foundations.html': 'python', 'java-spring.html': 'java',
};

export function detect(body, attrs, page) {
  const t = strip(body);
  const over = OVERRIDES[fingerprint(t)];
  if (over) return over;

  const lines = t.split('\n').filter(l => l.trim());
  const n = lines.length || 1;
  const has = re => re.test(t);
  const count = re => (t.match(re) || []).length;

  // --- console sessions -------------------------------------------------
  const first = (lines[0] || '').trim();
  const prompts = lines.filter(l => /^\s*\$\s+\S/.test(l)).length;
  if (/^\$\s+\S/.test(first) || prompts / n > 0.2) return 'shell';

  // Command lists with no "$" prompt (the "sixty seconds before you open the
  // pull request" blocks, the JVM-flag block). Backslash continuations are
  // folded first so a multi-line invocation counts as one command, not as one
  // command plus four non-command lines.
  const logical = [];
  for (const l of lines) {
    if (logical.length && /\\\s*$/.test(logical[logical.length - 1])) logical[logical.length - 1] += ' ' + l.trim();
    else logical.push(l);
  }
  const CMD = /^\s*(?:\.\/)?(?:javac|jshell|jwebserver|java|jar|mvnw|mvn|gradle|sdk|gofmt|gofumpt|golangci-lint|govulncheck|staticcheck|go|python3?|pip3?|poetry|pytest|mypy|ruff|uv|npx|npm|node|docker|kubectl|helm|aws|terraform|curl|wget|git|grep|sed|awk|make|psql|export|brew|apt-get|apt)\s+[-\w./]/;
  const cmds = logical.filter(l => CMD.test(l)).length;
  const bodyLines = logical.filter(l => !/^\s*#/.test(l)).length || 1;
  if (cmds >= 2 && cmds / bodyLines > 0.4) return 'shell';

  // --- filename in the opening comment ----------------------------------
  const fn = /^\s*(?:\/\/|#|--)\s*(?:[\w./-]*\/)?([\w.-]+\.(\w+))\b/.exec(t) ||
             /^\s*(?:\/\/|#)\s*(Dockerfile)\b/i.exec(t);
  if (fn) {
    const ext = (fn[2] || 'dockerfile').toLowerCase();
    if (BY_EXT[ext]) return BY_EXT[ext];
  }

  // --- language signals -------------------------------------------------
  const goish = has(/(?:^|\n)\s*package\s+\w+\s*$/) ||
    has(/\bfunc\s*(?:\([^)]*\)\s*)?\w*\s*\(/) || has(/:=/) ||
    has(/^\s*type\s+\w+\s+(?:struct|interface)\b/m) || has(/^\s*var\s*\($/m) ||
    has(/\bgo\s+func\b/) || has(/\berr\s*!=\s*nil\b/) || has(/\bchan\s+\w/);
  const javaish =
    has(/@(?:Override|Service|Component|RestController|Bean|Autowired|SpringBootApplication|Entity|Transactional|Repository|Configuration|Test|GetMapping|PostMapping|Query|EntityGraph)\b/) ||
    has(/^\s*(?:public|private|protected)\s+(?:static\s+|final\s+|abstract\s+)*(?:class|interface|record|enum|void|[A-Z<])/m) ||
    has(/\bSystem\.out\.print/) || has(/\bnew\s+[A-Z]\w*\s*(?:<[^>]*>)?\s*\(/) ||
    has(/\b(?:List|Map|Optional|Stream|ArrayList|HashMap)\s*<[^>]*>\s+\w/) ||
    has(/\bThread\.ofVirtual\b/) ||
    has(/^\s*(?:int|long|double|boolean|char|float|byte|short|var|final)\s+\w+\s*=.*;\s*(?:\/\/.*)?$/m);
  const pyish = has(/^\s*(?:async\s+)?def\s+\w+.*:\s*(?:#.*)?$/m) ||
    has(/^\s*class\s+\w+.*:\s*(?:#.*)?$/m) ||
    has(/^\s*(?:from\s+[\w.]+\s+)?import\s+\w/m) || has(/\bself\b/) || has(/\bf["']/) ||
    has(/^\s*@(?:app|router|pytest|property|dataclass|staticmethod|classmethod)/m) ||
    has(/^\s*(?:with|for)\s+[\w., ]+\s+(?:in|as)\s+.*:\s*(?:#.*)?$/m) ||
    has(/\b(?:True|False|None)\b/) || has(/\b(?:print|len|sorted|enumerate|zip|range)\(/) ||
    has(/\.(?:append|join|items|keys|values|get)\(/) ||
    has(/^\s*(?:try|except|finally|elif|else):/m);

  // The AWS and algorithms pages state the pane language on the element.
  // Trust it -- unless the body plainly disagrees and plainly agrees with a
  // different one, which catches a snippet filed under the wrong pane.
  const dl = /data-lang="(go|py|java)"/.exec(attrs || '');
  if (dl) {
    const want = { go: 'go', py: 'python', java: 'java' }[dl[1]];
    const looks = { go: goish, python: pyish, java: javaish };
    if (looks[want]) return want;
    for (const alt of ['go', 'python', 'java']) if (looks[alt]) return alt;
    return want;
  }

  // --- structured formats -----------------------------------------------
  // Gated on "not obviously Go or Java" so Go's `select {` and Spring's JPQL
  // @Query strings are not mistaken for SQL.
  if (!goish && !javaish) {
    if (has(/^\s*(?:SELECT|INSERT\s+INTO|UPDATE\s+\w|CREATE\s+(?:TABLE|INDEX|UNIQUE)|ALTER\s+TABLE|EXPLAIN|BEGIN;|COMMIT;|WITH\s+\w+\s+AS)\b/mi) &&
        has(/\b(?:FROM|INTO|TABLE|SET|VALUES)\b/i)) return 'sql';
    if (has(/^FROM\s+[\w./:-]+/m) && has(/^(?:RUN|COPY|WORKDIR|ENTRYPOINT|CMD|EXPOSE|ENV|USER)\s+\S/m)) return 'dockerfile';
    if (has(/^\s*<\?xml/m) || has(/^\s*<!--.*\bpom\.xml/m) ||
        has(/^\s*<(?:dependency|dependencies|project|configuration|beans|plugin)\b/m)) return 'html';
    if (has(/^\s*(?:GET|POST|PUT|PATCH|DELETE|HEAD)\s+\/\S*\s*(?:HTTP\/|$)/m) ||
        has(/^HTTP\/1\.[01]\s+\d{3}/m)) return 'http';
    if (/^[[{]/.test(t.trim()) && count(/"[\w$-]+"\s*:/g) >= 2) return 'json';
    if (has(/^\s*\[(?:tool|build-system|project)[\w.-]*\]\s*$/m)) return 'toml';
    if (has(/^\s*(?:resource|provider|variable|module|output|data|terraform)\s+"/m)) return 'hcl';
    if (has(/^\s*module\s+[\w./-]+\s*$/m) && has(/^\s*go\s+1\.\d+/m)) return 'gomod';
  }

  if (goish && !javaish) return 'go';
  if (javaish && !goish) return 'java';
  if (pyish && !goish && !javaish) return 'python';
  if (goish) return 'go';
  if (javaish) return 'java';
  if (pyish) return 'python';

  if (has(/^\s*(?:apiVersion|kind|metadata|spec|services|version|resources|jobs|steps):\s*/m) ||
      has(/^\s*-\s+(?:run|uses|name):\s+/m)) return 'yaml';
  if (count(/^\s*[\w.-]+:\s*(?:$|[^\s:].*)$/gm) / n > 0.5 && !has(/[;{}]/)) return 'yaml';
  if (count(/^\s*(?:export\s+)?[A-Z][A-Z0-9_]*=/gm) / n > 0.5) return 'env';

  if (dl) return dl[1] === 'go' ? 'go' : 'python';
  if (page && PAGE_DEFAULT[page]) return PAGE_DEFAULT[page];
  return 'plaintext';
}
