# Set Dresser

A Maya tool that dresses a set: it scatters rocks and trees across a 40 x 40 ground plane and keeps them off a path (4 wide, along Z through the middle, with a 1-unit margin) and out of a round pond (radius 6 at x=10, z=10).

A window with sliders for rock count, tree count, area and seed, a checkbox for keeping the path and pond clear, and Scatter / Clear buttons. The same seed with the same settings makes the same set every time. One Scatter is one undo, and Clear removes only the `rocks` and `trees` groups.

**Maya version:** Maya 2025 (Windows). Python 3, `maya.cmds` only, no pymel.

## Run it

Copy `set_dresser.py` and `set_dresser_ui.py` into your Maya scripts folder (find it with `print(cmds.internalVar(userScriptDir=True))`), then run these two lines in the Script Editor's Python tab:

```python
import set_dresser_ui
set_dresser_ui.show()
```

## Files

- `set_dresser.py` — the engine: settings at the top, `make_rock`, `make_tree`, `is_clear`, `scatter`, `build_ground`, `clear`. No UI.
- `set_dresser_ui.py` — the window. Reads the controls and calls the engine.
- `send_to_maya.py` — sends Python to Maya's command port (7001) from a terminal.
- `CLAUDE.md` — the rules the agent followed when building this.
