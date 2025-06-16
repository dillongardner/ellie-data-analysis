#%%

import polars as pl

board1 = pl.read_csv("./figures/iteration_1/formatted_board.csv").with_columns(
    pl.lit("iteration_1").alias("iteration")
)
board2 = pl.read_csv("./figures/iteration_2/formatted_board.csv").with_columns(
    pl.lit("iteration_2").alias("iteration")
)
board3 = pl.read_csv("./figures/iteration_3/formatted_board.csv").with_columns(
    pl.lit("iteration_3").alias("iteration")
)

cols = ["selection", "iteration", "is_menu"]
all_boards = pl.concat([board1[cols], board2[cols], board3[cols]])
# %%

summary = all_boards.group_by(
    ["selection", "iteration", "is_menu"]
).len().sort(["selection", "iteration", "is_menu"])
summary
summary.write_csv("word_summary.csv")

# %%

cts = (summary
       .drop_nans()
       .filter(pl.col("selection") != "")
       .group_by(["selection", "iteration"])
       .agg(pl.col("len").sum().alias("count"))
       .group_by("iteration")
       .agg(pl.col("count").sum().alias("total_count"),
            pl.col("selection").count().alias("n_unique_words")
            ))
cts.write_csv("unique_word_counts.csv")
# %%
