"""set_dresser.py — the engine. No windows in here.

Scatters rocks and trees on a 40 x 40 ground, keeping them off a path
(along Z through the middle) and out of a round pond.

    import set_dresser
    set_dresser.build_ground()
    set_dresser.scatter(rocks=30, trees=12, seed=12)
"""

# Borrow other people's toolboxes: math and random for numbers, maya.cmds to control Maya.
import math
import random

import maya.cmds as cmds

# ---------- settings: change a number here, not inside a function ----------

GROUND_SIZE = 40.0            # the ground is GROUND_SIZE x GROUND_SIZE
# Settings with names, so I can change a number here once instead of hunting inside the code.
AREA = 18.0                   # rocks and trees land within -AREA..AREA on X and Z
PATH_WIDTH = 4.0              # the path runs along Z, centred on x = 0
PATH_MARGIN = 1.0             # keep things at least this far back from the path's edges
POND_CENTER = (10.0, 10.0)    # x, z
POND_RADIUS = 6.0
MAX_TRIES_PER_ITEM = 20       # give up on a spot after this many misses per item

ROCK_GROUP = "rocks"
TREE_GROUP = "trees"


# ---------- one thing at a time ----------

def paint(obj, kind, r, g, b):
    """Give obj the flat colour for its kind. One shader per kind, made once."""
    shader = kind + "_mat"
    if not cmds.objExists(shader):
        shader = cmds.shadingNode("lambert", asShader=True, n=shader)
        cmds.setAttr(shader + ".color", r, g, b, type="double3")
        sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, n=shader + "SG")
        cmds.connectAttr(shader + ".outColor", sg + ".surfaceShader")
    cmds.sets(obj, e=True, forceElement=shader + "SG")


# A named job: make one rock at a spot and give back its name so I can use it later.
def make_rock(x, z, size=1.0):
    """A low-poly sphere, squashed and spun so it reads as a rock. Returns its name."""
    rock = cmds.polySphere(r=0.5, sx=6, sy=4, n="rock")[0]
    cmds.scale(size * random.uniform(0.8, 1.6),
               size * random.uniform(0.4, 0.9),
               size * random.uniform(0.8, 1.6), rock)
    cmds.rotate(0, random.uniform(0, 360), 0, rock)
    cmds.move(x, 0, z, rock)
    paint(rock, "rock", 0.42, 0.40, 0.37)
    return rock


def make_tree(x, z, height=3.0):
    """A trunk and a canopy, grouped so the tree moves as one thing. Returns the group."""
    trunk = cmds.polyCylinder(r=height * 0.06, h=height * 0.5, n="trunk")[0]
    cmds.move(0, height * 0.25, 0, trunk)
    canopy = cmds.polyCone(r=height * 0.35, h=height * 0.7, n="canopy")[0]
    cmds.move(0, height * 0.85, 0, canopy)
    paint(trunk, "trunk", 0.36, 0.24, 0.14)
    paint(canopy, "canopy", 0.18, 0.42, 0.20)
    tree = cmds.group(trunk, canopy, n="tree")
    cmds.move(x, 0, z, tree)
    return tree


# ---------- the rules ----------

def is_clear(x, z):
    """True when (x, z) is off the path (plus its margin) and out of the pond."""
# Ask a question: is this spot on the path? If yes, it is not a good place for a rock or tree.
    if abs(x) < PATH_WIDTH / 2.0 + PATH_MARGIN:
        return False
    if math.hypot(x - POND_CENTER[0], z - POND_CENTER[1]) < POND_RADIUS:
        return False
    return True


def group_for(name):
    """The group that holds everything of one kind. Made on first use."""
    if not cmds.objExists(name):
        cmds.group(empty=True, n=name)
    return name


# ---------- many at once ----------

def random_spot(area, keep_clear):
    """A random (x, z) inside the area, or None if no clear spot turned up."""
    for _ in range(MAX_TRIES_PER_ITEM):
        x = random.uniform(-area, area)
        z = random.uniform(-area, area)
        if not keep_clear or is_clear(x, z):
            return x, z
    return None


def scatter_rocks(count, area=AREA, keep_clear=True):
    """Place `count` rocks at random under the rocks group. Returns how many were placed."""
    grp = group_for(ROCK_GROUP)
    placed = 0

# Repeat once for every rock I asked for: find a free spot, make a rock, put it in the group.
    for _ in range(count):
        spot = random_spot(area, keep_clear)
        if spot is None:
            continue
        rock = make_rock(spot[0], spot[1], size=random.uniform(0.5, 1.5))
        cmds.parent(rock, grp)
        placed += 1
    return placed


def scatter_trees(count, area=AREA, keep_clear=True):
    """Place `count` trees at random under the trees group. Returns how many were placed."""
    grp = group_for(TREE_GROUP)
    placed = 0
    for _ in range(count):
        spot = random_spot(area, keep_clear)
        if spot is None:
            continue
        tree = make_tree(spot[0], spot[1], height=random.uniform(2.5, 4.5))
        cmds.parent(tree, grp)
        placed += 1
    return placed


def scatter(rocks=30, trees=12, area=AREA, keep_clear=True, seed=None, with_ground=True):
    """The whole set in one undo step. Same seed + same settings = same set.

    with_ground builds the ground, path and pond first (if missing), inside the
    same undo step, so one click is always one Ctrl+Z.
    Returns (rocks_placed, trees_placed).
    """
    if seed is not None:
        random.seed(seed)
    cmds.undoInfo(openChunk=True, chunkName="scatter")
    try:
        if with_ground:
            build_ground()
        rocks_placed = scatter_rocks(rocks, area, keep_clear)
        trees_placed = scatter_trees(trees, area, keep_clear)
        cmds.select(clear=True)  # leave nothing selected, inside the same undo step
    finally:
        cmds.undoInfo(closeChunk=True)
    if rocks_placed < rocks or trees_placed < trees:
        cmds.warning("Placed %d of %d rocks and %d of %d trees: not enough clear room."
                     % (rocks_placed, rocks, trees_placed, trees))
    print("Set dresser: placed %d rocks and %d trees." % (rocks_placed, trees_placed))
    return rocks_placed, trees_placed


def build_ground(size=GROUND_SIZE):
    """The ground, the path and the pond. Skips anything that already exists."""
    if not cmds.objExists("ground"):
        ground = cmds.polyPlane(w=size, h=size, sx=1, sy=1, n="ground")[0]
        paint(ground, "ground", 0.33, 0.38, 0.22)
    if not cmds.objExists("path"):
        path = cmds.polyPlane(w=PATH_WIDTH, h=size, sx=1, sy=1, n="path")[0]
        cmds.move(0, 0.02, 0, path)
        paint(path, "path", 0.62, 0.55, 0.40)
    if not cmds.objExists("pond"):
        pond = cmds.polyCylinder(r=POND_RADIUS, h=0.04, n="pond")[0]
        cmds.move(POND_CENTER[0], 0.02, POND_CENTER[1], pond)
        paint(pond, "pond", 0.22, 0.36, 0.48)


def clear():
    """Delete only what scatter made (the rocks and trees groups). The ground stays."""
    gone = 0
    for name in (ROCK_GROUP, TREE_GROUP):
        if cmds.objExists(name):
            cmds.delete(name)
            gone += 1
    if gone == 0:
        cmds.warning("Nothing to clear.")
