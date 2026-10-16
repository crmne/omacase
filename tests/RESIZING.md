# Resize acceptance checks

Command is Omarchy's Super. Use the physical minus and equals positions
(the two keys immediately right of 0), independent of the active layout.
Dvorak is covered by the registration regression test.

| Keys | Action |
| --- | --- |
| Command + minus / equals | Shrink / grow width |
| Command + Shift + minus / equals | Shrink / grow height |
| Add Option | Fine increment |
| Add Control | Coarse increment |
| Hold a resize chord | Repeat |
| Command + right-button drag | Mouse resize through OmniWM |

Floating windows and Niri request 25/100/300-point fine/normal/coarse changes.
Dwindle IPC only exposes proportional increments, so it uses 1/2/6 steps.
Application minimum sizes and display bounds can constrain the result.

Test with two tiled windows sharing the axis being resized. A single window
filling a workspace has no split to resize. Switch a disposable test window
to floating with Command+O, test both dimensions and all three increments,
then return it to tiling. Confirm holding the key repeats, and that native
Command+T and Command+W still work.

The Lua tests verify dispatch and floating geometry with mocks. Physical
keyboard behavior and application minimum sizes still require live checking.

On the reference Dvorak Mac, synthesized Command+physical-minus reduced a
tiled Ghostty window from 1350 to 1050 points. Command+physical-equals restored
it to 1349 points (one-point layout rounding). This verifies live hotkey
dispatch, not every physical keyboard or every resize variant.
