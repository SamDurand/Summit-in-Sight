from summit_lib import *

# res en km
top_left_corner, bottom_right_corner, location_summit = [47 , 5], [45 , 8], [45.832542 , 6.864717]
offset_view = 2
offset_summit = -100
res = 50

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

grid_locations = generate_locations_grid(top_left_corner, bottom_right_corner, res)
grid_locations_processed = summit_is_visible_multi_locations(grid_locations, location_summit, offset_view, offset_summit)

grid_locations_processed.to_csv("data.csv")

plot_locations_map(grid_locations=grid_locations_processed, color="view_possible")