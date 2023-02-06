from summit_lib import plot_locations_map
import pandas as pd

grid_locations = pd.read_csv("data/NW_Alps_res=0.5.csv")
plot_locations_map(grid_locations, color="view_possible")