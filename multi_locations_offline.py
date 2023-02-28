from summit_lib import generate_locations_grid, summit_is_visible_multi_locations_offline, summit_is_visible_fast_offline

top_left_corner, bottom_right_corner = [48, 5], [47, 8] # Grid covering west Europe 

location_summit = [45.832542 , 6.864717] # The summit to spot: Mont_Blanc, 4810m, France

offset_view = 2 # Your elevation from the ground at your location_point (can be either positive or 0)
offset_summit = -100 # How much of the summit you want to see. For example, if 0, you will test your location with exactly the altitude of the peak to spot. 
# If -100, you will test if you can see from your location the last 100 meters of the summit.
res = 0.5 # Resolution in kilometers. Defaults to 10.

# Generate grid of locations
grid_locations = generate_locations_grid(top_left_corner, bottom_right_corner, res)

# Determine the visibility of the summit from each position
grid_locations_processed = summit_is_visible_multi_locations_offline(grid_locations, location_summit, offset_view, offset_summit)

# Save data to csv file
grid_locations_processed.to_csv("data_multi_locations_offline.csv", index=False)

# Correct errors and reformat view_possible data
view_possible_corrected = []
for i, view in enumerate(grid_locations_processed["view_possible"]):
    if view == "error\r\n" or view == "error" or view == "error\n":
        view_possible_corrected.append(summit_is_visible_fast_offline(location_point=[grid_locations_processed["latitude"][i], grid_locations_processed["longitude"][i]], location_summit=location_summit, offset_view=offset_view, offset_summit=offset_summit))
    else:
        view_possible_corrected.append(view.replace("\r", "").replace("\n", ""))

grid_locations_processed["view_possible"] = view_possible_corrected

# Save data to csv file
grid_locations_processed.to_csv("data_multi_locations_offline.csv", index=False)