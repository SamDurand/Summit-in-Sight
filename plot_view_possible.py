from summit_lib import plot_locations_map
import pandas as pd

# Plot the results of summit visibility
grid_locations = pd.read_csv("data/results/global.csv")
grid_locations.sort_values(by="view_possible", ascending=False)

plot_locations_map(grid_locations, color="view_possible")