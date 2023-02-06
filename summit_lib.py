import numpy as np
from geopy.distance import GeodesicDistance, EARTH_RADIUS
import requests
import matplotlib.pyplot as plt
import pandas as pd
from scipy.signal import find_peaks
from plotly.express import scatter_mapbox
from tqdm import tqdm
from geopy.geocoders import Nominatim


def trigo_to_complex(modulus_z, arg_z):

    """Compute a complex number from its polar/trigonometric notation (= from argument and modulus)
    
    -> Convertion from polar coordinates to cartesian coordinates.

    Args:
        modulus_z (float): modulus of a complex number Z
        arg_z (float): argument of a complex number Z

    Returns:
        Z (complex): Complex number composed of real and imaginary parts
    """

    # Create a pure imaginary number 
    real_part = 0
    imag_part = 1
    c = complex(real_part,imag_part) # c = 0 + i

    # Compute Z
    Z = modulus_z * ( np.cos(arg_z) + c * np.sin(arg_z) )

    return Z

def summit_is_visible_online(location_point, location_summit, plot = False, offset_view = 10, offset_summit = -100, samples=False):

    """Determine the visibility of a summit from a single location. Optionaly plot the full geodesic profile.

    Method: api.opentopodata.org (https://www.opentopodata.org/)
    Dataset: srtm30m (https://wiki.openstreetmap.org/wiki/SRTM)

    Args:
        location_point (list): coordinates in decimal degrees (latitude, longitude) of a location. Example: [46.206939 , 6.147794]

        location_summit (list): coordinates in decimal degrees (latitude, longitude) of a summit. Example: [45.832542 , 6.864717]

        plot (bool, optional): if True, the full geodesic profile is plotted. Convenient to understand how the function actually works. Defaults to False.

        offset_view (int, optional): Your elevation from the ground at your location_point (can be either positive or 0). Defaults to 10.

        offset_summit (int, optional): How much of the summit you want to see. If 0, you will test your location with exactly the altitude of the summit to spot. 
        If -100, you will test if you can see from your location the last 100 meters of the summit.. Defaults to -100.

        samples (bool or int, optional): Number of equally-spaced samples to query along the path defined by location_point and location_summit. Defaults to False. 
        If False, the default number of samples is equal to the geodesic distance between location_point and location_summit.

    Returns:
        view_possible (bool): Return True if the summit is visible from your location.
        data (pandas DataFrame): table gathering latitude, longitude, elevation, elevation_from_earth_center, angle_from_origin, Z, real_Z, imag_Z, view_possible for all samples of the path       
    """

    earth_radius = EARTH_RADIUS
    offset_view, offset_summit, geodesic_distance, geodesic_earth_perimeter = offset_view/1000,  offset_summit/1000, GeodesicDistance(location_point, location_summit).km, (2*np.pi*earth_radius)

    if not samples:
        samples = (round(geodesic_distance) if round(geodesic_distance) <= 100 and round(geodesic_distance) >= 20 else 100)

    # Compute angle between the 2 locations and create a vector with sampling split of the total angle 
    angle_total_rad = np.deg2rad((geodesic_distance/geodesic_earth_perimeter)*360) 
    angle_from_origin = np.flip(np.linspace(np.pi/2 - angle_total_rad/2, np.pi/2 + angle_total_rad/2 , samples)) # + pi/2 to center plotting vertically

    # Query elevation from online api
    latitude = np.linspace(location_point[0], location_summit[0], samples)
    longitude = np.linspace(location_point[1], location_summit[1], samples)

    url = "https://api.opentopodata.org/v1/srtm30m"
    json = {"locations": "".join([str(latitude[i]) + "," + str(longitude[i]) + '|' for i in range(samples)]).removesuffix("|"),
            "interpolation": "cubic"}
    response = requests.post(url, json)
    data = response.json()

    elevation_profile, lat, long, elevation_from_earth_center = np.array([data['results'][i]["elevation"] if data['results'][i]["elevation"] != None else 0 for i in range(samples)], dtype=int), \
                                                                np.array([data['results'][i]["location"]["lat"] for i in range(samples)]), \
                                                                np.array([data['results'][i]["location"]["lng"] for i in range(samples)]), \
                                                                np.add(np.array([data['results'][i]["elevation"] if data['results'][i]["elevation"] != None else 0 for i in range(samples)], dtype=int)/1000, earth_radius) # Elevation_from_earth_center in km
                                                                
    # Generate complex coordinates of each point (relief). We have arg(Z) = angle from point origin and modulus of Z = elevation from earth center
    Z = np.array([trigo_to_complex(elevation_from_earth_center[i], angle_from_origin[i]) for i in range(samples)])

    real_Z = Z.real #X coordinate
    imag_Z = Z.imag #Y coordinate

    # Line of vision
    start_point, stop_point = trigo_to_complex(elevation_from_earth_center[0] + offset_view, angle_from_origin[0]), \
                            trigo_to_complex(elevation_from_earth_center[-1] + offset_summit, angle_from_origin[-1])
                            
    line_of_vision = np.linspace(start_point.imag, stop_point.imag, samples)

    # View is possible?
    view_possible_list = np.array([True if line_of_vision[i] > imag_Z[i] else False for i in range(samples)])
    view_possible = np.all([view_possible_list[i] for i in range(round(samples*0.95))]) # The for * 0.95 is not to take in consideration the collision of the line of vision with the target summit itself

    # Create a pandas df to gather data
    data = pd.DataFrame(columns=["latitude", "longitude", "elevation", "elevation_from_earth_center", "angle_from_origin", "Z", "real_Z", "imag_Z", "view_possible"],
                        data=np.column_stack([lat, long, elevation_profile, elevation_from_earth_center, angle_from_origin, Z, real_Z, imag_Z, view_possible_list]))
    
    # Get locations names
    geoLoc = Nominatim(user_agent="GetLoc")
    try:
        locname_point = geoLoc.reverse((location_point[0], location_point[1])).address
        print("Location point: " + locname_point)
    except:
        print("Location point: " + str(latitude[0]) + " " + str(longitude[0]))

    try:
        locname_summit = geoLoc.reverse((location_summit[0], location_summit[1])).address
        print("Location summit: " + locname_summit)
    except:
        print("Location summit: " + str(latitude[0]) + " " + str(longitude[0]))

    if view_possible:
        print("Summit in sight!")
    else:
        print("Summit not in Sight...")

    if plot == True:

        # Create a plot when the line of vision is below the relief level to show relief masking
        masked_view = np.array([np.nan if line_of_vision[i] > imag_Z[i] else line_of_vision[i] for i in range(samples)])
        
        # Plot the relief data
        fig, axs = plt.subplots(3)
        
        message = ("Summit is visible!" if view_possible else "Summit is not visible ..")
        fontdict = ({'family':'serif','color':'green','weight': 'bold','size':15} if view_possible else {'family':'serif','color':'red','weight': 'bold','size':15})

        fig.suptitle("Altimetric profiles (horizontal and geodesic)")
        fig.text(0.5, 0.88, (message+"\n"), fontdict, ha='center', va='center')

        axs[0].plot(np.linspace(0, geodesic_distance, samples), elevation_profile, linestyle="solid", color="k")
        axs[1].plot(real_Z, imag_Z, linestyle="solid", color="k")
        axs[1].plot(real_Z, line_of_vision, linestyle="dashdot", color="g")
        axs[1].plot(real_Z, masked_view, linestyle="solid", color="r")
        axs[2].plot(real_Z, imag_Z, linestyle="solid", color="k")
        axs[2].plot(real_Z, line_of_vision, linestyle="dashdot", color="g")
        axs[2].plot(real_Z, masked_view, linestyle="solid", color="r")
        
        # Fill in red masked parts
        for i in range(len(imag_Z)):
            if line_of_vision[i] < imag_Z[i]:
                axs[1].fill_between(real_Z, imag_Z, masked_view, alpha=.5, linewidth=0, fc='red')
                axs[2].fill_between(real_Z, imag_Z, masked_view, alpha=.5, linewidth=0, fc='red')
        axs[0].set(ylabel='Elevation (m)')
        axs[1].axis('equal')
        axs[1].set(ylabel='Earth radius (km)')
        axs[2].set(xlabel='Geodesic distance (km)', ylabel='//')
        plt.show()

    return view_possible, data

def summit_is_visible_fast_online(location_point, location_summit, offset_view = 10, offset_summit = -100, samples=False):
    """Return if a summit is visible or not.
    Method: api.opentopodata.org
    Dataset: srtm90m

    Args:
        location_point (_type_): _description_
        location_summit (_type_): _description_
        offset_view (int, optional): _description_. Defaults to 10.
        offset_summit (int, optional): _description_. Defaults to -100.
        samples (bool, optional): _description_. Defaults to False.

    Returns:
        _type_: _description_
    """
    earth_radius = EARTH_RADIUS
    offset_view, offset_summit, geodesic_distance, geodesic_earth_perimeter = offset_view/1000,  offset_summit/1000, GeodesicDistance(location_point, location_summit).km, (2*np.pi*earth_radius)
    
    if not samples:
        samples = (round(geodesic_distance) if round(geodesic_distance) <= 100 and round(geodesic_distance) >= 20 else 100)
        
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
    
    elevation_profile, lat, long, elevation_from_earth_center = np.array([data['results'][i]["elevation"] if data['results'][i]["elevation"] != None else 0 for i in range(samples)], dtype=int), \
                                                                np.array([data['results'][i]["location"]["lat"] for i in range(samples)]), \
                                                                np.array([data['results'][i]["location"]["lng"] for i in range(samples)]), \
                                                                np.add(np.array([data['results'][i]["elevation"] if data['results'][i]["elevation"] != None else 0 for i in range(samples)], dtype=int)/1000, earth_radius) # Elevation_from_earth_center in km
                        
    # Find peaks
    peaks = np.array(find_peaks(elevation_from_earth_center, height=True), dtype=object)
    peaks_index = peaks[0]
    peaks_heights = peaks[1]["peak_heights"]

    peaks_complex = trigo_to_complex(peaks_heights, angle_from_origin[peaks_index])
    peaks_index_complex = peaks_complex.real
    peak_heights_complex = peaks_complex.imag

    # Line of vision
    start_point, stop_point = trigo_to_complex(elevation_from_earth_center[0] + offset_view, angle_from_origin[0]), \
                            trigo_to_complex(elevation_from_earth_center[-1] + offset_summit, angle_from_origin[-1])

    line_of_vision = np.linspace(start_point.imag, stop_point.imag, samples)

    view_possible = np.all([True if peak_heights_complex[i]<line_of_vision[peaks_index][i] else False for i in range(peaks_index.size)])
    
    return view_possible

def summit_is_visible_fast_offline(location_point, location_summit, offset_view = 10, offset_summit = -100, samples=False):
    """Return if a summit is visible or not.
    Method: local
    Dataset: srtm90m

    Args:
        location_point (_type_): _description_
        location_summit (_type_): _description_
        offset_view (int, optional): _description_. Defaults to 10.
        offset_summit (int, optional): _description_. Defaults to -100.
        samples (bool, optional): _description_. Defaults to False.

    Returns:
        _type_: _description_
    """
    earth_radius = EARTH_RADIUS
    offset_view, offset_summit, geodesic_distance, geodesic_earth_perimeter = offset_view/1000,  offset_summit/1000, GeodesicDistance(location_point, location_summit).km, (2*np.pi*earth_radius)

    if not samples:
        samples = (round(geodesic_distance) if round(geodesic_distance) <= 200 else 200)
        samples = (100 if round(geodesic_distance) < 20 else samples) 

    # Compute angle between the 2 locations and create a vector with sampling split of the total angle 
    angle_total_rad = np.deg2rad((geodesic_distance/geodesic_earth_perimeter)*360) 
    angle_from_origin = np.flip(np.linspace(np.pi/2 - angle_total_rad/2, np.pi/2 + angle_total_rad/2 , samples)) # + pi/2 pour centrer le tracé

    latitude = np.linspace(location_point[0], location_summit[0], samples)
    longitude = np.linspace(location_point[1], location_summit[1], samples)

    url = "http://localhost:5000/v1/srtm90m"
    json = {"locations": "".join([str(latitude[i]) + "," + str(longitude[i]) + '|' for i in range(samples)]).removesuffix("|"),
            "interpolation": "bilinear",}
    response = requests.post(url, json)
    data = response.json()

    elevation_profile, lat, long, elevation_from_earth_center = np.array([data['results'][i]["elevation"] if data['results'][i]["elevation"] != None else 0 for i in range(samples)], dtype=int), \
                                                                np.array([data['results'][i]["location"]["lat"] for i in range(samples)]), \
                                                                np.array([data['results'][i]["location"]["lng"] for i in range(samples)]), \
                                                                np.add(np.array([data['results'][i]["elevation"] if data['results'][i]["elevation"] != None else 0 for i in range(samples)], dtype=int)/1000, earth_radius) # Elevation_from_earth_center in km
                        
    # Find peaks
    peaks = np.array(find_peaks(elevation_from_earth_center, height=True), dtype=object)
    peaks_index = peaks[0]
    peaks_heights = peaks[1]["peak_heights"]

    peaks_complex = trigo_to_complex(peaks_heights, angle_from_origin[peaks_index])
    peaks_index_complex = peaks_complex.real
    peak_heights_complex = peaks_complex.imag

    # Line of vision
    start_point, stop_point = trigo_to_complex(elevation_from_earth_center[0] + offset_view, angle_from_origin[0]), \
                            trigo_to_complex(elevation_from_earth_center[-1] + offset_summit, angle_from_origin[-1])

    line_of_vision = np.linspace(start_point.imag, stop_point.imag, samples)

    view_possible = np.all([True if peak_heights_complex[i]<line_of_vision[peaks_index][i] else False for i in range(peaks_index.size)])
    
    return view_possible

def summit_is_visible_multi_locations(grid_locations, location_summit, offset_view, offset_summit):
   
    locations = [[grid_locations["lat_grid"][i], grid_locations["lon_grid"][i]] for i in grid_locations.index]

    with open("data_temp.txt", "w") as f:
        f.write("view_possible \n")
    f.close()
    
    for i in tqdm(grid_locations.index):
       
        with open("data_temp.txt", "a") as f:
            f.write(str(summit_is_visible_fast_offline(location_point=locations[i], location_summit=location_summit, offset_view=offset_view, offset_summit=offset_summit)) + " \n")
        f.close()
        

    grid_locations_processed = grid_locations
    grid_locations_processed["view_possible"] = pd.read_csv("data_temp.txt")
    
    return grid_locations_processed
    
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
def generate_locations_grid(top_left_corner, bottom_right_corner, res = 10): #resolution in km
    """Generate a grid of multiples locations

    Args:
        top_left_corner (_type_): _description_
        bottom_right_corner (_type_): _description_
        res (int, optional): _description_. Defaults to 10.

    Returns:
        _type_: _description_
    """
    vert = (GeodesicDistance([top_left_corner[0], top_left_corner[1]], [bottom_right_corner[0], top_left_corner[1]]).km)/res
    hori = (GeodesicDistance([top_left_corner[0], top_left_corner[1]], [top_left_corner[0], bottom_right_corner[1]]).km)/res
    grid_lat = np.linspace(top_left_corner[0], bottom_right_corner[0], int(vert))
    grid_lon = np.linspace(top_left_corner[1], bottom_right_corner[1], int(hori))
    print("Number of locations: " + str(int(vert)*int(hori)))

    lat_grid = []
    lon_grid = []
    for lat in grid_lat:
        for lon in grid_lon:
            lat_grid.append(lat)
            lon_grid.append(lon)

    grid_locations = pd.DataFrame()
    grid_locations["lat_grid"], grid_locations["lon_grid"] = lat_grid, lon_grid
    
    return grid_locations

def plot_locations_map(grid_locations, color=False):
    if not color:
        fig = scatter_mapbox(grid_locations, lat="lat_grid", lon="lon_grid", zoom=6, mapbox_style="open-street-map")
        fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    else:
        fig = scatter_mapbox(grid_locations, lat="lat_grid", lon="lon_grid", zoom=6, color=color, mapbox_style="open-street-map")                
        fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    
    fig.show()
