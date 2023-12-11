from rasterio import warp
from rasterio.crs import CRS
import rasterio
from shapely.geometry import box
import geopandas as gpd
from fiona.crs import from_epsg
import os
import pandas as pd
import glob
import xarray as xr


def paths_to_datetimeindex(paths, string_slice=(0, 10)):
    """
    Helper function to generate a Pandas datetimeindex object
    from dates contained in a file path string.

    Parameters
    ----------
    paths : list of strings
        A list of file path strings that will be used to extract times
    string_slice : tuple
        An optional tuple giving the start and stop position that
        contains the time information in the provided paths. These are
        applied to the basename (i.e. file name) in each path, not the
        path itself. Defaults to (0, 10).

    Returns
    -------
    datetime : pandas.DatetimeIndex
        A pandas.DatetimeIndex object containing a 'datetime64[ns]' derived
        from the file paths provided by `paths`.
    """

    date_strings = [os.path.basename(os.path.dirname(i)) for i in paths]
    return pd.to_datetime(date_strings)


def getFeatures(gdf):
    """Function to parse features from GeoDataFrame in such a manner that rasterio wants them"""
    import json
    return [json.loads(gdf.to_json())['features'][0]['geometry']]


def crop_raster(asset_dir, coords, band):

  file_path = os.path.join(asset_dir, f'{band}.tiff')

  with rasterio.open(file_path) as data:
    out_img, out_transform = rasterio.mask.mask(dataset=data, shapes=coords, crop=True)
    out_meta = data.meta
    epsg_code = int(data.crs.data['init'][5:])

    out_meta.update({"driver": "GTiff",
                 "height": out_img.shape[1],
                 "width": out_img.shape[2],
                 "transform": out_transform})
    out_path = os.path.join(asset_dir, f"out_tif_{band}.tif")

    with rasterio.open(out_path, "w", **out_meta) as dest:
      dest.write(out_img)

def normalize(array):
    """Normalizes numpy arrays into scale 0.0 - 1.0"""
    array_min, array_max = array.min(), array.max()
    return ((array - array_min)/(array_max - array_min))

def prep_bands_datacube(asset_dir, date, band):
  child_dir = os.path.join(asset_dir, date, f'out_tif_{band}.tif')
  data_band = rasterio.open(child_dir).read(1)
  data_band_normalized = normalize(data_band)

  data_array_band_normalized = xr.DataArray(data = data_band_normalized,
                                      dims=('x', 'y'),
                                      coords={'x': list(range(0, data_band_normalized.shape[0])),
                                              'y': list(range(0, data_band_normalized.shape[1]))})

  if(band == 'b04'):
    data_array_band_normalized.name = 'band4'
  elif(band == 'b08'):
    data_array_band_normalized.name = 'band8'

  return(data_array_band_normalized)


"""# Create datacube"""

def create_datacube(asset_dir):
  # WGS84 coordinates
  minx, miny = -55.80602463366668, -13.49938970772358,
  maxx, maxy = -55.520612343249226, -13.267580954511516,
  bbox = box(minx, miny, maxx, maxy)
  geo = gpd.GeoDataFrame({'geometry': bbox}, index=[0], crs=from_epsg(4326))
  # Project the Polygon into same CRS as the grid
  geo = geo.to_crs(crs=CRS.from_epsg(32721))
  coords = getFeatures(geo)
  for i in os.listdir(asset_dir):
    crop_raster(os.path.join(asset_dir, i), coords, 'b04')
    crop_raster(os.path.join(asset_dir, i), coords, 'b08')
    list_time=list()
  for i in os.listdir(asset_dir):
    list_time.append(glob.glob((os.path.join(asset_dir, i, 'out_tif_b04.tif')),recursive = True)[0])

  list_data_array_merged_time = list()
  for i in os.listdir(asset_dir):
    print(os.path.join(asset_dir, i))
    data_array_merged = xr.merge([prep_bands_datacube(asset_dir, i, 'b04'),
                               prep_bands_datacube(asset_dir, i, 'b08')])
    list_data_array_merged_time.append(data_array_merged)

  ds_all = xr.concat(list_data_array_merged_time,
                   dim= xr.Variable('time', paths_to_datetimeindex(list_time)))
  
  return(ds_all)

