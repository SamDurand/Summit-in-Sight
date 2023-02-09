from summit_lib import summit_is_visible_online

location_point = [45.7023, 4.823] # Your location

# Try with these locations:
# Pont du Mont Blanc, Geneva, Switzerland [46.206939 , 6.147794]
# Basilica of Notre-Dame de Fourvière, Lyon, France [45.7023, 4.823]
# Montpellier, France [43.5485, 3.8782]
# Mont Cook, New-Zealand (antipode of France) [-43.595, 170.141944]

location_summit = [45.832542 , 6.864717] # The summit to spot

# Mont Blanc, 4810m, France [45.832542 , 6.864717]


offset_view = 100 # Your elevation from the ground at your location_point (can be either positive or 0)

offset_summit = -100 # How much of the summit you want to see. For example, if 0, you will test your location with exactly the altitude of the peak to spot. 
# If -100, you will test if you can see from your location the last 100 meters of the summit.

view_possible, data = summit_is_visible_online(location_point, location_summit, plot=True, offset_view=offset_view, offset_summit=offset_summit)