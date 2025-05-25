#%%

import polars as pl
import format
import constants


board1 = pl.read_csv("./figures/iteration_1/formatted_board.csv")
board2 = pl.read_csv("./figures/iteration_2/formatted_board.csv")
board3 = pl.read_csv("./figures/iteration_3/formatted_board.csv")
selections1 = pl.read_csv("./figures/iteration_1/formatted_selections.csv")
selections2 = pl.read_csv("./figures/iteration_2/formatted_selections.csv")
selections3 = pl.read_csv("./figures/iteration_3/formatted_selections.csv")



df1 = format.combine(selections=selections1, board=board1)
df2 = format.combine(selections=selections2, board=board2)
df3 = format.combine(selections=selections3, board=board3)

#%%

if __name__ == "__main__":
    "hello"


