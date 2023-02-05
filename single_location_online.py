from summit_lib import summit_is_visible_online

location_point = [46.206939 , 6.147794] # Your location

# Pont du Mont Blanc [46.206939 , 6.147794]
# Lyon Fourviere [45.7023, 4.823]
# Montpellier [43.5485, 3.8782]
# Everest [27.9495, 86.9252]

location_summit = [45.832542 , 6.864717] # The summit to spot

offset_view = 2 # Your elevation from the ground of your location_point (can be either positive or 0)

offset_summit = -50 # How much of the summit you want to see. If 0, you will test your location with exactly the altitude of the summit to spot. 
# If -100, you will test if you can see from your location the last 100 meters of the summit.

view_possible, _ = summit_is_visible_online(location_point, location_summit, plot=True, offset_view=offset_view, offset_summit=offset_summit)