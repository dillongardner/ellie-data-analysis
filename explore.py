#%%

import pandas as pd
import format
import constants


# board1 = pl.read_csv("./figures/iteration_1/formatted_board.csv")
# board2 = pl.read_csv("./figures/iteration_2/formatted_board.csv")
# board3 = pl.read_csv("./figures/iteration_3/formatted_board.csv")
# selections1 = pl.read_csv("./figures/iteration_1/formatted_selections.csv")
# selections2 = pl.read_csv("./figures/iteration_2/formatted_selections.csv")
# selections3 = pl.read_csv("./figures/iteration_3/formatted_selections.csv")





df1 = pd.read_csv("./figures/iteration_1/full_selections.csv")
df2 = pd.read_csv("./figures/iteration_2/full_selections.csv")
df3 = pd.read_csv("./figures/iteration_3/full_selections.csv")

#%%
group_cols = ["Training/ Spontaneous",
              "Utterance: Single word or phrase",
              "Type of Sign",]

#%%
import seaborn as sns

sns.barplot()




