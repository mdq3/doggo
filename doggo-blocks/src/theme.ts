// Use Blockly's built-in Zelos theme (hex colours, full colourPrimary/Secondary/Tertiary).
// The scratch_classic renderer's setTheme override creates {name}_selected variants
// using colourTertiary — Zelos provides this for every style; Classic does not.
import * as ScratchBlocks from 'scratch-blocks';

export const doggoTheme = ScratchBlocks.Themes.Zelos;
