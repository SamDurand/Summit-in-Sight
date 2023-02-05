from summit_lib import plot_locations_map
import pandas as pd

grid_locations = pd.read_csv("data/Summits_Alps_view_possible.csv")
plot_locations_map(grid_locations, color="view_possible")