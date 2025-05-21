#%%
import polars as pl

#%%

board2 = pl.read_csv("./figures/iteration_2/formatted_board.csv")
selections2 = pl.read_csv("./data/iteration_2_selections.csv")
board2_selection_cts = board2.group_by("selection").len()
board2_selection_menue_cts = board2.group_by("selection", "menu_title").len()

#%%
tandw = selections2.filter(pl.col("Word/Phrase") == "Temp and weather")
