# %%
import polars as pl

# %%

board2 = pl.read_csv("./figures/iteration_2/formatted_board.csv")
board3 = pl.read_csv("./figures/iteration_2/formatted_board.csv")
selections2 = pl.read_csv("./figures/iteration_2/formatted_selections.csv")

# %%
formatted_board: pl.LazyFrame = board2.lazy()
formatted_selections: pl.LazyFrame = selections2.lazy()

high_confidence = ((
                           (pl.col("source") == pl.lit("MENU"))
                           & (pl.col("selection") == pl.col("selection_right"))
                           & (pl.col("is_menu"))
                           & (pl.col("duplicity") == 1)
                   )
                   | (
                           (
                                   (pl.col("source") == pl.lit("FINAL"))
                                   & (pl.col("selection") == pl.col("selection_right")))
                           & (
                                   (pl.col("duplicity") == 1) |
                                   (pl.col("menu_ff") == pl.col("menu_title"))
                           )
                   ))

low_confidence = (
        (pl.col("selection") == pl.col("selection_right"))
        &
        (pl.col("duplicity") <= 2)
)

df: pl.LazyFrame = formatted_selections.join(
    formatted_board, how="cross"
).with_columns(
    high_confidence.alias("high_confidence"),
    low_confidence.alias("low_confidence"),
)

# %%
res = df.filter((pl.col("high_confidence")) | (pl.col("low_confidence"))
                ).collect()

# %%

res.filter(
    (pl.col("high_confidence")) & (pl.col("duplicity") > 1)
)
