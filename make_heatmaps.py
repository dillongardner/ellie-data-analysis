# %%
import os

import matplotlib.pyplot as plt
import polars as pl
import seaborn as sns

from format import format_selections, format_boards
from heatmaps import make_heatmap_arr, make_heatmap_plot_by_menu

OUTPUT_PATH = "./figures/iteration_2/"
BOARD_FILE = "./data/iteration_2_board.csv"
SELECTIONS_FILE ="./data/iteration_2_selections.csv"
# %%
def main(board_file: str=BOARD_FILE,
         selections_file: str=SELECTIONS_FILE,
         output_path: str=OUTPUT_PATH):

    board = pl.read_csv(board_file)
    selections = pl.read_csv(selections_file)


    formatted_board = format_boards(board)
    formatted_selections = format_selections(selections)

    df: pl.DataFrame = formatted_selections.join(formatted_board,
                                                 how="left",
                                                 on="selection",)
    bad_matches = df.filter(pl.col('full_pattern').is_null()).group_by("selection").len().sort("len", descending=True)
    bad_matches.write_csv(os.path.join(output_path, "missing_selections.csv"))
    bad_matches
    df = df.filter(pl.col('full_pattern').is_not_null())
    df.write_csv(os.path.join(output_path, "full_selections.csv"))


    # %%


    # Create figure with constrained layout to handle colorbar properly
    fig = plt.figure(figsize=(7, 3), layout='constrained')
    ax = fig.add_subplot(111)

    arr = make_heatmap_arr(df)

    # Format the annotations as percentages
    # Create a version of the array with formatted strings
    labels = [[f"{val:.1f}%" for val in row] for row in arr]

    # Use the number of rows (2) as the base for the colorbar aspect ratio
    # This will make the colorbar height match the heatmap height
    sns.heatmap(arr, ax=ax, xticklabels=False, yticklabels=False, cbar_kws={'aspect': 10},
                annot=labels, fmt="")
    fig.savefig(os.path.join(output_path, "heatmap_all.png"))
    plt.close(fig)

    menus = formatted_board["menu_title"].unique().to_list()
    for menu in menus:
        fig, ax = make_heatmap_plot_by_menu(df, menu, board=formatted_board)
        fig.savefig(os.path.join(output_path, f"{menu}.png"))
        plt.close(fig)

if __name__ == "__main__":
    main()


