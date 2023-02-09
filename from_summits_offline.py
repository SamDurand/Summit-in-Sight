from summit_lib import *

data = pd.read_csv("data\list_summits_massif_central.csv")

grid_locations = pd.DataFrame()
grid_locations["name"], grid_locations["lat_grid"], grid_locations["lon_grid"] = data["Name"], data["latitude"], data["longitude"]

location_summit = [45.832542 , 6.864717] # Mont Blanc
offset_view = 2
offset_summit = -100

grid_locations_processed = summit_is_visible_multi_locations(grid_locations, location_summit, offset_view, offset_summit)

# Save data to csv file
grid_locations_processed.to_csv("data_massif_central.csv")