// Highlight themes built from the series' own palette rather than an imported
// editor theme. Keyword stays on the teal accent and comment on --ink-faint, so
// the blocks read the same as they did under the old hand-rolled .c/.k scheme;
// the rest are tuned to sit at the same saturation as --l1/--l2/--l3.

export const lightTheme = {
  name: 'ladder-light', type: 'light',
  background: '#FFFFFF', foreground: '#101A22',
  tokens: {
    token: '#101A22',
    comment: '#6E808B',   // --ink-faint, matching the previous .c colour
    keyword: '#0A6E79',   // --l1 teal, a shade darker for contrast on white
    string:  '#A2461A',   // --l3 rust
    function:'#42539F',   // --l2 indigo
    type:    '#6F42AF',   // violet, adjacent to indigo but distinguishable
    number:  '#1B6B47',   // green
    literal: '#1B6B47',
    property:'#42539F',
    attr:    '#42539F',
    tag:     '#1B6B47',
    selector:'#1B6B47',
    operator:'#42545F',   // --ink-soft
    variable:'#101A22',
    meta:    '#6E808B',
    heading: '#0A6E79',
    link:    '#0A6E79',
    command: '#42539F',
    'code-inline': '#A2461A',
    inserted:'#1B6B47',
    deleted: '#A8281F',
  },
};

export const darkTheme = {
  name: 'ladder-dark', type: 'dark',
  background: '#111C24', foreground: '#E2EAEF',
  tokens: {
    token: '#E2EAEF',
    comment: '#8598A3',
    keyword: '#3EC0CC',   // --l1 dark
    string:  '#E7935B',   // --l3 dark
    function:'#8E9BEC',   // --l2 dark
    type:    '#C9A9F5',
    number:  '#5FD3A0',
    literal: '#5FD3A0',
    property:'#8E9BEC',
    attr:    '#8E9BEC',
    tag:     '#5FD3A0',
    selector:'#5FD3A0',
    operator:'#9FB0BA',
    variable:'#E2EAEF',
    meta:    '#8598A3',
    heading: '#3EC0CC',
    link:    '#3EC0CC',
    command: '#8E9BEC',
    'code-inline': '#E7935B',
    inserted:'#5FD3A0',
    deleted: '#FF8F85',
  },
};
