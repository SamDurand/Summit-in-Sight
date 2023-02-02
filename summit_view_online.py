from summit_lib import *

pont_du_Mont_Blanc_Geneve = [46.206939 , 6.147794]
Mont_Blanc = [45.832542 , 6.864717]

offset_view = 2
offset_summit = -50

data, view_possible = summit_is_visible_online(location_point=pont_du_Mont_Blanc_Geneve, location_summit=Mont_Blanc,
                                                   plot=True, offset_view=offset_view, offset_summit=offset_summit)