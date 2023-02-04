from summit_lib import *

data = pd.read_excel("data/List_Summits_from_wiki.xlsx")
grid_locations = pd.DataFrame()
grid_locations["lat_grid"], grid_locations["lon_grid"] = data["latitude"], data["longitude"]

location_summit = [45.832542 , 6.864717]
offset_view = 2
offset_summit = -50

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

grid_locations_processed = summit_is_visible_multi_locations(grid_locations, location_summit, offset_view, offset_summit)
grid_locations_processed.to_csv("data.csv")