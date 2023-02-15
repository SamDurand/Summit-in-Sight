from summit_lib import generate_locations_grid, summit_is_visible_multi_locations_online

top_left_corner, bottom_right_corner = [50, -7], [36, 19] # Grid covering west Europe 

location_summit = [45.832542 , 6.864717] # The summit to spot: Mont_Blanc, 4810m, France

offset_view = 2 # Your elevation from the ground at your location_point (can be either positive or 0)
offset_summit = -100 # How much of the summit you want to see. For example, if 0, you will test your location with exactly the altitude of the peak to spot. 
# If -100, you will test if you can see from your location the last 100 meters of the summit.
res = 500 # Resolution in kilometers. Defaults to 10.

# Generate grid of locations
grid_locations = generate_locations_grid(top_left_corner, bottom_right_corner, res)

# Determine the visibility of the summit from each position
grid_locations_processed = summit_is_visible_multi_locations_online(grid_locations, location_summit, offset_view, offset_summit)

# Save data to csv file
grid_locations_processed.to_csv("data_multi_locations_online.csv")