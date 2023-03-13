import pandas as pd
from plotly.express import scatter_mapbox

# Import a file
grid_locations = pd.read_csv("data/results/summits_results.csv")

# Show your summit
your_summit = {'name': "MontBlanc", 'latitude':[45.8327057] ,'longitude':[6.8651706], 'view_possible': "Mont Blanc 4808m", 'elevation': "4808"}
summit_to_spot = pd.DataFrame(your_summit)

"""
For locations
"""
# grid_locations = grid_locations[grid_locations['view_possible'] == True]
# grid_locations = pd.concat([grid_locations, summit_to_spot])
# fig = scatter_mapbox(grid_locations, lat="latitude", lon="longitude", color="view_possible", zoom=5, mapbox_style="open-street-map",
#                       color_discrete_sequence=["darkgreen", "blue"])

"""
For summits
"""
grid_locations = grid_locations.sort_values(by="view_possible", ascending=True)
grid_locations = pd.concat([grid_locations, summit_to_spot])
fig = scatter_mapbox(grid_locations, lat="latitude", lon="longitude", zoom=5, mapbox_style="open-street-map", 
                    hover_name="name", text="elevation", color="view_possible" , color_discrete_sequence=["red", "darkgreen", "blue"])

fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
# fig.show()
fig.write_html("data/maps/from_summits_Mont_Blanc.html")