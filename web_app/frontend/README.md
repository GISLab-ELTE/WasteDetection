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

| Name                 | Description                                                                                                                         |
| :------------------- | :---------------------------------------------------------------------------------------------------------------------------------- |
| `VITE_BASE_URL`      | Frontend application base URL. Only used in `vite.config.ts`. In the code, the built-in `BASE_URL` variable should be used instead. |
| `VITE_DATA_URL`      | Backend data URL hosting the satellite imagery and the produced classification data.                                                |
| `VITE_FLASK_URL`     | Backend Flask service URL hosting the annotation service.                                                                           |
| `VITE_GEOSERVER_URL` | Backend GeoServer URL hosting the TileWMS for flood zone maps.                                                                      |
