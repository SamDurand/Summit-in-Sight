from summit_lib import generate_locations_grid, summit_is_visible_multi_locations

# res en km
top_left_corner, bottom_right_corner, location_summit = [47 , 5], [45 , 8], [45.832542 , 6.864717]
offset_view = 2
offset_summit = -50
res = 0.5

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

grid_locations = generate_locations_grid(top_left_corner, bottom_right_corner, res)
grid_locations_isvisible = summit_is_visible_multi_locations(grid_locations, location_summit, offset_view, offset_summit, samples=1000)

# print("Correcting potential errors")
# for i in tqdm(range(len(grid_locations_isvisible["view_possible"]))):
#     if grid_locations_isvisible["view_possible"][i] == "error":
#         grid_locations_isvisible["view_possible"][i] = summit_is_visible_fast_online([grid_locations_isvisible["lat_grid"][i], grid_locations_isvisible["lon_grid"][i]], 
#                                                                                       location_summit, offset_view, offset_summit)
# plot_locations_map(grid_locations_isvisible.sort_values(by=["view_possible"], ascending=False), color="view_possible")