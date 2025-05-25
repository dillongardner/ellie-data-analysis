KEY_MAP = dict(
    A=(0, 0),
    B=(0, 1),
    C=(0, 2),
    D=(0, 3),
    E=(0, 4),
    F=(0, 5),
    G=(1, 0),
    H=(1, 1),
    I=(1, 2),
    J=(1, 3),
    K=(1, 4),
    L=(1, 5),
    M=(2, 0),
    N=(2, 1),
    O=(2, 2),
    P=(2, 3),
    Q=(2, 4),
    R=(2, 5),
)
BOARD_ROWS = 3
BOARD_COLS = 6

FORMATTED_SELECTIONS_COL = [
    "Line Number",
    "Location path code",
    "selection",
    "source",
    "word",
    "menu",
    "menu_ff",
]
FORMATTED_BOARD_COLS = [
    "Line Number",
    "full_pattern",
    "menu_pattern",
    "button",
    "menu_title",
    "is_menu",
    "menu_multiplicity",
    "multiplicity",
]
MATCHING_COLS = [
    "is_match",
    "match_type"
]
FULL_SELECTIONS_COLS = (FORMATTED_SELECTIONS_COL
                        + [c for c in FORMATTED_BOARD_COLS if c not in FORMATTED_SELECTIONS_COL]
                        + MATCHING_COLS)
