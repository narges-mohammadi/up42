import httpx
from httpx_auth import OAuth2ClientCredentials
from IPython.display import JSON, DisplayObject
import asset
from typing import Final
import os

_UP42_AUTH_URL: Final[str] = "https://api.up42.com/oauth/token"

client_auth = OAuth2ClientCredentials(
                _UP42_AUTH_URL,
                client_id = "53caf794-d4af-4f24-96d5-fedcbaa27e67",
                client_secret = "fyRfimk0.B281MMelUyl4IeAIqJLNTo38R5QrCOAWv7s"
        )

def up42_asset_stac_url(url: str) -> str:
    """Create a UP42 Spatial Asset service URL."""
    return f"https://api.up42.com/v2/assets/stac{url}"

def ppjson(json_data: dict, expand:bool=True) -> DisplayObject:
    """Pretty print JSON data."""
    return JSON(json_data, expanded=expand)

def search_item(req_body:dict, client_auth) -> httpx.Response:
    """Searches for a STAC item according to the given criteria."""
    return httpx.post(up42_asset_stac_url("/search"),
                      headers={"content-type":"application/json"},
                      auth=client_auth,
                      json=req_body)

def download_asset(url, path, client_auth) -> None:
    """Downloads an asset with the given ID."""
    with open(path, 'wb') as output:
        with httpx.stream("GET",
                          url,
                          auth=client_auth, follow_redirects=True) as r:
            for data in r.iter_bytes():
                output.write(data)

def download_search_request(complex_search_results_max_lim, 
                            complex_search_results_max_lim_asset_ids, 
                            asset_dir):
    for i in range(len(complex_search_results_max_lim_asset_ids)):
        try:
            print(complex_search_results_max_lim["features"][i]['properties']['datetime'].split('T')[0])

            path = os.path.join(asset_dir,
                       complex_search_results_max_lim["features"][i]['properties']['datetime'].split('T')[0])
            os.mkdir(path)
            b04_url = (complex_search_results_max_lim["features"][i]['assets']['b04.tiff']['href'])
            b08_url = (complex_search_results_max_lim["features"][i]['assets']['b08.tiff']['href'])
            file_path_b04 = os.path.join(path, 'b04.tiff')
            file_path_b08 = os.path.join(path, 'b08.tiff')
            download_asset(b04_url, file_path_b04, client_auth)
            download_asset(b08_url, file_path_b08, client_auth)
            print('**********************************************')
        except FileExistsError:
            continue

