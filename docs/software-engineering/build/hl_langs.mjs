// Language definitions this series needs that TanStack Highlight does not ship.
//
// The bundled set is web-oriented (25 languages: ts/tsx/css/html/json/yaml/sql/
// shell/python/...). It has no Go and no Java, which between them cover 119 of
// the series' 244 code blocks, plus go.mod and Terraform for one block each.
//
// A LanguageDefinition is just { name, aliases, tokenize(code) -> TokenRange[] },
// so these are ordinary pattern lists. `collect` below reimplements the
// package's own first-match-wins range merging, because the helper it uses for
// the bundled languages lives under internal/ and is not a public export.

import { defineLanguage } from '@tanstack/highlight/core';

function collect(code, patterns) {
  const ranges = [];
  const occupied = new Uint8Array(code.length);
  for (const p of patterns) {
    if (p.collect) {
      for (const r of p.collect(code)) {
        let clash = false;
        for (let i = r.start; i < r.end && !clash; i++) if (occupied[i]) clash = true;
        if (clash || r.start >= r.end) continue;
        ranges.push(r);
        occupied.fill(1, r.start, r.end);
      }
      continue;
    }
    const re = new RegExp(p.regex.source, p.regex.flags.includes('g') ? p.regex.flags : p.regex.flags + 'g');
    let m;
    while ((m = re.exec(code))) {
      const value = p.group ? m[p.group] : m[0];
      if (!value) { if (!m[0].length) re.lastIndex++; continue; }
      const start = m.index + (p.group ? m[0].indexOf(value) : 0);
      const end = start + value.length;
      let clash = false;
      for (let i = start; i < end && !clash; i++) if (occupied[i]) clash = true;
      if (clash) continue;
      ranges.push({ start, end, className: typeof p.className === 'function' ? p.className(m) : p.className });
      occupied.fill(1, start, end);
    }
  }
  return ranges;
}

// Comments and strings are matched by one alternation so that a `//` inside a
// string literal does not open a comment, and a quote inside a comment does not
// open a string.
const commentOrString = m => (m[0].startsWith('//') || m[0].startsWith('/*') || m[0].startsWith('#') || m[0].startsWith('--') ? 'comment' : 'string');

export const go = defineLanguage({
  name: 'go',
  aliases: ['golang'],
  tokenize(code) {
    return collect(code, [
      { className: commentOrString,
        regex: /\/\/[^\n]*|\/\*[\s\S]*?\*\/|`[^`]*`|"(?:\\.|[^"\\\n])*"|'(?:\\.|[^'\\\n])*'/g },
      { className: 'keyword',
        regex: /\b(?:break|case|chan|const|continue|default|defer|else|fallthrough|for|func|go|goto|if|import|interface|map|package|range|return|select|struct|switch|type|var)\b/g },
      { className: 'literal', regex: /\b(?:true|false|nil|iota)\b/g },
      { className: 'type', regex: /\btype\s+([A-Za-z_]\w*)/g, group: 1 },
      { className: 'function', regex: /\bfunc\s+(?:\([^)]*\)\s*)?([A-Za-z_]\w*)/g, group: 1 },
      { className: 'type',
        regex: /\b(?:any|bool|byte|complex64|complex128|error|float32|float64|int|int8|int16|int32|int64|rune|string|uint|uint8|uint16|uint32|uint64|uintptr)\b/g },
      { className: 'function', regex: /\b([A-Za-z_]\w*)\s*\(/g, group: 1 },
      { className: 'number',
        regex: /\b(?:0[xX][\da-fA-F_]+|0[bB][01_]+|0[oO][0-7_]+|\d[\d_]*(?:\.\d[\d_]*)?(?:[eE][+-]?\d+)?i?)\b/g },
    ]);
  },
});

export const java = defineLanguage({
  name: 'java',
  tokenize(code) {
    return collect(code, [
      { className: commentOrString,
        regex: /\/\/[^\n]*|\/\*[\s\S]*?\*\/|"""[\s\S]*?"""|"(?:\\.|[^"\\\n])*"|'(?:\\.|[^'\\\n])*'/g },
      { className: 'function', regex: /@[A-Za-z_]\w*/g },
      { className: 'keyword',
        regex: /\b(?:abstract|assert|break|case|catch|class|const|continue|default|do|else|enum|extends|final|finally|for|goto|if|implements|import|instanceof|interface|native|new|package|permits|private|protected|public|record|return|sealed|static|strictfp|super|switch|synchronized|this|throw|throws|transient|try|var|volatile|while|yield)\b/g },
      { className: 'literal', regex: /\b(?:true|false|null)\b/g },
      { className: 'type', regex: /\b(?:class|interface|record|enum)\s+([A-Za-z_]\w*)/g, group: 1 },
      { className: 'type',
        regex: /\b(?:boolean|byte|char|double|float|int|long|short|void)\b/g },
      { className: 'function', regex: /\b([A-Za-z_]\w*)\s*\(/g, group: 1 },
      { className: 'type', regex: /\b[A-Z][A-Za-z0-9_]*\b/g },
      { className: 'number',
        regex: /\b(?:0[xX][\da-fA-F_]+|0[bB][01_]+|\d[\d_]*(?:\.\d[\d_]*)?(?:[eE][+-]?\d+)?[dDfFlL]?)\b/g },
    ]);
  },
});

export const gomod = defineLanguage({
  name: 'gomod',
  tokenize(code) {
    return collect(code, [
      { className: 'comment', regex: /\/\/[^\n]*/g },
      { className: 'keyword', regex: /^\s*(?:module|go|require|replace|exclude|retract|toolchain)\b/gm },
      { className: 'string', regex: /"(?:\\.|[^"\\\n])*"/g },
      { className: 'number', regex: /\bv?\d+(?:\.\d+)+(?:[-+][\w.]+)?\b/g },
    ]);
  },
});

export const hcl = defineLanguage({
  name: 'hcl',
  aliases: ['terraform', 'tf'],
  tokenize(code) {
    return collect(code, [
      { className: commentOrString,
        regex: /#[^\n]*|\/\/[^\n]*|\/\*[\s\S]*?\*\/|"(?:\\.|[^"\\\n])*"/g },
      { className: 'keyword',
        regex: /^\s*(?:resource|provider|variable|module|output|data|terraform|locals|for_each|count|depends_on|dynamic|lifecycle)\b/gm },
      { className: 'literal', regex: /\b(?:true|false|null)\b/g },
      { className: 'property', regex: /^\s*([\w-]+)\s*=/gm, group: 1 },
      { className: 'function', regex: /\b([a-z_]\w*)\s*\(/g, group: 1 },
      { className: 'number', regex: /\b\d+(?:\.\d+)?\b/g },
    ]);
  },
});

// The bundled `shell` language lexes shell *scripts*: it scans left to right and
// lets a quote open a string that runs until the next quote, anywhere later in
// the block. These pages show console *transcripts* -- a command, then prose
// output -- where an apostrophe in "the compiler's own lint" or a bare `"` in a
// test failure swallowed every following comment. This tokenizer is built for
// transcripts instead: comments win first, and a string can never cross a line,
// so a stray quote costs at most the rest of its own line.
export const consoleLang = defineLanguage({
  name: 'console',
  aliases: ['shell', 'bash', 'sh', 'zsh', 'session'],
  tokenize(code) {
    // In a transcript, only the "$ " lines are commands. In a plain command
    // list (no prompts at all), every line starts with one.
    const prompted = /^\s*\$\s+\S/m.test(code);
    return collect(code, [
      ...(prompted ? [{ collect: outputLines }] : []),
      { className: 'comment', regex: /(?:^|[ \t])(#[^\n]*)/gm, group: 1 },
      { className: 'meta', regex: /^\s*\$(?=\s)/gm },
      prompted
        ? { className: 'command', regex: /^\s*\$\s+((?:[A-Z_][A-Z0-9_]*=\S*\s+)*[\w./-]+)/gm, group: 1 }
        : { className: 'command', regex: /^([a-z][\w./-]*)(?=\s|$)/gm, group: 1 },
      { className: 'string', regex: /"(?:\\.|[^"\\\n])*"|'[^'\n]*'/g },
      { className: 'variable', regex: /\$\{[^}\n]*\}|\$[A-Za-z_]\w*/g },
      { className: 'keyword', regex: /\b(?:case|do|done|elif|else|esac|export|fi|for|function|if|in|then|until|while)\b/g },
      { className: 'attr', regex: /(?:^|\s)(--?[A-Za-z][\w-]*)/g, group: 1 },
    ]);
  },
});

// In a transcript, every line that is not typed at a prompt is output from the
// machine. The pages have always dimmed those lines, so the reader can see at a
// glance what they type and what comes back; this reproduces that, and claims
// the whole line so a bare quote or "#" in the output cannot start a token.
function outputLines(code) {
  const out = [];
  let at = 0, typed = false;
  for (const line of code.split('\n')) {
    const isPrompt = /^\s*\$(?=\s|$)/.test(line);
    // A backslash at the end of a typed line continues it onto the next.
    typed = isPrompt || (typed && /\\\s*$/.test(out.lastTyped || ''));
    out.lastTyped = typed ? line : '';
    if (!typed && line.trim()) out.push({ start: at, end: at + line.length, className: 'meta' });
    at += line.length + 1;
  }
  return out;
}

// These pages routinely append a short coda in another language to a snippet --
// a YAML setting after a Java class, a JPA mapping after a SQL migration -- and
// mark it with a "#" or "//" prose comment the host language does not know. The
// wrapper adds those comments to any language, after its own tokenizer has run,
// so anything already inside a string or comment is left alone.
const CODA = [
  /^[ \t]*(?:#|\/\/)[^\n]*$/gm,     // a whole line of prose
  /(?<=[ \t])(?:#|\/\/)[^\n]*$/gm,  // a comment trailing a line of code
];

export function withCodas(def) {
  return defineLanguage({
    name: def.name,
    aliases: def.aliases,
    tokenize(code, context) {
      const host = [...def.tokenize(code, context)];
      // A "#" or "//" inside a string or a real comment is not a coda, so those
      // regions are off limits. Everything else the host tokenizer produced is
      // fair game: prose reads as identifiers to it ("Spring Boot" comes back as
      // two types), and the coda comment has to win over that.
      // Strings are off limits -- a "#" inside one is data, not a comment. So is
      // console output, which is dimmed as a whole line already. A comment may be
      // absorbed only if the coda contains it outright (the SQL tokenizer reads
      // "-- collections are LAZY" inside a "// ..." coda as SQL comment); a coda
      // that would split a longer comment, such as a /* */ block, is dropped.
      const locked = new Uint8Array(code.length);
      const comments = [];
      for (const r of host) {
        if (r.className === 'string' || r.className === 'meta') locked.fill(1, r.start, r.end);
        else if (r.className === 'comment') comments.push(r);
      }
      const codas = [];
      const taken = new Uint8Array(code.length);
      for (const src of CODA) {
        const re = new RegExp(src.source, src.flags);
        let m;
        while ((m = re.exec(code))) {
          const start = m.index + m[0].length - m[0].trimStart().length;
          const end = m.index + m[0].length;
          let blocked = start >= end;
          for (let i = start; i < end && !blocked; i++) if (locked[i] || taken[i]) blocked = true;
          if (!blocked) {
            for (const c of comments) {
              const overlaps = c.start < end && c.end > start;
              if (overlaps && !(c.start >= start && c.end <= end)) { blocked = true; break; }
            }
          }
          if (blocked) continue;
          codas.push({ start, end, className: 'comment' });
          taken.fill(1, start, end);
        }
      }
      if (!codas.length) return host;
      const kept = host.filter(r => {
        for (let i = r.start; i < r.end; i++) if (taken[i]) return false;
        return true;
      });
      return [...kept, ...codas].sort((a, b) => a.start - b.start);
    },
  });
}
