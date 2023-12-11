import os 
import asset
import json 
from ipyleaflet import Map, GeoJSON, Marker, AwesomeIcon
from shapely.geometry import shape, mapping
from toolz.dicttoolz import get_in
import asset

def complex_search_request(data_folder, limit, client_auth):
    with open(os.path.join(data_folder, "amazonas.geojson"), "r") as f:
        geom_map = json.load(f)

    shape_geom_map = shape(get_in(["features", 0, "geometry"], geom_map))

    intersect_map_center = shape_geom_map.centroid

    # Add the AOI to the map. First style it and then add it.
    intersect_layer = GeoJSON(
        data=geom_map,
        style={"opacity": 1, "dashArray": "9", "fillOpacity": 0.5, "weight": 1},
        hover_style={"color": "yellow", "dashArray": "0", "fillOpacity": 0.5},
        )
    # Add a marker layer at the center.
    intersect_marker_layer = Marker(location=(intersect_map_center.y, intersect_map_center.x),
                                draggable=False, icon=AwesomeIcon(name="close",
                                                                  color_marker="green"))
   
    intersect_req_body = dict(intersects = mapping(shape_geom_map))

    my_cloud_cover_dict = dict(filter=dict(args=[
        dict(property="eo:cloud_cover"), 10],
        op="<"))

    new_intersect_req_body = intersect_req_body | my_cloud_cover_dict

    complex_search_results = asset.search_item(new_intersect_req_body, client_auth).json()
    asset.ppjson(complex_search_results)

    cloud_cover_workspace_dict = dict(filter=
        dict(args=[
             dict(args=[dict(property="eo:cloud_cover"), 10],
                  op="<"),
             dict(args=[dict(property="workspace_id"), os.getenv('WORKSPACE_ID')],
                  op="=")],
          op="and")
    )

    limit_dict = dict(limit = limit)
    complex_search_results_max_lim = asset.search_item(intersect_req_body | cloud_cover_workspace_dict | limit_dict, client_auth).json()
    asset.ppjson(complex_search_results_max_lim, expand = True)

    complex_search_results_layer = GeoJSON(data=complex_search_results_max_lim,#complex_search_results,
                                       style={"color":"red",  "opacity": 1,
                                              "dashArray": "9", "fillOpacity": 0.5,
                                              "weight": 1},
    hover_style={"color": "white", "dashArray": "0", "fillOpacity": 0.5},
    )
    return(complex_search_results)
