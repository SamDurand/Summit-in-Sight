![image](data/pictures/logo_summit.png)

# **Summit-in-Sight**
Python package to determine the visibility of a summit from specified locations, allowing you to generate a map with the locations from which a summit is in sight! 

## **See the results: where can we see the summit of Mont Blanc from?**
**Global results:** (click on image)

[![global_results_Mont_Blanc](data/pictures/global_results_Mont_Blanc.png)](https://htmlpreview.github.io/?https://raw.githubusercontent.com/SamDurand/Summit-in-Sight/main/data/maps/global_results_Mont_Blanc.html)

**View from summits only:** (click on image)

[![view from summits](data/pictures/from_summits_MontBlanc_map.png)](https://htmlpreview.github.io/?https://raw.githubusercontent.com/SamDurand/Summit-in-Sight/main/data/maps/from_summits_Mont_Blanc.html)

## **Installation**

1. Zip download the repository or clone it to your local machine using this command in your terminal window:
```
git clone https://github.com/SamDurand/Summit-in-Sight.git
```
2. Open the terminal or command prompt and navigate to the directory containing the requirements.txt file.

3. Run the command:
```
pip install -r requirements.txt
```
4. The packages will be installed in your Python environment, and you can verify this by running `pip freeze` to see all of the installed packages and their versions.



5. (Optional) Offline data downloading:
   
   This package relies on the awesome **[opentopodata API](https://www.opentopodata.org/)** to get elevation data. All online versions of the functions works well but with some limitations. 
   
   If you want to calculate the visibility of a peak for a very large number of locations (to generate a map for example), I suggest you to host your own elevation data on your computer. To do so, follow the [instructions here](https://www.opentopodata.org/#host-your-own).

   For instance, when computing the visibility of a peak for a large number of locations, the `multi_locations_online.py` usually take around **1s per location** whereas the `multi_locations_offline.py` has performed up to **10 locations per second**!

   However, to try it out, the file `multi_locations_online.py` does the job.


## **Basic usage**

### **1) Determine if a summit is in sight from a location**

**A full example is provided in `single_location_online.py`.**

Use the `summit_is_visible_online` function to check if a summit is visible from a given location. For example, you can use it to check if Mont Blanc is visible from Geneva, Switzerland. 

To do so, you need to provide the decimal coordinates of your location (`location_point`) and the coordinates of the summit (`location_summit`). You can also specify an offset for your location (`offset_view`) and for the summit (`offset_summit`). The function will then return a boolean value (True or False) indicating if the summit is visible from your location. Additionally, it will plot a map with the visibility line between your location and the summit.

It returns:
```python
Location point: Pont du Mont-Blanc, Rue du Mont-Blanc, Grottes et Saint-Gervais, Gen??ve, 1201, Schweiz/Suisse/Svizzera/Svizra
Location summit: Les Bosses, Chamonix-Mont-Blanc, Bonneville, Haute-Savoie, Auvergne-Rh??ne-Alpes, France m??tropolitaine, 74400, France

Summit in sight! Distance =  69.54 km
```

![return](data/pictures/geneva_montblanc.png)

The first plot shows the horizontal altimetric profile between your location and the summit.

The second and third plot shows the geodesic profile between your locations. These profiles are used to compute if a summit is in sight. 

The dashed green line represents the line of sight. If the line of sight intersects the relief, the view is therefore impossible and the summits intersected are filled with red.

Some additional examples below:
1. Mont Blanc (4810m, Alps) from Lyon Fourvi??re (France):

![return](data/pictures/lyon_montblanc.png)

2. Mont Blanc (4810m, Alps) from Montpellier (France):

![return](data/pictures/montpellier_montblanc.png)

3. Mont Rosa (4634m, Alps) from Milan (Italy):

![return](data/pictures/milan_montrosa.png)

4. Mont Blanc (4810m, Alps) from Mont Cook (3724m, New Zealand):

![return](data/pictures/mtcooknz_montblanc.png)

5. Everest (8848m) from Katmandu (Nepal)
   
![return](data/pictures/katmandu_everest.png)

### **2) Generate a map of possible views of a summit**



**A full example is provided in `multi_locations_offline.py` or `multi_locations_offline.py` whether you use the online or offline version of opentopodata API.**

The `generate_locations_grid` function is used to generate the grid of locations, and `summit_is_visible_multi_locations_offline` (or online) is used to determine the visibility of a summit from each position.

To generate the grid, you must first define the limits of your bounding box, defined by its `top_left_corner` position, `bottom_right_corner` position and resolution (`res`) in kilometers.

You can also specify an offset for your location (`offset_view`) and for the summit (`offset_summit`).

The results are saved in a csv file containing the coordinates of each location and `view_possible`, the boolean value (True or False) indicating whether the summit is visible from that location. During computing, view_possible list will be written in temporary txt file (exemple: `data_temp_0.txt`). Once the code is finished, you can delete them.

You can then use the `plot_view_possible` to plot your coordinates on a map.

Finally, the function `from_summits_offline.py` allows to compute the visibility of a peak from a list of different summits. As a demonstration, a rather exhaustive list of Western Europe summits is provided in `data\summits\summits.csv`.

*Profile image was generated using AI: [DALL E](https://openai.com/dall-e-2/)*
