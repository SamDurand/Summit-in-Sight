import pandas as pd
from summit_lib import *

data = pd.read_csv("data\list_summits_pyrenees.csv")

location_summit = [45.832542 , 6.864717] # Mont Blanc
offset_view = 2
offset_summit = -100

grid_locations = data[["Name", "latitude", "longitude"]]  # Extract the columns needed for processing 
grid_locations_processed = summit_is_visible_multi_locations(grid_locations, location_summit, offset_view, offset_summit)  # Process the data 
grid_locations_processed.to_csv("data/vosges.csv")  # Save data to csv file