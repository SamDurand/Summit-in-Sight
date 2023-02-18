import pandas as pd
from summit_lib import *

grid_locations = pd.read_csv("data/summits_Europe_list.csv")

location_summit = [45.832542 , 6.864717] # Mont Blanc
offset_view = 2
offset_summit = -100

grid_locations_processed = summit_is_visible_multi_locations_offline(grid_locations, location_summit, offset_view, offset_summit)  # Process the data 
grid_locations_processed.to_csv("data/results/list_from_summits.csv", index=False)  # Save data to csv file