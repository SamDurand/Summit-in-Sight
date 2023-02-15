
![logo](data\pictures\logo.png)

# Summit-in-Sight

Python package to determine the visibility of a summit from specified locations. It allows to generate a map with the locations from which a summit is in sight.

## Installation

1. Zip download the repository or clone it to your local machine using:
```
git clone https://github.com/SamDurand/Summit-in-Sight.git
```
2. Open the terminal or command prompt and navigate to the directory containing the requirements.txt file.

3. Run the command:
```
pip install -r requirements.txt
```
4. The packages will be installed in your Python environment, and you can verify this by running `pip freeze` to see all of the installed packages and their versions.

## Basic usage

### Determine if a summit is in sight from a location

**A full example is provided in `plot_view_possible.py`.**

Use the `summit_is_visible_online` function to check if a summit is visible from a given location. For example, you can use it to check if Mont Blanc is visible from Geneva, Switzerland. 

To do so, you need to provide the decimal coordinates of your location (`location_point`) and the coordinates of the summit (`location_summit`). You can also specify an offset for your location (`offset_view`) and for the summit (`offset_summit`). The function will then return a boolean value (True or False) indicating if the summit is visible from your location. Additionally, it will plot a map with the visibility line between your location and the summit.

```python
from summit_lib import summit_is_visible_online

location_point =  [46.206939 , 6.147794] # Your location
location_summit = [45.832542 , 6.864717] # The summit to spot
offset_view = 2
offset_summit = -100

view_possible, data = summit_is_visible_online(location_point, location_summit, plot=True, offset_view=offset_view,offset_summit=offset_summit)
```

Return:
```python
Location point: Pont du Mont-Blanc, Rue du Mont-Blanc, Grottes et Saint-Gervais, Genève, 1201, Schweiz/Suisse/Svizzera/Svizra
Location summit: Les Bosses, Chamonix-Mont-Blanc, Bonneville, Haute-Savoie, Auvergne-Rhône-Alpes, France métropolitaine, 74400, France

Summit in sight! Distance =  69.54 km
```
![return](data\pictures\Geneve_MontBlanc.png)

The first plot shows the horizontal altimetric profile between your location and the summit.

The second and third plot shows the geodesic profile between your locations. These profiles are used to compute if a summit is in sight. 

The dashed green line represents the line of sight. If the line of sight intersects the relief, the view is therefore impossible and the summits intersected are filled with red.

Some additional examples below:
1. Mont Blanc (4810m, Alps) from Lyon Fourvière (France):

![return](data/pictures/Lyon_MontBlanc.png)

2. Mont Blanc (4810m, Alps) from Montpellier (France):

![return](data/pictures/Montpellier_MontBlanc.png)

3. Mont Rosa (4634m, Alps) from Milan (Italy):

![return](data/pictures/Milan_MontRosa.png)

4. Mont Blanc (4810m, Alps) from Mont Cook (3724m, New Zealand):

![return](data/pictures/MtCookNZ_MontBlanc.png)

5. Everest (8848m) from Katmandu (Nepal)
   
![return](data/pictures/Katmandu_Everest.png)


*Profile image was generated using AI: [DALL E](https://openai.com/dall-e-2/)*