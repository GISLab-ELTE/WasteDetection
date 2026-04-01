# OpenLayers + Vite Application Frontend

Install the dependencies with the _NPM_ package manager:

    npm install

Then you can start the local server:

    npm start

To generate a build ready for production:

    npm run build

Then deploy the contents of the `dist` directory to your server. You can also run `npm run serve` to serve the results of the `dist` directory for preview.

## Environment Variables

### .env files

These files store the default values for environment variables.  
**Important:** the following files are version controlled.

- `.env`: common settings
- `.env.development`: development mode specific settings (`npm start`)
- `.env.production`: production mode specific settings (`npm run build`)

If you want to override an environment variable, you should create a local .env file.  
`.env*.local` files are excluded from version control.

- `.env.development.local`: local overrides used in development mode (`npm start`)
- `.env.production.local`: local overrides used in production mode (`npm run build`)

### Variables

| Name                         | Description                                                                                                                         |
| :--------------------------- | :---------------------------------------------------------------------------------------------------------------------------------- |
| `VITE_BASE_URL`              | Frontend application base URL. Only used in `vite.config.ts`. In the code, the built-in `BASE_URL` variable should be used instead. |
| `VITE_DATA_URL`              | Backend data URL hosting the satellite imagery and the produced classification data.                                                |
| `VITE_FLASK_URL`             | Backend Flask service URL hosting the annotation service.                                                                           |
| `VITE_GEOSERVER_URL`         | Backend GeoServer URL hosting the TileWMS for flood zone maps.                                                                      |
| `VITE_GOOGLE_MAPS_API_KEY`   | Google Maps API key.                                                                                                                |
| `VITE_STADIA_MAPS_API_KEY`   | Stadia Maps API key.                                                                                                                |
| `VITE_DEFAULT_LOCATION`      | Default selected location `id` from `locations.json`. If empty or unset, the first location is selected.                            |
| `VITE_DEFAULT_HEATMAP_LEVEL` | Minimum heatmap level enabled by default. Accepted values: `low`, `medium`, `high`, `none`. Defaults to `high`.                     |

## Configuration Files

### locations.json

Defines the available locations, their display names, and bounding boxes for map navigation. This file is located in the `public` directory (`public/locations.json`) and is served as a static asset.
To add or modify locations, edit the `public/locations.json` file directly. The file must be a JSON array containing location objects with the following structure:

The default selected location can be set using the `VITE_DEFAULT_LOCATION` environment variable, which should match one of the `id` values in this file.
If `VITE_DEFAULT_LOCATION` is not set or is empty, the application will default to the first location in the array.

```json
[
  {
    "id": "string",       // Unique identifier (must match AOI keys in geojson_files.json)
    "name": "string",     // Display name for the location
    "bbox": [number, number, number, number]  // Bounding box [minX, minY, maxX, maxY] in map projection (EPSG:3857)
  }
]
```

**Note**: The `id` field in the frontend's `locations.json` must match the location keys used in the `satellite_images.json` and `geojson_files.json` - produced by the _server_app_.
