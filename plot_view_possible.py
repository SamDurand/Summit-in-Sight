import pandas as pd
from plotly.express import scatter_mapbox

# Import a file
grid_locations = pd.read_csv("data/results/global_results.csv")


"""
For locations
"""
# Keep only locations when view_possible = True
grid_locations = grid_locations[grid_locations['view_possible'] == True]
fig = scatter_mapbox(grid_locations, lat="latitude", lon="longitude", zoom=5, mapbox_style="stamen-terrain",
                      color_discrete_sequence=["mediumspringgreen"])

"""
For summits
"""
# # Plot summits
# grid_locations = grid_locations.sort_values(by="view_possible", ascending=True)

# fig = scatter_mapbox(grid_locations, lat="latitude", lon="longitude", zoom=5, mapbox_style="stamen-terrain", 
#                     hover_name="name", text="elevation", color="view_possible" , color_discrete_sequence=["red", "mediumspringgreen"])


fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
fig.show()
# fig.write_html("data/maps/view_possible_Mont_Blanc.html")