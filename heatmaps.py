# %%
import os

import matplotlib.pyplot as plt
import polars as pl
import seaborn as sns
import numpy as np


OUTPUT_PATH = "./figures"
KEY_MAP = dict(
    A=(0,0),
    B=(0,1),
    C=(0,2),
    D=(0,3),
    E=(0,4),
    F=(0,5),
    G=(1,0),
    H=(1,1),
    I=(1,2),
    J=(1,3),
    K=(1,4),
    L=(1,5),
    M=(2,0),
    N=(2,1),
    O=(2,2),
    P=(2,3),
    Q=(2,4),
    R=(2,5),
)
#%%

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
    result = df.with_columns(
        terminal_level.alias("terminal_level")
    ).with_columns(
        pl.col("terminal_level").str.replace("\xa0", " ", n=-1).str.splitn(" ", 2).alias("splits")
    ).with_columns(
        pl.col("splits").struct.field("field_0").alias("full_pattern"),
        pl.col("splits").struct.field("field_1").str.strip_chars().str.to_uppercase().alias("terminal_selection"),
    ).select(
        "terminal_level",
        "full_pattern",
        pl.col("terminal_selection").str.replace("  ", " ").alias("terminal_selection"),
    )
    return result

formatted_board = format_boards(board)
formatted_selections = format_selections(selections)


# %%
df: pl.DataFrame = formatted_selections.join(formatted_board,
                          how="left",
                          left_on="selection",
                          right_on="terminal_selection")
bad_matches = df.filter(pl.col('full_pattern').is_null()).group_by("selection").len().sort("len", descending=True)
bad_matches.write_csv(os.path.join(OUTPUT_PATH, "missing_selections.csv"))
bad_matches
df = df.filter(pl.col('full_pattern').is_not_null())
# %%

def make_full_heatmap_arr(df: pl.DataFrame) -> np.ndarray:
    arr = np.zeros((3,6), dtype=float)
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
# plt.show()
# %%
