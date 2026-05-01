// Use Blockly's built-in Zelos theme as base (hex colours, full colourTertiary).
// The scratch_classic renderer's setTheme override creates {style}_selected variants
// using colourTertiary — Zelos provides this for every style; Classic does not.
import * as ScratchBlocks from 'scratch-blocks';

export const doggoTheme = ScratchBlocks.Theme.defineTheme('doggo', {
  name: 'doggo',
  base: ScratchBlocks.Themes.Zelos,
  fontStyle: {
    family: 'Sono Variable, Sono, monospace',
    weight: '500',
    size: 15,
  },
});
