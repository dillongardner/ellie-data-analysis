from typing import List

import numpy as np
import polars as pl
import seaborn as sns
from matplotlib import pyplot as plt

from constants import BOARD_ROWS, BOARD_COLS, KEY_MAP


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


def make_labels(arr, menu: str, board: pl.DataFrame, normalized: bool = False, max_length: int = 15,
                wrap: bool = True) -> List[List[str]]:
    board = board.filter(pl.col("menu_title") == menu)
    phrase_indices = [(r[1], KEY_MAP.get(r[0], "")) for r in board.select("button", "selection").iter_rows()]
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


def make_heatmap_plot_by_menu(df: pl.DataFrame,
                              menu: str,
                              board: pl.DataFrame,
                              normalize: bool = False,
                              max_length: int = 15,
                              wrap: bool = True) -> tuple[plt.Figure, plt.Axes]:
    plot_df = df.filter(pl.col("menu_title") == menu)
    fig = plt.figure(figsize=(10, 5), layout='constrained')  # Increased figure size
    ax = fig.add_subplot(111)
    arr = make_heatmap_arr(plot_df, normalize=normalize)

    # Format the annotations as percentages
    # Create a version of the array with formatted strings
    labels = make_labels(arr, menu, board, normalize, max_length=max_length, wrap=wrap)

    # Use the number of rows (2) as the base for the colorbar aspect ratio
    # This will make the colorbar height match the heatmap height
    sns.heatmap(arr, ax=ax, xticklabels=False, yticklabels=False, cbar_kws={'aspect': 10},
                annot=labels, fmt="", annot_kws={"fontsize": 10})  # Added smaller font size
    ax.set_title(menu)
    return fig, ax
