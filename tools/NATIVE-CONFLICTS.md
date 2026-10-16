# Native shortcut audit

Command+L is passed through to the focused app. Command+Option+L restores
Dwindle split tiling, but conflicts with Finder's Downloads shortcut.
Scrolling Niri is no longer reachable through the layout shortcut.

Run `lua tools/audit-native-conflicts.lua` to compare every bridge descriptor
against the reviewed macOS/Finder/Chrome catalog. The saved result is
`native-shortcut-conflicts.tsv`. This inspects 247 bridge descriptors
(246 upstream audited chords plus the emergency passthrough toggle).

Nine ordinary app shortcuts were subsequently restored by user choice:
Command+F/S/Q/P/G/comma and Command+Shift+T/W/N. Workspace moves, wallpaper,
Calculator, emoji and locking retain their desktop mappings. Command+Shift+G
remains the messaging launcher; only unshifted Find Next was changed.

The original catalog found 59 intercepted native conflicts, including deliberate
desktop overrides. It does not enumerate every installed application's
custom menu shortcuts, browser extensions, editor keymaps, or other utilities.
A missing catalog match does not mean a chord is conflict-free.

Priority decisions:

| Keys | Native action displaced | Current bridge action |
| --- | --- | --- |
| Command+F/S/Q/P | Find/save/quit/print | Fullscreen/scratchpad/close window/center window |
| Command+G, Shift+G | Find next/previous | Group window / messaging app |
| Command+comma | App settings | Notification settings |
| Command+I/J | Info/downloads or app-specific | Input source / split layout |
| Command+Shift+T/W/N | Reopen tab/close window/private window | Todoist/TextEdit/editor |
| Command+Shift+3/4/5 | Screenshots | Move window to workspace |
| Command+Control+Space/Q | Emoji/lock screen | Wallpaper/calculator |
| Command+Tab, grave | App/window switching | Workspace/scratchpad |
| Command+1..9, 0 | Browser tabs/zoom reset | Workspaces |
| Command+arrows, Shift+arrows | Text movement/selection | Focus/move tiles |
| Command+O/K | Open file/app action | Floating/shortcut help (explicit user choices) |

Physical resize keys also displace zoom on a QWERTY layout; with Dvorak the
character positions differ. Command-drag and right-Option dictation can have
mouse/typing tradeoffs not captured by a keyboard-menu catalog.

The table above records the original conflicts, not the current state.
Consult the regenerated TSV for current dispositions. Do not automatically
remove the remaining desktop overrides: the user explicitly retained them.

Sources:

- https://support.apple.com/en-us/102650
- https://support.google.com/chrome/answer/157179?hl=en-DM
