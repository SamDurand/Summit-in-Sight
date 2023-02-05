from summit_lib import *

top_left_corner, bottom_right_corner = [47 , 5], [45 , 8]
location_summit = [45.832542 , 6.864717] # Mont_Blanc
offset_view = 2
offset_summit = -100
res = 50 #km

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

grid_locations = generate_locations_grid(top_left_corner, bottom_right_corner, res)
grid_locations_processed = summit_is_visible_multi_locations(grid_locations, location_summit, offset_view, offset_summit)
grid_locations_processed.to_csv("data.csv")