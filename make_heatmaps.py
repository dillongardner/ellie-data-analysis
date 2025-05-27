# %%
import os

import matplotlib.pyplot as plt
import polars as pl
import seaborn as sns

from format import format_selections, format_boards, format_board_v1, combine
from heatmaps import make_heatmap_arr, make_heatmap_plot_by_menu

OUTPUT_PATH = "./figures/iteration_2/"
BOARD_FILE = "./data/iteration_2_board.csv"
SELECTIONS_FILE ="./data/iteration_2_selections.csv"
# %%
def main(board_file: str=BOARD_FILE,
         selections_file: str=SELECTIONS_FILE,
         output_path: str=OUTPUT_PATH,
         is_v1: bool=False,
         max_board_ln: int=None,):

    board = pl.read_csv(board_file)
    if max_board_ln:
        board = board.filter(pl.col("Line Number") <= max_board_ln)
    selections = pl.read_csv(selections_file)

    if is_v1:
        formatted_board = format_board_v1(board)
    else:
        formatted_board = format_boards(board)
    formatted_board.write_csv(os.path.join(output_path, "formatted_board.csv"))

    formatted_selections = format_selections(selections)
    formatted_selections.write_csv(os.path.join(output_path, "formatted_selections.csv"))

    bad_match_base: pl.DataFrame = formatted_selections.join(formatted_board,
                                                 how="left",
                                                 on="selection",)
    bad_matches = bad_match_base.filter(pl.col('full_pattern').is_null()).group_by("selection").len().sort("len", descending=True)
    bad_matches.write_csv(os.path.join(output_path, "missing_selections.csv"))

    df = combine(selections=formatted_selections, board=formatted_board,)


    df.write_csv(os.path.join(output_path, "full_selections.csv"))

    plot_df = df.filter(pl.col("is_match"))


    # Create figure with constrained layout to handle colorbar properly
    fig = plt.figure(figsize=(7, 3), layout='constrained')
    ax = fig.add_subplot(111)

    arr = make_heatmap_arr(plot_df)

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
        fig, ax = make_heatmap_plot_by_menu(plot_df, menu, board=formatted_board)
        fig.savefig(os.path.join(output_path, f"{menu}_cts.png"))
        plt.close(fig)
        fig, ax = make_heatmap_plot_by_menu(plot_df, menu, board=formatted_board, normalize=True)
        fig.savefig(os.path.join(output_path, f"{menu}_pct.png"))
        plt.close(fig)

if __name__ == "__main__":
    main('./data/iteration_2_board.csv',
         './data/iteration_2_selections.csv',
         './figures/iteration_2')
    main('./data/iteration_1_board.csv',
         './data/iteration_1_selections.csv',
         './figures/iteration_1', is_v1=True)
    main('./data/iteration_3_board.csv',
         './data/iteration_3_selections.csv',
         './figures/iteration_3',
         max_board_ln=947,)


