import pycrs
import leafmap
import pandas as pd
import os
import up42
import requests, base64
import pystac_client
import matplotlib.pyplot as plt
import httpx
from httpx_auth import OAuth2ClientCredentials
import json
from pathlib import Path
import numpy as n
import earthpy as et
import earthpy.spatial as es
import earthpy.plot as ep
import glob
import rioxarray as rxr
import xarray as xr
import json
from pyproj import Proj, transform
from geojson import Point, Polygon, MultiPolygon, FeatureCollection, Feature
from toolz.dicttoolz import get_in
from typing import Final
import order
import asset
import request
import datacube


data_folder = 'assets/'
asset_dir = os.path.join(data_folder , "S2/")
os.mkdir('assets/result')
os.mkdir(asset_dir)

limit = int(os.getenv('SEARCH_RESULT_LIMIT_MAX'))
aoi_geometry = up42.read_vector_file(os.path.join(data_folder, "amazonas.geojson"))
# authenticate with UP42
_UP42_AUTH_URL: Final[str] = "https://api.up42.com/oauth/token"

client_auth = OAuth2ClientCredentials(
                _UP42_AUTH_URL,
                client_id = "53caf794-d4af-4f24-96d5-fedcbaa27e67",
                client_secret = "fyRfimk0.B281MMelUyl4IeAIqJLNTo38R5QrCOAWv7s"
        )
# Access catalog & Place orders
order.order(limit, aoi_geometry)

# Complex searches
complex_search_results_max_lim = request.complex_search_request(data_folder, limit, client_auth)

# Download the assets
complex_search_results_max_lim_asset_ids = list(map(lambda e: get_in(["properties", "up42-system:asset_id"], e),
                                    complex_search_results_max_lim["features"]))

asset.download_search_request(complex_search_results_max_lim, 
                              complex_search_results_max_lim_asset_ids, 
                              asset_dir)

ds_all = datacube.create_datacube(asset_dir)

# Compute NDVI time series & Visulaze 
ds_all['ndvi'] = (ds_all['band8'] - ds_all['band4'])/\
                 (ds_all['band8'] + ds_all['band4'])
# Reindex datacube based on time
new_time = sorted(ds_all.time.values)
ds_all = ds_all.reindex(time = new_time)

point_x, point_y = 150, 1500
sentinel_point = ds_all.interp(x=point_x, y=point_y,method="nearest")
sentinel_table = sentinel_point.to_dataframe()

## Plot 
ds_all.ndvi.plot(col='time', cmap='RdYlGn')
ds_all.band4.plot(col='time')


plt.figure(figsize=(11, 4))
sentinel_table['ndvi'].plot(label='ndvi', marker='*', linestyle='', markersize=2, color = 'red')
plt.savefig('assets/result/point_ndvi.png')

ds_all.ndvi.mean(['x', 'y']).plot.line('b-^', figsize=(11,4))
plt.title('Zonal mean of vegetation timeseries')
plt.savefig('assets/result/area_ndvi_mean.png')
