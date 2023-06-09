# Server application for continuous waste detection

## Running the application in Docker Container
1. **Build image:** `docker build -t server_app .`
2. **Run container:** `docker run -it --name server_app_container --mount type=bind,source="$(pwd)"/docker/config.docker.json,target=/mnt/config.docker.json,readonly --mount type=bind,source={YOUR OUTPUT DIRECTORY},target=/mnt/output server_app [startup] [sleep]`
    - `startup`: Starts a startup process before the main loop.
    - `sleep`: Sleeps after execution until the previously set local time.

## Running the application

1. **Create the virtual environment:** `conda env create -f environment.yml`. The name of the new environment will be `WasteDetectionServerApp`.
2. **Activate environment:** `conda activate WasteDetectionServerApp`.
3. **Run the application:** `python __main__.py (-st) (-s)` There are two flags that can be used optionally:
    - `-st`: Starts a startup process before the main loop.
    - `-s`: Sleeps after execution until the previously set local time.
   

## Configuration

Meaning of the parameters in `config.sample.json` file:

- `download_dir_planetscope`: Download destination of PlanetScope images.
- `download_dir_sentinel-2`: Download destination of Sentinel-2 images.
- `result_dir_planetscope`: Output directory of result GeoJSON files created from PlanetScope images.
- `result_dir_sentinel-2`: Output directory of result GeoJSON files created from Sentinel-2 images.
- `estimations_file_path`: Path of the file that will contain the estimation of the polluted areas' extension.
- `geojson_files_path`: Path of the dynamically produced JSON file that stores the location of the result GeoJSONs. 
- `planet_api_key`: Planet Account API key.
- `sentinel_sh_client_id`: Account OAuth client ID in SentinelHub.
- `sentinel_instance_id`: Account User ID in SentinelHub.
- `sentinel_sh_client_secret`: Account OAuth Secret in SentinelHub.
- `satellite_type`: Name of the satellite that took the images.
- `data_file_path`: Path of the GeoJSON file containing the AOIs.
- `observation_span_in_days`: Number of days to analyze.
- `max_cloud_cover`: Cloud coverage in percentage.
- `clf_path`: Path of Random Forest classifier.
- `classification_postfix`: File name postfix of classified image.
- `heatmap_postfix`: File name postfix of heatmap image.
- `masked_classification_postfix`: File name postfix of masked classified image.
- `masked_heatmap_postfix`: File name postfix of masked heatmap image.
- `file_extension`: Extension of result images.
- `garbage_c_id`: Class ID of garbage class.
- `water_c_id`: Class ID of water class.
- `morphology_matrix_size`: Matrix size (N x N) of kernel in morphological transformations.
- `morphology_iterations`: Number of iterations in morphological transformations.
- `planet_item_type`: Represents the class of spacecraft and/or processing level of an item (in the Planet API, an item is an entry in our catalog, and generally represents a single logical observation (or scene) captured by a satellite).
- `planet_orders_url`: URL for placing orders using Planet API.
- `planet_search_url`: URL for searching images using Planet API.
- `download_start_time`: Start time of downloading.
- `first_sentinel-2_date`: Date of first ever acquisition of Sentinel-2.
- `low_prob_percent`: Threshold percentage of the classifier's prediction confidence for low probability.
- `medium_prob_percent`: Threshold percentage of the classifier's prediction confidence for medium probability.
- `high_prob_percent`: Threshold percentage of the classifier's prediction confidence for high probability.
- `sentinel-2_blue`: The index of the Blue band on the Sentinel-2 image.
- `sentinel-2_green`: The index of the Green band on the Sentinel-2 image.
- `sentinel-2_red`: The index of the Red band on the Sentinel-2 image.
- `sentinel-2_nir`: The index of the NIR band on the Sentinel-2 image.
- `planetscope_blue`: The index of the Blue band on the PlanetScope image.
- `planetscope_green`: The index of the Green band on the PlanetScope image.
- `planetscope_red`: The index of the Red band on the PlanetScope image.
- `planetscope_nir`: The index of the NIR band on the PlanetScope image.

These values can be overridden if you create a `config.local.json` file in the `resources` folder. In this it is enough to include the fields that you want to change the value of.
