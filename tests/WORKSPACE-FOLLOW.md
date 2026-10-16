# Move and follow

Command+Shift+number resolves the focused window's stable OmniWM ID, moves
that window, then navigates to that same window. It does not rely on a
workspace-only switch after the source workspace has reassigned focus.
Command+Option+Shift+number remains move without following.

Live validation on OmniWM 0.7.6: a synthesized Command+Shift+0 moved the
focused window to workspace 10. IPC confirmed workspace 10 was current and
that exact window remained focused. The test window was returned afterwards.
The previous implementation reproduced the reported failure: the window
reached workspace 10 while workspace 1 stayed current.

Keyboard workspace-slide animations remain unsupported by the installed
OmniWM version. Its workspace-selection path passes startScrollAnimation:
false. General tiling animations do not provide workspace-slide animations.
