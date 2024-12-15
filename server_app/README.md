# Server application for continuous waste detection

## Running the application in Docker Container

1. **Open CMD:** navigate to repository folder.
2. **Build image:** `docker build . --target server_app -t server_app`
3. **Run container:**

   ```bash
      docker run -it --name server_app_container \
        --mount type=bind,source="$(pwd)"/docker/config.docker.json,target=/mnt/config.docker.json,readonly \
        --mount type=bind,source={YOUR OUTPUT DIRECTORY},target=/mnt/output \
        server_app [download-init|download-update] [classify]
   ```

   Options:

   - `download-init`: Initialize image database: Download all the images on the given time interval.
   - `download-update`: Download new images. Cannot be used with `download-init`.
   - `classify`: Execute classification (does not download images).

## Running the application

1. **Open _Anaconda Prompt_:** navigate to repository folder.
2. **Create the virtual environment:** `conda env create -f environment.yml`. The name of the new environment will be `WasteDetection`.
3. **Activate environment:** `conda activate WasteDetection`.
4. **Run the application:** `python run_server_app.py [--download-init|--download-update] [--classify]` There are 3 flags that can be used, at least 1 must be given.
   - `--download-init`: Initialize image database: Download all the images on the given time interval.
   - `--download-update`: Download new images. Cannot be used with `--download-init`.
   - `--classify`: Execute classification (does not download images).

## Configuration

Meaning of the parameters in `config.sample.json` file:

- `workspace_root_dir`: Root directory of workspace.
- `download_dir_planetscope`: Download destination of PlanetScope images. Relative to `workspace_root_dir`.
- `download_dir_sentinel_2`: Download destination of Sentinel-2 images. Relative to `workspace_root_dir`.
- `result_dir_planetscope`: Output directory of result GeoJSON files created from PlanetScope images. Relative to `workspace_root_dir`.
- `result_dir_sentinel_2`: Output directory of result GeoJSON files created from Sentinel-2 images. Relative to `workspace_root_dir`.
- `estimations_file_path`: Path of the file that will contain the estimation of the polluted areas' extension. Relative to `workspace_root_dir`.
- `geojson_files_path`: Path of the dynamically produced JSON file that stores the location of the result GeoJSONs. Relative to `workspace_root_dir`.
- `satellite_images_path`: Path of the dynamically produced JSON file that stores the location of the downloaded satellite images. Relative to `workspace_root_dir`.
- `planet_api_key`: Planet Account API key.
- `sentinel_sh_client_id`: Account OAuth client ID in SentinelHub.
- `sentinel_instance_id`: Account User ID in SentinelHub.
- `sentinel_sh_client_secret`: Account OAuth Secret in SentinelHub.
- `satellite_type`: Name of the satellite that took the images.
- `data_file_path`: Path of the GeoJSON file containing the AOIs.
- `observation_span_in_days`: Number of days to analyze.
- `max_cloud_cover`: Cloud coverage in percentage.
- `min_coverage`: Minimum image coverage in percentage.
- `clf_path`: Path of Random Forest classifier.
- `clf_id`: The Id of the Random Forest classifier.
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
- `minimum_image_age`: The minimum age of an image in days. The server app will search for images that are atleast as old as the minimum age.
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
- `masking`: Turn water and cloud masking on.
- `udm2_eliminator`: The value to mask out in UDM2 cloud masking.
- `udm2_masking_bands`: List of UDM2 bands to use in cloud masking.
- `invert_water_mask`: Inverts created water mask.
- `open_kernel`: The size of the ellíptic kernel in pixel, used for morphologically opening the water mask.
- `close_kernel`: The size of the ellíptic kernel in pixel. Used for morphologically closing the water mask.
- `dilute_kernel`: The size of the ellíptic kernel in pixel. Used for morphologically diluting the water mask.
- `minimum_confidence`: The minimum confidence above which the program accepts an udm2 mask value.
- `planetscope_udm2_clear`: The index of the Clear band on the PlanetScope UDM2 image.
- `planetscope_udm2_snow`: The index of the Snow band on the PlanetScope UDM2 image.
- `planetscope_udm2_cloud_shadow`: The index of the Cloud Shadow band on the PlanetScope UDM2 image.
- `planetscope_udm2_light_haze`: The index of the Light Haze band on the PlanetScope UDM2 image.
- `planetscope_udm2_heavy_haze`: The index of the Heavy Haze band on the PlanetScope UDM2 image.
- `planetscope_udm2_cloud`: The index of the Cloud band on the PlanetScope UDM2 image.
- `planetscope_udm2_confidence`: The index of the Confidence band on the PlanetScope UDM2 image.

These values can be overridden if you create a `config.local.json` file in the `resources` folder. In this it is enough to include the fields that you want to change the value of.
