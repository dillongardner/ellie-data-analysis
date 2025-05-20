# %%
import os
from typing import List

import matplotlib.pyplot as plt
import polars as pl
import seaborn as sns
import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure

OUTPUT_PATH = "./figures/iteration_2/"
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
# %%

board = pl.read_csv("./data/iteration_2_board.csv")
selections = pl.read_csv("./data/iteration_2_selections.csv")


# %%

def format_selections(df: pl.DataFrame) -> pl.DataFrame:
    terminal_press = pl.coalesce(pl.col("Word/Phrase"), pl.col("Menu"))
    result = df.with_columns(
        terminal_press.str.to_uppercase().alias("selection")
    ).filter(
        pl.col("selection").is_not_null()
    ).select("Date/Video Link",
             (pl.col("selection").str.strip_chars()
              .str.replace("  ", " ")
              .str.replace("BEETHOVEN AND DVORAK", "BEETHOVEN & DVORAK")
              .alias("selection"))
             )
    return result


def format_boards(df: pl.DataFrame) -> pl.DataFrame:
    terminal_level = pl.coalesce(
        pl.col("L5"), pl.col("L4"), pl.col("L3"), pl.col("L2"), pl.col("L1"),
    )
    df = df.with_columns(
        terminal_level.alias("terminal_level")
    ).with_columns(
        pl.col("terminal_level").str.replace("\xa0", " ", n=-1).str.splitn(" ", 2).alias("splits")
    ).with_columns(
        pl.col("splits").struct.field("field_0").alias("full_pattern"),
        pl.col("splits").struct.field("field_1").str.strip_chars().str.to_uppercase().alias("phrase"),
    ).select(
        "terminal_level",
        "full_pattern",
        pl.col("phrase").str.replace("  ", " ").alias("phrase"),
    ).with_columns(
        str_length=pl.col("full_pattern").str.len_chars()
    ).with_columns(
        menu_pattern=pl.col("full_pattern").str.slice(0, pl.col("str_length") - 1),
        button=pl.col("full_pattern").str.slice(-1)
    ).select(
        "full_pattern",
        "menu_pattern",
        "button",
        "phrase",
    )
    result = df.join(
        df.select(
            "full_pattern", pl.col("phrase").alias("menu_title")
        ),
        how="left",
        left_on="menu_pattern",
        right_on="full_pattern"
    ).with_columns(
        menu_title=pl.col("menu_title").fill_null(value="MAIN MENU")
    )

    return result


formatted_board = format_boards(board)
formatted_selections = format_selections(selections)

# %%
df: pl.DataFrame = formatted_selections.join(formatted_board,
                                             how="left",
                                             left_on="selection",
                                             right_on="phrase")
bad_matches = df.filter(pl.col('full_pattern').is_null()).group_by("selection").len().sort("len", descending=True)
bad_matches.write_csv(os.path.join(OUTPUT_PATH, "missing_selections.csv"))
bad_matches
df = df.filter(pl.col('full_pattern').is_not_null())


# %%

def make_full_heatmap_arr(df: pl.DataFrame) -> np.ndarray:
    arr = np.zeros((BOARD_ROWS, BOARD_COLS), dtype=float)
    s = df["full_pattern"].str.split("").explode().value_counts()
    total = s["count"].sum()
    for r in s.iter_rows():
        i, j = KEY_MAP[r[0]]
        arr[i][j] = r[1] / total * 100.0
    return arr


# Create figure with constrained layout to handle colorbar properly
fig = plt.figure(figsize=(7, 3), layout='constrained')
ax = fig.add_subplot(111)

arr = make_full_heatmap_arr(df)

# Format the annotations as percentages
# Create a version of the array with formatted strings
labels = [[f"{val:.1f}%" for val in row] for row in arr]

# Use the number of rows (2) as the base for the colorbar aspect ratio
# This will make the colorbar height match the heatmap height
sns.heatmap(arr, ax=ax, xticklabels=False, yticklabels=False, cbar_kws={'aspect': 10},
            annot=labels, fmt="")
fig.savefig(os.path.join(OUTPUT_PATH, "heatmap_all.png"))
plt.show()
# %%

(formatted_board
 .with_columns(str_length=pl.col("full_pattern").str.len_chars())
 .with_columns(menu=pl.col("full_pattern").str.slice(0, pl.col("str_length") - 1))
 #  .select(pl.col("full_pattern").str.slice(0,2))
 )


# %%

def explode_df(df: pl.DataFrame, pattern_col: str = "full_pattern") -> pl.DataFrame:
    # Create a new dataframe with exploded patterns
    return (
        df
        # First, create a column with the length of each pattern
        .with_columns(pattern_length=pl.col(pattern_col).str.len_chars())
        # Create sequence from 0 to length-1 for each row
        .with_columns(
            indices=pl.struct(["pattern_length"]).map_elements(
                lambda x: list(range(x["pattern_length"])),
                return_dtype=pl.List(pl.Int64)
            )
        )
        # Explode the indices to create multiple rows
        .explode("indices")
        # Create the menu column (characters before current index)
        .with_columns(
            menu_pattern=pl.col(pattern_col).str.slice(0, pl.col("indices")),
            # Create the button column (character at the current index)
            button=pl.col(pattern_col).str.slice(pl.col("indices"), 1)
        )
        .select(
            pl.col(pattern_col),
            "menu_pattern",
            "button"
        )
    )


def make_full_press_df(df: pl.DataFrame, formatted_board: pl.DataFrame) -> pl.DataFrame:
    exploded = explode_df(df)
    result = exploded.join(
        formatted_board,
        how="left",
        on=["menu_pattern", "button"],
    )
    return result


full_press_df = make_full_press_df(df, formatted_board)


# %%

def make_heatmap_arr(df, normalize: bool = True) -> np.ndarray:
    arr = np.zeros((3, 6), dtype=float)
    s = df["button"].value_counts()
    total = s["count"].sum()
    for r in s.iter_rows():
        i, j = KEY_MAP[r[0]]
        if normalize:
            arr[i][j] = r[1] / total * 100.0
        else:
            arr[i][j] = r[1]
    return arr


def make_labels(arr, menu: str, normalized: bool = False, board: pl.DataFrame = formatted_board, max_length: int = 15,
                wrap: bool = True) -> List[List[str]]:
    board = board.filter(pl.col("menu_title") == menu)
    phrase_indices = [(r[1], KEY_MAP.get(r[0],"")) for r in board.select("button", "phrase").iter_rows()]
    labels = [["" for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
    for phrase, (i, j) in phrase_indices:
        # Truncate long phrases
        if not phrase:
            phrase = ""
        if len(phrase) > max_length:
            if wrap and " " in phrase:
                # Simple word wrapping by splitting at space closest to middle
                mid = len(phrase) // 2
                left_space = phrase.rfind(" ", 0, mid)
                right_space = phrase.find(" ", mid)

                if left_space != -1 and (right_space == -1 or mid - left_space <= right_space - mid):
                    split_pos = left_space
                elif right_space != -1:
                    split_pos = right_space
                else:
                    # No spaces, just truncate
                    display_phrase = phrase[:max_length - 3] + "..."

                if left_space != -1 or right_space != -1:
                    display_phrase = phrase[:split_pos] + "\n" + phrase[split_pos + 1:]
            else:
                display_phrase = phrase[:max_length - 3] + "..."
        else:
            display_phrase = phrase

        if normalized:
            labels[i][j] = f"{display_phrase}\n{arr[i, j]:.1f}%"
        else:
            labels[i][j] = f"{display_phrase}\n{int(arr[i, j])}"
    return labels


def make_heatmap_plot_by_menu(df: pl.DataFrame, menu: str, normalize: bool = False, max_length: int = 15,
                              wrap: bool = True) -> tuple[plt.Figure, plt.Axes]:
    plot_df = df.filter(pl.col("menu_title") == menu)
    fig = plt.figure(figsize=(10, 5), layout='constrained')  # Increased figure size
    ax = fig.add_subplot(111)
    arr = make_heatmap_arr(plot_df, normalize=normalize)

    # Format the annotations as percentages
    # Create a version of the array with formatted strings
    labels = make_labels(arr, menu, normalize, max_length=max_length, wrap=wrap)

    # Use the number of rows (2) as the base for the colorbar aspect ratio
    # This will make the colorbar height match the heatmap height
    sns.heatmap(arr, ax=ax, xticklabels=False, yticklabels=False, cbar_kws={'aspect': 10},
                annot=labels, fmt="", annot_kws={"fontsize": 10})  # Added smaller font size
    ax.set_title(menu)
    return fig, ax


# %%

# Example of using the improved heatmap function
fig, ax = make_heatmap_plot_by_menu(full_press_df, "SAY HELLO TO", normalize=False, max_length=12, wrap=True)
plt.show()

# %%

menus = formatted_board["menu_title"].unique().to_list()
for menu in menus:
    fig, ax = make_heatmap_plot_by_menu(full_press_df, menu)
    fig.savefig(os.path.join(OUTPUT_PATH, f"{menu}.png"))
    plt.close(fig)


