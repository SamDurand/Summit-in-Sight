import pandas as pd
from summit_lib import plot_locations_map

grid_locations = pd.read_csv("data/results/global.csv")
sorted_grid_locations = grid_locations.sort_values(by="view_possible", ascending=False)
plot_locations_map(sorted_grid_locations, color="view_possible")