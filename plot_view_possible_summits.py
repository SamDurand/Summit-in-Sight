import pandas as pd
from plotly.express import scatter_mapbox

# Import a file
grid_locations = pd.read_csv("data/summits_list.csv")

# PLot locations
fig = scatter_mapbox(grid_locations, lat="latitude", lon="longitude", zoom=5, mapbox_style="stamen-terrain")
fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
fig.show()
# fig.write_html("data/results/Grid_NW_Alps_res=0.5.html")