import up42
import os

def order(limit, aoi_geometry):
    up42.authenticate(
        username=os.getenv('USER'),
        password=os.getenv('PASSWORD'),
    )

    project = up42.initialize_project(project_id=os.getenv('PROJECT_ID'))

    catalog = up42.initialize_catalog()

    data_product_id = catalog.get_data_products(basic=True).get("Sentinel-2").get("data_products").get("Level-2A")

    data_products = catalog.get_data_products(basic=True)

    # Search and select the right scene for your use-case
    print('max limit is:', limit)
    search_results = catalog.search(search_parameters=catalog.construct_search_parameters(
        geometry=aoi_geometry, 
        start_date="2022-01-01", end_date="2022-07-31", 
        collections=[data_products.get("Sentinel-2").get("collection")],
        max_cloudcover=10, limit=limit))

    catalog.download_quicklooks(search_results.iloc[limit-1].id, collection='sentinel-2')
    catalog.plot_quicklooks()

    list_order_parameters = []
    for k in range(search_results.shape[0]):
        list_order_parameters.append(catalog.construct_order_parameters(
                                        data_product_id=data_product_id,
                                        image_id=search_results.iloc[k]["id"],
        ))
  
    for k in range(search_results.shape[0]):
        print(catalog.place_order((list_order_parameters[k]), track_status=True))
