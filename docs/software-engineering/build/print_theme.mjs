// The palette a printed page gets.
//
// A printer has no dark mode, and Chrome prints with "Background graphics" off
// by default -- so a reader printing from a dark-themed browser would otherwise
// get pale text on unprinted white. Print therefore forces one palette: the
// light one, with the quiet greys pushed darker, because ink on paper reads
// lighter than the same value backlit on a screen.

import { lightTheme } from './hl_theme.mjs';

// Series design tokens, print values. Every surface flattens to paper white and
// the structure is carried by borders, which print whether or not the reader
// enables background graphics.
export const seriesTokens = {
  ground: '#FFFFFF', surface: '#FFFFFF', 'surface-2': '#FFFFFF',
  line: '#AEBDC6',                                    // #CFDAE1 is invisible in ink
  ink: '#0B141B', 'ink-soft': '#33424C', 'ink-faint': '#596A74',
  l1: '#0A6E79', l2: '#3E4E9E', l3: '#98420F',        // one shade down from screen
  'l1-wash': 'transparent', 'l2-wash': 'transparent', 'l3-wash': 'transparent',
  accent: '#0A6E79',
  shadow: 'none',
};

// Syntax tokens: the light theme as-is, with three changes.
//
// comment and meta sit at the 3.5:1 comment threshold on screen and want more
// weight on paper.
//
// type moves from #6F42AF to a violet a shade to its left. Chrome's print
// backend rewrites certain colours on the way to the page -- #6F42AF lands as
// #39225B, half its brightness, which kills the distinction from plain text
// that the violet exists to make. #6A3FA8 is visually the same colour and
// survives the trip. That was measured by rendering the palette through
// Chrome's own print backend; the tool that did it is gone with the rest of
// the PDF checks, so treat these two values as findings, not as guesses.
export const printTheme = {
  name: 'ladder-print', type: 'print', background: '#FFFFFF', foreground: seriesTokens.ink,
  tokens: {
    ...lightTheme.tokens,
    comment: seriesTokens['ink-faint'],
    meta: seriesTokens['ink-faint'],
    type: '#6A3FA8',
  },
};
