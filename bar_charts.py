#%%

import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

OUTPUT_DIR = "./figures/bar_charts"

selections1 = pd.read_csv("./figures/iteration_1/full_selections.csv").assign(
    iteration="iteration_1"
)
selections2 = pd.read_csv("./figures/iteration_2/full_selections.csv").assign(
    iteration="iteration_2"
)
selections3 = pd.read_csv("./figures/iteration_3/full_selections.csv").assign(
    iteration="iteration_3"
)

board1 = pd.read_csv("./figures/iteration_1/formatted_board.csv").assign(
    iteration="iteration_1"
)
board2 = pd.read_csv("./figures/iteration_2/formatted_board.csv").assign(
    iteration="iteration_2"
)
board3 = pd.read_csv("./figures/iteration_3/formatted_board.csv").assign(
    iteration="iteration_3"
)

col_map = {"Training/ Spontaneous": "Training",
           "Utterance: Single word or phrase": "Type of Utterance"}
all_selections = pd.concat([selections1, selections2, selections3]).rename(col_map, axis=1)
all_boards = pd.concat([board1, board2, board3]).rename(col_map, axis=1)

#%%
group_cols = ["Training",
              "Type of Utterance",
              "Type of Sign", 
              "Category"]

#%%

def make_barchart(df: pd.DataFrame, col: str, title:str):
    # Get counts using groupby and unstack
    counts = (df.groupby(["iteration", group_col])
            .size()
            .unstack(fill_value=0))

    # Convert to percentages
    percentages = counts.div(counts.sum(axis=1), axis=0) * 100

    # Setup the plot
    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot bars
    x = np.arange(len(percentages.index))
    width = 0.8 / len(percentages.columns)
    for i, (category, data) in enumerate(percentages.items()):
        ax.bar(x + i*width - width*len(percentages.columns)/2 + width/2,
            data,
            width,
            label=category,
            capsize=3)

    # Customize the plot
    ax.set_ylabel("Percentage")
    ax.set_title(title)
    ax.set_xticks(x)
    ax.set_xticklabels(percentages.index, rotation=45)
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    return fig, ax

for group_col in group_cols:
    selections_title = f"Distributions of Selections\nBy {group_col}"
    selections_name = f"selections_{group_col}"
    fig, ax = make_barchart(df=all_selections, 
                            col=group_col,
                            title=selections_title)
    plt.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR,selections_name))
    plt.close(fig)

    board_title = f"Distributions of Board Items\nBy {group_col}"
    board_name = f"board_{group_col}"
    fig, ax = make_barchart(df=all_boards, 
                            col=group_col,
                            title=board_title)
    plt.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR,board_name))
    plt.close(fig)






# %%
