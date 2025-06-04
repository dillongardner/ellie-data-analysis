#%%

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

selections1 = pd.read_csv("./figures/iteration_1/full_selections.csv").assign(
    iteration="iteration_1"
)
selections2 = pd.read_csv("./figures/iteration_2/full_selections.csv").assign(
    iteration="iteration_2"
)
selections3 = pd.read_csv("./figures/iteration_3/full_selections.csv").assign(
    iteration="iteration_3"
)

all_selections = pd.concat([selections1, selections2, selections3])

#%%
# group_cols = ["Training/ Spontaneous",
#               "Utterance: Single word or phrase",
#               "Type of Sign",]

#%%

group_col = "Training/ Spontaneous"

# Get counts using groupby and unstack
counts = (all_selections.groupby(["iteration", group_col])
         .size()
         .unstack(fill_value=0))

# Convert to percentages
percentages = counts.div(counts.sum(axis=1), axis=0) * 100

# Calculate standard errors
n = counts.sum(axis=1)
std_errs = np.sqrt((percentages * (100 - percentages)) / (n.values.reshape(-1, 1))) 

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
           yerr=std_errs[category] * 1.96,  # 95% confidence interval
           capsize=3)

# Customize the plot
ax.set_ylabel("Percentage")
ax.set_title(f"Distribution of {group_col}")
ax.set_xticks(x)
ax.set_xticklabels(percentages.index, rotation=45)
ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')

# Adjust layout to prevent label cutoff
plt.tight_layout()
plt.show()




