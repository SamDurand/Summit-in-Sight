import geopy.distance
import requests
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import cmath
import matplotlib.pyplot as plt
import plotly.express as px
from tqdm import tqdm
from scipy.signal import find_peaks
import time
from requests.structures import CaseInsensitiveDict

earth_radius = geopy.distance.EARTH_RADIUS
geodesic_earth_perimeter = 2 * np.pi * geopy.distance.EARTH_RADIUS

#Compute a complex number from its trigonometric notation (from argument and modulus)
def trigo_to_complex(modulus, arg_z):

    real = 0
    imag = 1
    c = complex(real,imag) # c = 0 + i

    Z = modulus * ( np.cos(arg_z) + c * np.sin(arg_z) )

    return Z

def summit_is_visible_multi_locations(grid_locations, location_summit, offset_view, offset_summit):
    view_possible_grid = []

    for i in tqdm(range(len(grid_locations["lat_grid"]))):
        
        try:
            location_1 = [grid_locations["lat_grid"][i], grid_locations["lon_grid"][i]]
            view_possible = summit_is_visible_peaks_fast(location_point=location_1, location_summit=location_summit, offset_view=offset_view, offset_summit=offset_summit)
            view_possible_grid.append(view_possible)
        except:
            view_possible_grid.append("error")

    grid_locations["view_possible"] = view_possible_grid

    return grid_locations

def summit_is_visible_online_api(location_point, location_summit, plot = False, offset_view = 10, offset_summit = -100, samples=False):

    # Empty lists
    elevation_profile = []
    lat = []
    long = []
    elevation_from_earth_center = []
    Z = []
    masked_view = []
    view_possible = []

    # Convert offsets in km
    offset_view /= 1000
    offset_summit /= 1000

    # Get constant values
    geodesic_distance = geopy.distance.GeodesicDistance(location_point, location_summit).km
    if samples==False:
        samples = geodesic_distance*2
    else: samples=samples
    
    # Limit samples to 1500
    if samples > 1500:
        samples = 1500
    else:
        samples = round(samples)
    
    # Compute angle between the 2 locations and create a vector with sampling split of the total angle 
    angle_total_rad = np.deg2rad((geodesic_distance/geodesic_earth_perimeter)*360)
    angle_from_origin = np.flip( np.linspace(np.pi/2 - angle_total_rad/2, np.pi/2 + angle_total_rad/2 , samples) ) # + pi/2 pour centrer le tracé
    
    latitude = np.linspace(location_point[0], location_summit[0], samples)
    longitude = np.linspace(location_point[1], location_summit[1], samples)

    try:
        # Send request and saving the response as response object
        url = "https://api.open-elevation.com/api/v1/lookup"

        headers = CaseInsensitiveDict()
        headers["Content-Type"] = "application/json"

        data = '{"locations":['
        for i in range(samples):
            data += '{"latitude": ' + str(latitude[i]) + "," + '"longitude": ' + str(longitude[i]) + "},"

        data = data.removesuffix(",") + ']}'

        resp = requests.post(url, headers=headers, data=data)
        data = resp.json()
        
        # Extract data from request
        for i in range(len(data["results"])):
            elevation_profile.append(data['results'][i]["elevation"])
            lat.append(data['results'][i]["latitude"])
            long.append(data['results'][i]["longitude"])
            try:
                elevation_from_earth_center.append(earth_radius + elevation_profile[i]/1000) # Elevation_from_earth_center in km
            except:
                elevation_from_earth_center.append(earth_radius)
            
            # Avoid abberant values
            if elevation_profile[i] == -99999:
                elevation_profile[i] = np.nan
                elevation_from_earth_center[i] = np.nan

        # Create a pandas df
        data = pd.DataFrame()

        data["lat"] = lat
        data["lon"] = long
        data["elevation"] = elevation_profile
        data["elevation_from_earth_center"] = elevation_from_earth_center # = modulus of Z
        data["angle_from_origin"] = angle_from_origin # = arg (Z)

        # Fill gaps of nan values with a linear interpolation
        data["elevation"] = data["elevation"].interpolate(method="linear", limit=1000)
        data["elevation_from_earth_center"] = data["elevation_from_earth_center"].interpolate(method="linear")

        elevation_from_earth_center = np.array(data["elevation_from_earth_center"])

        # Generate complex coordinates of each point. We have arg(Z) = angle depuis l'origine du point and module de Z = elevation from earth center
        for i in range(len(elevation_from_earth_center)):
            Z.append(trigo_to_complex(elevation_from_earth_center[i], angle_from_origin[i]))

        start_point = trigo_to_complex(elevation_from_earth_center[0] + offset_view, angle_from_origin[0])
        stop_point = trigo_to_complex(elevation_from_earth_center[-1] + offset_summit, angle_from_origin[-1])

        data["Z"] = Z
        real_Z = [ele.real for ele in data["Z"]] #X coordinate
        imag_Z = [ele.imag for ele in data["Z"]] #Y coordinate

        # Line of vision
        line_of_vision = np.linspace(start_point.imag, stop_point.imag, samples)
        line_of_vision_index = np.linspace(start_point.real, stop_point.real, samples)
        
        # View is possible ? The for * 0.95 is not to take in consideration the collision of the line of vision with the target summit itself
        for i in range( round( len(imag_Z) * 0.95 )):
                if line_of_vision[i] > imag_Z[i]:
                    view_possible.append(True)
                else: 
                    view_possible.append(False)

        if view_possible.count(False) == 0:
                view_possible = True
        else:
            view_possible = False

        
        if plot == True:
            # Create a plotting when the line of vision is below the relief level
            for i in range( len(imag_Z) ):
                if line_of_vision[i] > imag_Z[i]:
                    masked_view.append(np.nan)
                else: 
                    masked_view.append(line_of_vision[i])


            # Plot the complex numbers
            fig, axs = plt.subplots(3)
            
            if view_possible:
                message = "Summit is visible!"
                fontdict = font = {'family': 'serif',
                                    'color':  'green',
                                    'weight': 'bold',
                                    'size': 20
                                    }
            else:
                message = "Summit is not visible .."
                fontdict = font = {'family': 'serif',
                                    'color':  'red',
                                    'weight': 'bold',
                                    'size': 20
                                    }

            fig.suptitle("Altimetric profiles (horizontal and geodesic)")

            fig.text(0.25, 1, (message+"\n"), fontdict)
            
            axs[0].plot(np.linspace(0, geodesic_distance, samples), data["elevation"], linestyle="solid", color="k")

            axs[1].plot(real_Z, imag_Z, linestyle="solid", color="k")
            axs[1].plot(real_Z, line_of_vision, linestyle="dashdot", color="g")
            axs[1].plot(real_Z, masked_view, linestyle="solid", color="r")
        
            axs[2].plot(real_Z, imag_Z, linestyle="solid", color="k")
            axs[2].plot(real_Z, line_of_vision, linestyle="dashdot", color="g")
            axs[2].plot(real_Z, masked_view, linestyle="solid", color="r")

            # Fill in red
            for i in range(len(imag_Z)):
                if line_of_vision[i] < imag_Z[i]:
                    axs[1].fill_between(real_Z, imag_Z, masked_view, alpha=.5, linewidth=0, fc='red')
                    axs[2].fill_between(real_Z, imag_Z, masked_view, alpha=.5, linewidth=0, fc='red')

            axs[0].set(ylabel='Elevation (m)')

            axs[1].axis('equal')
            axs[1].set(ylabel='Earth radius (km)')

            axs[2].set(xlabel='Geodesic distance (km)', ylabel='//')

            plt.show()
        
    except:
        data = "error"
        real_Z = "error"
        imag_Z = "error"
        line_of_vision = "error"
        view_possible = "error"
    

    return data, view_possible

def generate_locations_grid(top_left_corner, bottom_right_corner, res = 10): #resolution in km

    vert = (geopy.distance.GeodesicDistance([top_left_corner[0], top_left_corner[1]], [bottom_right_corner[0], top_left_corner[1]]).km)/res
    hori = (geopy.distance.GeodesicDistance([top_left_corner[0], top_left_corner[1]], [top_left_corner[0], bottom_right_corner[1]]).km)/res

    grid_lat = np.linspace(top_left_corner[0], bottom_right_corner[0], int(vert))
    grid_lon = np.linspace(top_left_corner[1], bottom_right_corner[1], int(hori))

    print("Number of samples: " + str(int(vert)*int(hori)))

    lat_grid = []
    lon_grid = []

    for i in range(len(grid_lat)):
        for j in range(len(grid_lon)):
            lat_grid.append(grid_lat[i])
            lon_grid.append(grid_lon[j])

    grid_locations = pd.DataFrame()

    grid_locations["lat_grid"] = lat_grid
    grid_locations["lon_grid"] = lon_grid

    return grid_locations

def plot_locations_map(grid_locations, color=False):
    
    try:
        if not True in grid_locations["view_possible"].unique():
            print("No Possible views for your summit!")
        else:
            if color:
                fig = px.scatter_mapbox(grid_locations, lat="lat_grid", lon="lon_grid", zoom=6, height=300, color=color, mapbox_style="open-street-map")
                fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
            else:
                fig = px.scatter_mapbox(grid_locations, lat="lat_grid", lon="lon_grid", zoom=6, height=300, mapbox_style="open-street-map")                
                fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

            fig.show()
    except:
        if color:
                fig = px.scatter_mapbox(grid_locations, lat="lat_grid", lon="lon_grid", zoom=6, height=300, color=color, mapbox_style="open-street-map")
                fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
        else:
            fig = px.scatter_mapbox(grid_locations, lat="lat_grid", lon="lon_grid", zoom=6, height=300, mapbox_style="open-street-map")                
            fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

        fig.show()
        
def summit_is_visible_offline_api(location_point, location_summit, plot = False, offset_view = 10, offset_summit = -100, samples=False):

    # Empty lists
    elevation_profile = []
    lat = []
    long = []
    elevation_from_earth_center = []
    Z = []
    masked_view = []
    view_possible = []

    # Convert offsets in km
    offset_view /= 1000
    offset_summit /= 1000

    # Get constant values
    geodesic_distance = geopy.distance.GeodesicDistance(location_point, location_summit).km
    if samples==False:
        samples = geodesic_distance*2
    else: samples=samples
    
    # Limit samples to 5000
    if samples > 1500:
        samples = 1500
    else:
        samples = round(samples)

    # Compute angle between the 2 locations and create a vector with sampling split of the total angle 
    angle_total_rad = np.deg2rad((geodesic_distance/geodesic_earth_perimeter)*360)
    angle_from_origin = np.flip( np.linspace(np.pi/2 - angle_total_rad/2, np.pi/2 + angle_total_rad/2 , samples) ) # + pi/2 pour centrer le tracé
    
    latitude = np.linspace(location_point[0], location_summit[0], samples)
    longitude = np.linspace(location_point[1], location_summit[1], samples)

    try:
        locations_json = []
        for i in range(samples):
            locations_json.append(str(latitude[i]) + "," + str(longitude[i]) + '|')

        locations_json = "".join(locations_json).removesuffix("|")

        json = {"locations": locations_json,
                "interpolation": "cubic",}

        # Send request and saving the response as response object
        url = "http://localhost:5000/v1/eudem25m"

        resp = requests.post(url, json)

        data = resp.json()
    
        # Extract data from request
        for i in range(len(data["results"])):
            elevation_profile.append(data['results'][i]["elevation"])
            lat.append(data['results'][i]["location"]["lat"])
            long.append(data['results'][i]["location"]["lng"])
            elevation_from_earth_center.append(earth_radius + elevation_profile[i]/1000) # Elevation_from_earth_center in km

            # Avoid abberant values
            if elevation_profile[i] == -99999:
                elevation_profile[i] = np.nan
                elevation_from_earth_center[i] = np.nan

        # Create a pandas df
        data = pd.DataFrame()

        data["lat"] = lat
        data["lon"] = long
        data["elevation"] = elevation_profile
        data["elevation_from_earth_center"] = elevation_from_earth_center # = modulus of Z
        data["angle_from_origin"] = angle_from_origin # = arg (Z)

        # Fill gaps of nan values with a linear interpolation
        data["elevation"] = data["elevation"].interpolate(method="linear", limit=1000)
        data["elevation_from_earth_center"] = data["elevation_from_earth_center"].interpolate(method="linear")

        elevation_from_earth_center = np.array(data["elevation_from_earth_center"])

        # Generate complex coordinates of each point. We have arg(Z) = angle depuis l'origine du point and module de Z = elevation from earth center
        for i in range(len(elevation_from_earth_center)):
            Z.append(trigo_to_complex(elevation_from_earth_center[i], angle_from_origin[i]))

        start_point = trigo_to_complex(elevation_from_earth_center[0] + offset_view, angle_from_origin[0])
        stop_point = trigo_to_complex(elevation_from_earth_center[-1] + offset_summit, angle_from_origin[-1])

        data["Z"] = Z
        real_Z = [ele.real for ele in data["Z"]] #X coordinate
        imag_Z = [ele.imag for ele in data["Z"]] #Y coordinate

        # Line of vision
        line_of_vision = np.linspace(start_point.imag, stop_point.imag, samples)
        line_of_vision_index = np.linspace(start_point.real, stop_point.real, samples)
        
        # View is possible ? The for * 0.95 is not to take in consideration the collision of the line of vision with the target summit itself
        for i in range( round( len(imag_Z) * 0.95 )):
                if line_of_vision[i] > imag_Z[i]:
                    view_possible.append(True)
                else: 
                    view_possible.append(False)

        if view_possible.count(False) == 0:
            view_possible = True
        else:
            view_possible = False

        
        if plot == True:
            # Create a plotting when the line of vision is below the relief level
            for i in range( len(imag_Z) ):
                if line_of_vision[i] > imag_Z[i]:
                    masked_view.append(np.nan)
                else: 
                    masked_view.append(line_of_vision[i])

            # Plot the complex numbers
            fig, axs = plt.subplots(3)
            
            if view_possible:
                message = "Summit is visible!"
                fontdict = font = {'family': 'serif',
                                    'color':  'green',
                                    'weight': 'bold',
                                    'size': 20
                                    }
            else:
                message = "Summit is not visible .."
                fontdict = font = {'family': 'serif',
                                    'color':  'red',
                                    'weight': 'bold',
                                    'size': 20
                                    }

            fig.suptitle("Altimetric profiles (horizontal and geodesic)")

            fig.text(0.25, 1, (message+"\n"), fontdict)
            
            axs[0].plot(np.linspace(0, geodesic_distance, samples), data["elevation"], linestyle="solid", color="k")

            axs[1].plot(real_Z, imag_Z, linestyle="solid", color="k")
            axs[1].plot(real_Z, line_of_vision, linestyle="dashdot", color="g")
            axs[1].plot(real_Z, masked_view, linestyle="solid", color="r")
        
            axs[2].plot(real_Z, imag_Z, linestyle="solid", color="k")
            axs[2].plot(real_Z, line_of_vision, linestyle="dashdot", color="g")
            axs[2].plot(real_Z, masked_view, linestyle="solid", color="r")

            # Fill in red
            for i in range(len(imag_Z)):
                if line_of_vision[i] < imag_Z[i]:
                    axs[1].fill_between(real_Z, imag_Z, masked_view, alpha=.5, linewidth=0, fc='red')
                    axs[2].fill_between(real_Z, imag_Z, masked_view, alpha=.5, linewidth=0, fc='red')

            axs[0].set(ylabel='Elevation (m)')

            axs[1].axis('equal')
            axs[1].set(ylabel='Earth radius (km)')

            axs[2].set(xlabel='Geodesic distance (km)', ylabel='//')

            plt.show()
        
    except:
        data = "error"
        real_Z = "error"
        imag_Z = "error"
        line_of_vision = "error"
        view_possible = "error"
    

    return data, view_possible

def summit_is_visible_peaks_fast(location_point, location_summit, offset_view = 10, offset_summit = -100):
  
    # Empty lists
    elevation_profile = []
    elevation_from_earth_center = []
    view_possible = []

    # Convert offsets in km
    offset_view /= 1000
    offset_summit /= 1000

    # Get constant values
    geodesic_distance = geopy.distance.GeodesicDistance(location_point, location_summit).km

    samples = geodesic_distance

    # Limit samples to 5000
    if samples > 500:
        samples = 500
    else:
        samples = round(samples)
        
    latitude = np.linspace(location_point[0], location_summit[0], samples)
    longitude = np.linspace(location_point[1], location_summit[1], samples)

    # Compute angle between the 2 locations and create a vector with sampling split of the total angle 
    angle_total_rad = np.deg2rad((geodesic_distance/geodesic_earth_perimeter)*360)
    angle_from_origin = np.flip( np.linspace(np.pi/2 - angle_total_rad/2, np.pi/2 + angle_total_rad/2 , samples) ) # + pi/2 pour centrer le tracé
        
    locations_json = []
    for i in range(samples):
        locations_json.append(str(latitude[i]) + "," + str(longitude[i]) + '|')

    locations_json = "".join(locations_json).removesuffix("|")

    json = {"locations": locations_json,
            "interpolation": "cubic",}

    # Send request and saving the response as response object
    url = "http://localhost:5000/v1/eudem25m"

    resp = requests.post(url, json)

    data = resp.json()

    lat = []
    long = []

    # Extract data from request
    for i in range(len(data["results"])):
        elevation_profile.append(data['results'][i]["elevation"])
        lat.append(data['results'][i]["location"]["lat"])
        long.append(data['results'][i]["location"]["lng"])
        try:
            elevation_from_earth_center.append(earth_radius + elevation_profile[i]/1000) # Elevation_from_earth_center in km
        except:
            elevation_from_earth_center.append(earth_radius)
            
        # Avoid abberant values
        if elevation_profile[i] == -99999:
            elevation_profile[i] = np.nan
            elevation_from_earth_center[i] = np.nan

    # Find peaks
    peaks_earth_radius = find_peaks(elevation_from_earth_center, height=True)
    peaks_index_earth_radius = peaks_earth_radius[0]
    peaks_heights_earth_radius = peaks_earth_radius[1]["peak_heights"]

    peaks_complex = trigo_to_complex(peaks_heights_earth_radius, angle_from_origin[peaks_index_earth_radius])

    peaks_index_complex = [ele.real for ele in peaks_complex]
    peak_heights_complex = [ele.imag for ele in peaks_complex]

    start_point = trigo_to_complex(elevation_from_earth_center[0] + offset_view, angle_from_origin[0])
    stop_point = trigo_to_complex(elevation_from_earth_center[-1] + offset_summit, angle_from_origin[-1])

    # Line of vision
    line_of_vision = np.linspace(start_point.imag, stop_point.imag, samples)
    
    # View is possible ? The for * 0.95 is not to take in consideration the collision of the line of vision with the target summit itself
    for i in range(len(peaks_index_complex)):
        if peak_heights_complex[i] < line_of_vision[peaks_index_earth_radius][i]:
            view_possible.append(True)
        else:
            view_possible.append(False)
            
    if view_possible.count(False) == 0:
            view_possible = True
    else:
        view_possible = False
            
    return view_possible

def dev_altimetric_profile(location_point, location_summit, plot = False, offset_view = 10, offset_summit = -100, samples=False):

    try:
        # Empty lists
        elevation_profile = []
        elevation_from_earth_center = []
        Z = []
        masked_view = []
        view_possible = []

        # Convert offsets in km
        offset_view /= 1000
        offset_summit /= 1000

        # Get constant values
        geodesic_distance = geopy.distance.GeodesicDistance(location_point, location_summit).km
        
        if samples==False:
            samples = geodesic_distance
        
        else: samples=samples
        
        # Limit samples to 5000
        if samples > 5000:
            samples = 5000
        else:
            samples = round(samples)
            
        lat = np.linspace(location_point[0], location_summit[0], samples)
        lon = np.linspace(location_point[1], location_summit[1], samples)
        
        json = '{"locations":[{'
        for i in range(len(lat)):
            json += '"latitude":' + str(lat[i]) + ',' + '"longitude":' + str(lon[i]) + "},{"
        json = json.removesuffix(",{") + "]}"

        # Compute angle between the 2 locations and create a vector with sampling split of the total angle 
        angle_total_rad = np.deg2rad((geodesic_distance/geodesic_earth_perimeter)*360)
        angle_from_origin = np.flip( np.linspace(np.pi/2 - angle_total_rad/2, np.pi/2 + angle_total_rad/2 , samples) ) # + pi/2 pour centrer le tracé
        
    
        # Send request and saving the response as response object
        url = "https://api.open-elevation.com/api/v1/lookup"

        headers = CaseInsensitiveDict()
        headers["Accept"] = "application/json"
        headers["Content-Type"] = "application/json"

        resp = requests.post(url, headers=headers, data=json)
        resp = resp.json() 
        
        lat = []
        long = []
        
        # Extract data from request
        for i in range(len(resp["results"])):
            elevation_profile.append(resp["results"][i]["elevation"])
            lat.append(resp["results"][i]["latitude"])
            long.append(resp["results"][i]["longitude"])
            elevation_from_earth_center.append(earth_radius + elevation_profile[i]/1000) # Elevation_from_earth_center in km

            # Avoid abberant values
            if elevation_profile[i] == -99999:
                elevation_profile[i] = np.nan
                elevation_from_earth_center[i] = np.nan

        # Create a pandas df
        data = pd.DataFrame()

        data["lat"] = lat
        data["lon"] = long
        data["elevation"] = elevation_profile
        data["elevation_from_earth_center"] = elevation_from_earth_center # = modulus of Z
        data["angle_from_origin"] = angle_from_origin # = arg (Z)

        # Fill gaps of nan values with a linear interpolation
        data["elevation"] = data["elevation"].interpolate(method="linear", limit=1000)
        data["elevation_from_earth_center"] = data["elevation_from_earth_center"].interpolate(method="linear")

        elevation_from_earth_center = np.array(data["elevation_from_earth_center"])

        # Generate complex coordinates of each point. We have arg(Z) = angle depuis l'origine du point and module de Z = elevation from earth center
        for i in range(len(elevation_from_earth_center)):
            Z.append(trigo_to_complex(elevation_from_earth_center[i], angle_from_origin[i]))

        start_point = trigo_to_complex(elevation_from_earth_center[0] + offset_view, angle_from_origin[0])
        stop_point = trigo_to_complex(elevation_from_earth_center[-1] + offset_summit, angle_from_origin[-1])

        data["Z"] = Z
        real_Z = [ele.real for ele in data["Z"]] #X coordinate
        imag_Z = [ele.imag for ele in data["Z"]] #Y coordinate

        # Line of vision
        line_of_vision = np.linspace(start_point.imag, stop_point.imag, samples)
        line_of_vision_index = np.linspace(start_point.real, stop_point.real, samples)
        
        # View is possible ? The for * 0.95 is not to take in consideration the collision of the line of vision with the target summit itself
        for i in range( round( len(imag_Z) * 0.95 )):
                if line_of_vision[i] > imag_Z[i]:
                    view_possible.append(True)
                else: 
                    view_possible.append(False)

        if view_possible.count(False) == 0:
                view_possible = True
        else:
            view_possible = False

        
        if plot == True:
            # Create a plotting when the line of vision is below the relief level
            for i in range( len(imag_Z) ):
                if line_of_vision[i] > imag_Z[i]:
                    masked_view.append(np.nan)
                else: 
                    masked_view.append(line_of_vision[i])


            # Plot the complex numbers
            fig, axs = plt.subplots(3)
            
            if view_possible:
                message = "Summit is visible!"
                fontdict = font = {'family': 'serif',
                                    'color':  'green',
                                    'weight': 'bold',
                                    'size': 20
                                    }
            else:
                message = "Summit is not visible .."
                fontdict = font = {'family': 'serif',
                                    'color':  'red',
                                    'weight': 'bold',
                                    'size': 20
                                    }

            fig.suptitle("Altimetric profiles (horizontal and geodesic)")

            fig.text(0.25, 1, (message+"\n"), fontdict)
            
            axs[0].plot(np.linspace(0, geodesic_distance, samples), data["elevation"], linestyle="solid", color="k")

            axs[1].plot(real_Z, imag_Z, linestyle="solid", color="k")
            axs[1].plot(real_Z, line_of_vision, linestyle="dashdot", color="g")
            axs[1].plot(real_Z, masked_view, linestyle="solid", color="r")
        
            axs[2].plot(real_Z, imag_Z, linestyle="solid", color="k")
            axs[2].plot(real_Z, line_of_vision, linestyle="dashdot", color="g")
            axs[2].plot(real_Z, masked_view, linestyle="solid", color="r")

            # Fill in red
            for i in range(len(imag_Z)):
                if line_of_vision[i] < imag_Z[i]:
                    axs[1].fill_between(real_Z, imag_Z, masked_view, alpha=.5, linewidth=0, fc='red')
                    axs[2].fill_between(real_Z, imag_Z, masked_view, alpha=.5, linewidth=0, fc='red')

            axs[0].set(ylabel='Elevation (m)')

            axs[1].axis('equal')
            axs[1].set(ylabel='Earth radius (km)')

            axs[2].set(xlabel='Geodesic distance (km)', ylabel='//')

            plt.show()
    except:
        print("error point")
        
    return data, real_Z, imag_Z, line_of_vision, view_possible

def altimetric_geodesic_elevationapi(location_point, location_summit, plot = False, offset_view = 10, offset_summit = -100):

    # Empty lists
    elevation_profile = []
    lat = []
    long = []
    elevation_from_earth_center = []
    Z = []
    masked_view = []
    view_possible = []

    # Convert offsets in km
    offset_view /= 1000
    offset_summit /= 1000

    # Get constant values
    geodesic_distance = geopy.distance.GeodesicDistance(location_point, location_summit).km
    if geodesic_distance >= 500:
        print("Geodesic distance > 500. Please retry with an inferior value")

    try:
        # Send request and saving the response as response object
        url = "https://api.elevationapi.com/api/Elevation/line/"
        url +=  str(location_point[0]) + "," + str(location_point[1]) + "/" + str(location_summit[0]) + "," + str(location_summit[1])
        url += "?dataSet=SRTM_GL3&reduceResolution=10"
        resp = requests.get(url)
        data=resp.json()
        
        samples = len(data["geoPoints"])
        
        # Compute angle between the 2 locations and create a vector with sampling split of the total angle 
        angle_total_rad = np.deg2rad((geodesic_distance/geodesic_earth_perimeter)*360)
        angle_from_origin = np.flip( np.linspace(np.pi/2 - angle_total_rad/2, np.pi/2 + angle_total_rad/2 , samples) ) # + pi/2 pour centrer le tracé -> arg (Z)
        
        # Extract data from request
        for i in range(len(data["geoPoints"])):
            elevation_profile.append(data['geoPoints'][i]["elevation"])
            lat.append(data['geoPoints'][i]["latitude"])
            long.append(data['geoPoints'][i]["longitude"])
            elevation_from_earth_center.append(earth_radius + elevation_profile[i]/1000) # Elevation_from_earth_center in km

        # Create a pandas df
        data = pd.DataFrame()
        data["lat"] = lat
        data["lon"] = long
        data["elevation"] = elevation_profile
        data["elevation_from_earth_center"] = elevation_from_earth_center # = modulus of Z
        data["angle_from_origin"] = angle_from_origin # = arg (Z)

        # Generate complex coordinates of each point. We have arg(Z) = angle depuis l'origine du point and module de Z = elevation from earth center
        for i in range(len(elevation_from_earth_center)):
            Z.append(trigo_to_complex(elevation_from_earth_center[i], angle_from_origin[i]))

        start_point = trigo_to_complex(elevation_from_earth_center[0] + offset_view, angle_from_origin[0])
        stop_point = trigo_to_complex(elevation_from_earth_center[-1] + offset_summit, angle_from_origin[-1])

        data["Z"] = Z
        real_Z = [ele.real for ele in data["Z"]] #X coordinate
        imag_Z = [ele.imag for ele in data["Z"]] #Y coordinate

        # Line of vision
        line_of_vision = np.linspace(start_point.imag, stop_point.imag, samples)
        line_of_vision_index = np.linspace(start_point.real, stop_point.real, samples)
        
        # View is possible ? The for * 0.95 is not to take in consideration the collision of the line of vision with the target summit itself
        for i in range( round( len(imag_Z) * 0.95 )):
                if line_of_vision[i] > imag_Z[i]:
                    view_possible.append(True)
                else: 
                    view_possible.append(False)

        if view_possible.count(False) == 0:
                view_possible = True
        else:
            view_possible = False

        
        if plot == True:
            # Create a plotting when the line of vision is below the relief level
            for i in range( len(imag_Z) ):
                if line_of_vision[i] > imag_Z[i]:
                    masked_view.append(np.nan)
                else: 
                    masked_view.append(line_of_vision[i])

            # Plot the complex numbers
            fig, axs = plt.subplots(3)
            
            if view_possible:
                message = "Summit is visible!"
                fontdict = font = {'family': 'serif',
                                    'color':  'green',
                                    'weight': 'bold',
                                    'size': 20
                                    }
            else:
                message = "Summit is not visible .."
                fontdict = font = {'family': 'serif',
                                    'color':  'red',
                                    'weight': 'bold',
                                    'size': 20
                                    }

            fig.suptitle("Altimetric profiles (horizontal and geodesic)")

            fig.text(0.25, 1, (message+"\n"), fontdict)
            
            axs[0].plot(np.linspace(0, geodesic_distance, samples), data["elevation"], linestyle="solid", color="k")

            axs[1].plot(real_Z, imag_Z, linestyle="solid", color="k")
            axs[1].plot(real_Z, line_of_vision, linestyle="dashdot", color="g")
            axs[1].plot(real_Z, masked_view, linestyle="solid", color="r")
        
            axs[2].plot(real_Z, imag_Z, linestyle="solid", color="k")
            axs[2].plot(real_Z, line_of_vision, linestyle="dashdot", color="g")
            axs[2].plot(real_Z, masked_view, linestyle="solid", color="r")

            # Fill in red
            for i in range(len(imag_Z)):
                if line_of_vision[i] < imag_Z[i]:
                    axs[1].fill_between(real_Z, imag_Z, masked_view, alpha=.5, linewidth=0, fc='red')
                    axs[2].fill_between(real_Z, imag_Z, masked_view, alpha=.5, linewidth=0, fc='red')

            axs[0].set(ylabel='Elevation (m)')

            axs[1].axis('equal')
            axs[1].set(ylabel='Earth radius (km)')

            axs[2].set(xlabel='Geodesic distance (km)', ylabel='//')

            plt.show()
        
    except:
        print("error with this point")
        
    return data, real_Z, imag_Z, line_of_vision, view_possible

def altimetric_geodesic_IGN(location_point, location_summit, plot = False, offset_view = 10, offset_summit = -100, samples=False):

    # Empty lists
    elevation_profile = []
    lat = []
    long = []
    elevation_from_earth_center = []
    Z = []
    masked_view = []
    view_possible = []

    # Convert offsets in km
    offset_view /= 1000
    offset_summit /= 1000

    # Get constant values
    geodesic_distance = geopy.distance.GeodesicDistance(location_point, location_summit).km
    
    if samples==False:
        samples = geodesic_distance*2
    else: samples=samples
    
    # Limit samples to 5000
    if samples > 5000:
        samples = 5000
    else:
        samples = round(samples)

    # Compute angle between the 2 locations and create a vector with sampling split of the total angle 
    angle_total_rad = np.deg2rad((geodesic_distance/geodesic_earth_perimeter)*360)
    angle_from_origin = np.flip( np.linspace(np.pi/2 - angle_total_rad/2, np.pi/2 + angle_total_rad/2 , samples) ) # + pi/2 pour centrer le tracé
    
    try:
        # Send request and saving the response as response object
        URL = "https://wxs.ign.fr/calcul/alti/rest/elevationLine.json?sampling=" + \
            str(samples) + "&lon=" + str(location_point[1]) + "|" + str(location_summit[1]) + "&lat=" + str(location_point[0]) + "|" + str(location_summit[0]) + "&indent=true"
        r = requests.get(url = URL)
        data = r.json()
        
        
        
        # Extract data from request
        for i in range(len(data["elevations"])):
            elevation_profile.append(data['elevations'][i]["z"])
            lat.append(data['elevations'][i]["lat"])
            long.append(data['elevations'][i]["lon"])
            elevation_from_earth_center.append(earth_radius + elevation_profile[i]/1000) # Elevation_from_earth_center in km

            # Avoid abberant values
            if elevation_profile[i] == -99999:
                elevation_profile[i] = np.nan
                elevation_from_earth_center[i] = np.nan

        # Create a pandas df
        data = pd.DataFrame()

        data["lat"] = lat
        data["lon"] = long
        data["elevation"] = elevation_profile
        data["elevation_from_earth_center"] = elevation_from_earth_center # = modulus of Z
        data["angle_from_origin"] = angle_from_origin # = arg (Z)

        # Fill gaps of nan values with a linear interpolation
        data["elevation"] = data["elevation"].interpolate(method="linear", limit=1000)
        data["elevation_from_earth_center"] = data["elevation_from_earth_center"].interpolate(method="linear")

        elevation_from_earth_center = np.array(data["elevation_from_earth_center"])

        # Generate complex coordinates of each point. We have arg(Z) = angle depuis l'origine du point and module de Z = elevation from earth center
        for i in range(len(elevation_from_earth_center)):
            Z.append(trigo_to_complex(elevation_from_earth_center[i], angle_from_origin[i]))

        start_point = trigo_to_complex(elevation_from_earth_center[0] + offset_view, angle_from_origin[0])
        stop_point = trigo_to_complex(elevation_from_earth_center[-1] + offset_summit, angle_from_origin[-1])

        data["Z"] = Z
        real_Z = [ele.real for ele in data["Z"]] #X coordinate
        imag_Z = [ele.imag for ele in data["Z"]] #Y coordinate

        # Line of vision
        line_of_vision = np.linspace(start_point.imag, stop_point.imag, samples)
        line_of_vision_index = np.linspace(start_point.real, stop_point.real, samples)
        
        # View is possible ? The for * 0.95 is not to take in consideration the collision of the line of vision with the target summit itself
        for i in range( round( len(imag_Z) * 0.95 )):
                if line_of_vision[i] > imag_Z[i]:
                    view_possible.append(True)
                else: 
                    view_possible.append(False)

        if view_possible.count(False) == 0:
                view_possible = True
        else:
            view_possible = False

        
        if plot == True:
            # Create a plotting when the line of vision is below the relief level
            for i in range( len(imag_Z) ):
                if line_of_vision[i] > imag_Z[i]:
                    masked_view.append(np.nan)
                else: 
                    masked_view.append(line_of_vision[i])


            # Plot the complex numbers
            fig, axs = plt.subplots(3)
            
            if view_possible:
                message = "Summit is visible!"
                fontdict = font = {'family': 'serif',
                                    'color':  'green',
                                    'weight': 'bold',
                                    'size': 20
                                    }
            else:
                message = "Summit is not visible .."
                fontdict = font = {'family': 'serif',
                                    'color':  'red',
                                    'weight': 'bold',
                                    'size': 20
                                    }

            fig.suptitle("Altimetric profiles (horizontal and geodesic)")

            fig.text(0.25, 1, (message+"\n"), fontdict)
            
            axs[0].plot(np.linspace(0, geodesic_distance, samples), data["elevation"], linestyle="solid", color="k")

            axs[1].plot(real_Z, imag_Z, linestyle="solid", color="k")
            axs[1].plot(real_Z, line_of_vision, linestyle="dashdot", color="g")
            axs[1].plot(real_Z, masked_view, linestyle="solid", color="r")
        
            axs[2].plot(real_Z, imag_Z, linestyle="solid", color="k")
            axs[2].plot(real_Z, line_of_vision, linestyle="dashdot", color="g")
            axs[2].plot(real_Z, masked_view, linestyle="solid", color="r")

            # Fill in red
            for i in range(len(imag_Z)):
                if line_of_vision[i] < imag_Z[i]:
                    axs[1].fill_between(real_Z, imag_Z, masked_view, alpha=.5, linewidth=0, fc='red')
                    axs[2].fill_between(real_Z, imag_Z, masked_view, alpha=.5, linewidth=0, fc='red')

            axs[0].set(ylabel='Elevation (m)')

            axs[1].axis('equal')
            axs[1].set(ylabel='Earth radius (km)')

            axs[2].set(xlabel='Geodesic distance (km)', ylabel='//')

            plt.show()
        
    except:
        print("error with this point")
        
    return data, real_Z, imag_Z, line_of_vision, view_possible

def dev(location_point, location_summit, offset_view = 10, offset_summit = -100, plot = True):

    # Empty lists
    elevation_profile = []
    lat = []
    long = []
    elevation_from_earth_center = []
    Z = []
    masked_view = []
    view_possible = []

    # Convert offsets in km
    offset_view /= 1000
    offset_summit /= 1000

    # Get constant values
    geodesic_distance = geopy.distance.GeodesicDistance(location_point, location_summit).km
    samples = geodesic_distance

    # Limit samples to 5000
    if samples > 5000:
        samples = 5000
    else:
        samples = round(samples)

    # Compute angle between the 2 locations and create a vector with sampling split of the total angle 
    angle_total_rad = np.deg2rad((geodesic_distance/geodesic_earth_perimeter)*360)
    angle_from_origin = np.flip( np.linspace(np.pi/2 - angle_total_rad/2, np.pi/2 + angle_total_rad/2 , samples) ) # + pi/2 pour centrer le tracé -> arg (Z)
    
    # Send request and saving the response as response object
    URL = "https://wxs.ign.fr/calcul/alti/rest/elevationLine.json?sampling=" + \
        str(samples) + "&lon=" + str(location_point[1]) + "|" + str(location_summit[1]) + "&lat=" + str(location_point[0]) + "|" + str(location_summit[0]) + "&indent=true"
    r = requests.get(url = URL)
    data = r.json()
    
    # Extract data from request
    for i in range(len(data["elevations"])):
        elevation_profile.append(data['elevations'][i]["z"])
        lat.append(data['elevations'][i]["lat"])
        long.append(data['elevations'][i]["lon"])
        elevation_from_earth_center.append(earth_radius + elevation_profile[i]/1000) # Elevation_from_earth_center in km

        # Avoid abberant values
        if elevation_profile[i] == -99999:
            elevation_profile[i] = np.nan
            elevation_from_earth_center[i] = np.nan

      # Create a pandas df
    data = pd.DataFrame()

    data["lat"] = lat
    data["lon"] = long
    data["elevation"] = elevation_profile
    data["elevation_from_earth_center"] = elevation_from_earth_center # = modulus of Z
    data["angle_from_origin"] = angle_from_origin # = arg (Z)

    # Fill gaps of nan values with a linear interpolation
    data["elevation"] = data["elevation"].interpolate(method="linear", limit=1000)
    data["elevation_from_earth_center"] = data["elevation_from_earth_center"].interpolate(method="linear")

    elevation_from_earth_center = np.array(data["elevation_from_earth_center"])
    elevation_profile = np.array(data["elevation"])

    # Find peaks
    peaks_earth_radius = find_peaks(elevation_from_earth_center, height=True)
    peaks_index_earth_radius = peaks_earth_radius[0]
    peaks_heights_earth_radius = peaks_earth_radius[1]["peak_heights"]

    peaks_complex = trigo_to_complex(peaks_heights_earth_radius, angle_from_origin[peaks_index_earth_radius])
    
    peaks_index_complex = [ele.real for ele in peaks_complex]
    peak_heights_complex = [ele.imag for ele in peaks_complex]

    # Generate complex coordinates of each point. We have arg(Z) = angle depuis l'origine du point and module de Z = elevation from earth center
    for i in range(len(elevation_from_earth_center)):
        Z.append(trigo_to_complex(elevation_from_earth_center[i], angle_from_origin[i]))

    start_point = trigo_to_complex(elevation_from_earth_center[0] + offset_view, angle_from_origin[0])
    stop_point = trigo_to_complex(elevation_from_earth_center[-1] + offset_summit, angle_from_origin[-1])
    
   
    data["Z"] = Z
    real_Z = np.array([ele.real for ele in data["Z"]]) #X coordinate
    imag_Z = [ele.imag for ele in data["Z"]] #Y coordinate

    # Line of vision
    line_of_vision = np.linspace(start_point.imag, stop_point.imag, samples)
    line_of_vision_index = np.linspace(start_point.real, stop_point.real, samples)
    
    for i in range(len(peaks_index_complex)):
        if line_of_vision[int(peaks_index_complex[i])] > peak_heights_complex[i]:
            print(True)
       
    if plot == True:
        # Create a line of peaks
        test_vision = pd.DataFrame()
        test_vision["peaks_height"] = peak_heights_complex
        test_vision.index = peaks_index_complex
        relief =  pd.DataFrame()
        relief["relief"] = imag_Z
        relief.index = real_Z
    
        peaks_line = relief.join(test_vision)
        peaks_line["index"] = real_Z
    
        peaks_line.index = np.linspace(0, len(peaks_line["index"])-1, len(peaks_line["index"]))
        peaks_line["peaks_height"][0] = peaks_line["relief"][0]
        peaks_line["peaks_height"][len(peaks_line["peaks_height"])-1] = peaks_line["relief"][len(peaks_line["peaks_height"])-1]

        
        peaks_line["peaks_height"] = peaks_line["peaks_height"].interpolate(method="linear")
        
    # View is possible ? The for * 0.95 is not to take in consideration the collision of the line of vision with the target summit itself
    for i in range( round( len(imag_Z) * 0.95 )):
            if line_of_vision[i] > imag_Z[i]:
                view_possible.append(True)
            else: 
                view_possible.append(False)

    if view_possible.count(False) == 0:
            view_possible = True
    else:
        view_possible = False

    if plot == True:
        # Create a plotting when the line of vision is below the relief level
        for i in range( len(imag_Z) ):
            if line_of_vision[i] > imag_Z[i]:
                masked_view.append(np.nan)
            else: 
                masked_view.append(line_of_vision[i])


        # Plot the complex numbers
        fig, axs = plt.subplots(3)
        
        if view_possible:
          message = "Summit is visible!"
          fontdict = font = {'family': 'serif',
                            'color':  'green',
                            'weight': 'bold',
                            'size': 20
                            }
        else:
          message = "Summit is not visible .."
          fontdict = font = {'family': 'serif',
                            'color':  'red',
                            'weight': 'bold',
                            'size': 20
                            }

        fig.suptitle("Altimetric profiles (horizontal and geodesic")

        fig.text(0.25, 1, (message+"\n"), fontdict)

        axs[0].plot(real_Z, imag_Z, linestyle="solid", color="k")
        axs[0].plot(real_Z, line_of_vision, linestyle="dashdot", color="g")
        axs[0].plot(real_Z, masked_view, linestyle="solid", color="r")
        axs[0].scatter(peaks_index_complex, peak_heights_complex, s=10, marker="^", color="g")

        axs[1].plot(real_Z, imag_Z, linestyle="solid", color="k")
        axs[1].plot(real_Z, line_of_vision, linestyle="dashdot", color="g")
        axs[1].plot(real_Z, masked_view, linestyle="solid", color="r")
        axs[1].scatter(peaks_index_complex, peak_heights_complex, s=50, marker="^", color="g")

        axs[2].scatter(peaks_index_complex, peak_heights_complex, s=50, marker="^", color="g")
        axs[2].plot(real_Z, peaks_line["peaks_height"], linestyle="solid", color="k")
        axs[2].plot(real_Z, line_of_vision, linestyle="dashdot", color="g")
        #axs[2].plot(real_Z, masked_view, linestyle="solid", color="r")
        # axs[1].scatter(real_Z, peaks_line_test, s=50, marker="^", color="g")

        # Fill in red
        for i in range(len(imag_Z)):
            if line_of_vision[i] < imag_Z[i]:
                axs[0].fill_between(real_Z, imag_Z, masked_view, alpha=.5, linewidth=0, fc='red')
                axs[1].fill_between(real_Z, imag_Z, masked_view, alpha=.5, linewidth=0, fc='red')

        axs[0].axis('equal')
        axs[0].set(ylabel='Earth radius (km)')

        axs[2].set(xlabel='Geodesic distance (km)', ylabel='//')

        plt.show()
    
    return view_possible

def is_visible(grid_locations, location_summit):
    view_possible_grid = []
    for i in tqdm(range(len(grid_locations["lat_grid"]))):
        location_1 = [grid_locations["lat_grid"][i], grid_locations["lon_grid"][i]]
        data, real_Z, imag_Z, line_of_vision, view_possible = dev_altimetric_profile(location_point=location_1, location_summit=location_summit, 
        plot=False, offset_view=10, offset_summit=-100)
        view_possible_grid.append(view_possible)

    summit_itself = pd.DataFrame()

    grid_locations["view_possible"] = view_possible_grid
    grid_locations = grid_locations.sort_values(by="view_possible", ascending=False)

    return grid_locations

def altimetric_geodesic_apielevation(location_point, location_summit, plot = False, offset_view = 10, offset_summit = -100, samples=False):

    # Empty lists
    elevation_profile = []
    lat = []
    long = []
    elevation_from_earth_center = []
    Z = []
    masked_view = []
    view_possible = []

    # Convert offsets in km
    offset_view /= 1000
    offset_summit /= 1000

    # Get constant values
    geodesic_distance = geopy.distance.GeodesicDistance(location_point, location_summit).km
    if samples==False:
        samples = geodesic_distance*2
    else: samples=samples
    
    # Limit samples to 5000
    if samples > 1500:
        samples = 1500
    else:
        samples = round(samples)

    # Compute angle between the 2 locations and create a vector with sampling split of the total angle 
    angle_total_rad = np.deg2rad((geodesic_distance/geodesic_earth_perimeter)*360)
    angle_from_origin = np.flip( np.linspace(np.pi/2 - angle_total_rad/2, np.pi/2 + angle_total_rad/2 , samples) ) # + pi/2 pour centrer le tracé
    
    latitude = np.linspace(location_point[0], location_summit[0], samples)
    longitude = np.linspace(location_point[1], location_summit[1], samples)

    try:
        # Send request and saving the response as response object
        url = "https://api.open-elevation.com/api/v1/lookup"

        headers = CaseInsensitiveDict()
        headers["Content-Type"] = "application/json"

        data = '{"locations":['
        for i in range(samples):
            data += '{"latitude": ' + str(latitude[i]) + "," + '"longitude": ' + str(longitude[i]) + "},"

        data = data.removesuffix(",") + ']}'

        resp = requests.post(url, headers=headers, data=data)
        data = resp.json()
        
        
        # Extract data from request
        for i in range(len(data["results"])):
            elevation_profile.append(data['results'][i]["elevation"])
            lat.append(data['results'][i]["latitude"])
            long.append(data['results'][i]["longitude"])
            elevation_from_earth_center.append(earth_radius + elevation_profile[i]/1000) # Elevation_from_earth_center in km

            # Avoid abberant values
            if elevation_profile[i] == -99999:
                elevation_profile[i] = np.nan
                elevation_from_earth_center[i] = np.nan

        # Create a pandas df
        data = pd.DataFrame()

        data["lat"] = lat
        data["lon"] = long
        data["elevation"] = elevation_profile
        data["elevation_from_earth_center"] = elevation_from_earth_center # = modulus of Z
        data["angle_from_origin"] = angle_from_origin # = arg (Z)

        # Fill gaps of nan values with a linear interpolation
        data["elevation"] = data["elevation"].interpolate(method="linear", limit=1000)
        data["elevation_from_earth_center"] = data["elevation_from_earth_center"].interpolate(method="linear")

        elevation_from_earth_center = np.array(data["elevation_from_earth_center"])

        # Generate complex coordinates of each point. We have arg(Z) = angle depuis l'origine du point and module de Z = elevation from earth center
        for i in range(len(elevation_from_earth_center)):
            Z.append(trigo_to_complex(elevation_from_earth_center[i], angle_from_origin[i]))

        start_point = trigo_to_complex(elevation_from_earth_center[0] + offset_view, angle_from_origin[0])
        stop_point = trigo_to_complex(elevation_from_earth_center[-1] + offset_summit, angle_from_origin[-1])

        data["Z"] = Z
        real_Z = [ele.real for ele in data["Z"]] #X coordinate
        imag_Z = [ele.imag for ele in data["Z"]] #Y coordinate

        # Line of vision
        line_of_vision = np.linspace(start_point.imag, stop_point.imag, samples)
        line_of_vision_index = np.linspace(start_point.real, stop_point.real, samples)
        
        # View is possible ? The for * 0.95 is not to take in consideration the collision of the line of vision with the target summit itself
        for i in range( round( len(imag_Z) * 0.95 )):
                if line_of_vision[i] > imag_Z[i]:
                    view_possible.append(True)
                else: 
                    view_possible.append(False)

        if view_possible.count(False) == 0:
                view_possible = True
        else:
            view_possible = False

        
        if plot == True:
            # Create a plotting when the line of vision is below the relief level
            for i in range( len(imag_Z) ):
                if line_of_vision[i] > imag_Z[i]:
                    masked_view.append(np.nan)
                else: 
                    masked_view.append(line_of_vision[i])


            # Plot the complex numbers
            fig, axs = plt.subplots(3)
            
            if view_possible:
                message = "Summit is visible!"
                fontdict = font = {'family': 'serif',
                                    'color':  'green',
                                    'weight': 'bold',
                                    'size': 20
                                    }
            else:
                message = "Summit is not visible .."
                fontdict = font = {'family': 'serif',
                                    'color':  'red',
                                    'weight': 'bold',
                                    'size': 20
                                    }

            fig.suptitle("Altimetric profiles (horizontal and geodesic)")

            fig.text(0.25, 1, (message+"\n"), fontdict)
            
            axs[0].plot(np.linspace(0, geodesic_distance, samples), data["elevation"], linestyle="solid", color="k")

            axs[1].plot(real_Z, imag_Z, linestyle="solid", color="k")
            axs[1].plot(real_Z, line_of_vision, linestyle="dashdot", color="g")
            axs[1].plot(real_Z, masked_view, linestyle="solid", color="r")
        
            axs[2].plot(real_Z, imag_Z, linestyle="solid", color="k")
            axs[2].plot(real_Z, line_of_vision, linestyle="dashdot", color="g")
            axs[2].plot(real_Z, masked_view, linestyle="solid", color="r")

            # Fill in red
            for i in range(len(imag_Z)):
                if line_of_vision[i] < imag_Z[i]:
                    axs[1].fill_between(real_Z, imag_Z, masked_view, alpha=.5, linewidth=0, fc='red')
                    axs[2].fill_between(real_Z, imag_Z, masked_view, alpha=.5, linewidth=0, fc='red')

            axs[0].set(ylabel='Elevation (m)')

            axs[1].axis('equal')
            axs[1].set(ylabel='Earth radius (km)')

            axs[2].set(xlabel='Geodesic distance (km)', ylabel='//')

            plt.show()
        
    except:
        print("error with this point")
        
    return data, real_Z, imag_Z, line_of_vision, view_possible

def summit_is_visible_multi_locations(grid_locations, location_summit):
    view_possible_grid = []

    for i in tqdm(range(len(grid_locations["lat_grid"]))):
        try:
            location_1 = [grid_locations["lat_grid"][i], grid_locations["lon_grid"][i]]
            _, _, _, _, view_possible = summit_is_visible(location_point=location_1, location_summit=location_summit, 
            plot=False, offset_view=10, offset_summit=-100)
            view_possible_grid.append(view_possible)
        except:
            view_possible_grid.append("error")

    summit_itself = pd.DataFrame()
    grid_locations["view_possible"] = view_possible_grid

    return grid_locations

def summit_is_visible_fast_offline_eudem(location_point, location_summit, offset_view = 10, offset_summit = -100):
    # offline eudem25m
    earth_radius = EARTH_RADIUS
    offset_view, offset_summit, geodesic_distance, geodesic_earth_perimeter = offset_view/1000,  offset_summit/1000, GeodesicDistance(location_point, location_summit).km, (2*np.pi*earth_radius)

    samples = (round(geodesic_distance*2) if round(geodesic_distance*2) <= 100 else 100)

    # Compute angle between the 2 locations and create a vector with sampling split of the total angle 
    angle_total_rad = np.deg2rad((geodesic_distance/geodesic_earth_perimeter)*360) 
    angle_from_origin = np.flip(np.linspace(np.pi/2 - angle_total_rad/2, np.pi/2 + angle_total_rad/2 , samples)) # + pi/2 pour centrer le tracé

    latitude = np.linspace(location_point[0], location_summit[0], samples)
    longitude = np.linspace(location_point[1], location_summit[1], samples)

    url = "http://localhost:5000/v1/eudem25m"
    json = {"locations": "".join([str(latitude[i]) + "," + str(longitude[i]) + '|' for i in range(samples)]).removesuffix("|"),
            "interpolation": "cubic",}
    response = requests.post(url, json)
    data = response.json()

    elevation_profile, lat, long, elevation_from_earth_center = np.array([data['results'][i]["elevation"] for i in range(samples)], dtype=int), \
                                                                np.array([data['results'][i]["location"]["lat"] for i in range(samples)]), \
                                                                np.array([data['results'][i]["location"]["lng"] for i in range(samples)]), \
                                                                np.add(np.array([data['results'][i]["elevation"] for i in range(samples)], dtype=int)/1000, earth_radius) # Elevation_from_earth_center in km
                                                                
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
