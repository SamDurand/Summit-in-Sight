def summit_is_visible_fast_online(location_point, location_summit, offset_view = 10, offset_summit = -100, samples=False):
    
    """This function is a simplified version of summit_is_visible_online. It allows to determine the visibility of a summit from a single location.
    Instead of plotting all the different altimetric profiles, this function just focuses on the different peaks that could hide the view.
    This version use the online api.opentopodata.org (https://www.opentopodata.org/). It can be used without hosting data locally. 
   
    Dataset: srtm90m (https://wiki.openstreetmap.org/wiki/SRTM)

    Args:
        - location_point (list): coordinates in decimal degrees (latitude, longitude) of a location. Example: [46.206939 , 6.147794]

        - location_summit (list): coordinates in decimal degrees (latitude, longitude) of a summit. Example: [45.832542 , 6.864717]

        - offset_view (int, optional): Your elevation from the ground at your location_point (can be either positive or 0). Defaults to 10.

        - offset_summit (int, optional): How much of the summit you want to see. If 0, you will test your location with exactly the altitude of the summit to spot. 
          If -100, you will test if you can see from your location the last 100 meters of the summit.. Defaults to -100.

        - samples (bool or int, optional): Number of equally-spaced samples to query along the path defined by location_point and location_summit. Defaults to False. 
          If False, the default number of samples is equal to the geodesic distance between location_point and location_summit.

    Returns:
        - view_possible (bool): Return True if the summit is visible from your location.
        
    """
    
    earth_radius, offset_view, offset_summit, geodesic_distance, geodesic_earth_perimeter = EARTH_RADIUS, offset_view/1000,  offset_summit/1000, GeodesicDistance(location_point, location_summit).km, (2*np.pi*EARTH_RADIUS)

    if not samples:
        samples = (round(geodesic_distance) if round(geodesic_distance) <= 100 else 100)
        samples = (20 if round(geodesic_distance) <= 20 else samples)

    # Compute angle between the 2 locations and create a vector with sampling split of the total angle 
    angle_total_rad = np.deg2rad((geodesic_distance/geodesic_earth_perimeter)*360) 
    angle_from_origin = np.flip(np.linspace(np.pi/2 - angle_total_rad/2, np.pi/2 + angle_total_rad/2 , samples)) # + pi/2 pour centrer le tracé

    latitude = np.linspace(location_point[0], location_summit[0], samples)
    longitude = np.linspace(location_point[1], location_summit[1], samples)

    url = "https://api.opentopodata.org/v1/srtm90m"
    json = {"locations": "".join([str(latitude[i]) + "," + str(longitude[i]) + '|' for i in range(samples)]).removesuffix("|"),
            "interpolation": "bilear",}
    response = requests.post(url, json)
    data = response.json()
    
    elevation_from_earth_center = np.add( np.array([data['results'][i]["elevation"] if data['results'][i]["elevation"] != None else 0 for i in range(samples)], dtype=int)/1000 , earth_radius ) # Elevation_from_earth_center in km
            