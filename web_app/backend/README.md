# Dockerized Flask Application Backend

This backend is a containerized Flask application designed for processing satellite imagery, managing user sessions, annotating geospatial data, and retrieving flood forecast information from an external API.

## Environment Variables

The application expects the following environment variables:

| Variable | Description |
|----------|-------------|
| `FLASK_SECRET_KEY` | Secret key for session management and CSRF protection. |
| `PSQL_DATABASE_URL` | PostgreSQL connection string. Format: `postgresql://<USER>:<PASSWORD>@<HOST>:<PORT>/<DB_NAME>` |
| `API_URL` | Flood forecast API URL (e.g., `https://hydroinfo.hu/WSCSS/ovszws/api.php`) |
| `OVSZ_TOKEN` | API token for accessing the external flood forecast service. |
| `VARID` | Numerical identifier for API request parameters (e.g. `4`). |
| `data_folder` | Base path to where your spatial files (TIFF/Shape) are located. |
| `HUNGARY_ELEVATION_MODEL` | DEM raster file name relative to `data_folder`. |
| `STATIONS_DISTANCE_LIMIT` | Max distance (in meters) from deposit to stations (default: `40000`). |
| `FLOOD_ZONE_MEDIUM` | Shapefile path for medium flood zones. |
| `FLOOD_ZONE_LOW` | Shapefile path for low flood zones. |
| `FLOOD_ZONE_HIGH` | Shapefile path for high flood zones. |
| `FLOOD_ZONE_NAGYVIZ` | Shapefile path for nagyvízi meder. |
| `POINT_CRS` | CRS code for deposit coordinates (e.g., `EPSG:23700`). |
| `DEM_CRS` | CRS code for DEM data (e.g., `EPSG:32634`). |
| `FLASK_APP` | Entry point of the Flask app. Default: `app.py`. |
| `FLASK_APP_HOST` | Host address for the Flask server. Default: `0.0.0.0`. |
| `FLASK_APP_PORT` | Port number the app listens to. Default: `5000`. |
| `FLASK_DEBUG` | Enables debug mode and CORS configuration. Default: `False`. |
| `FLASK_CORS_ORIGIN` | Allowed CORS origin during development. Default: `http://localhost:5173`. |
| `GUNICORN_WORKERS` | Number of Gunicorn worker processes. Default: `5`. |

## Running the Application

### Build Docker Image

```bash
docker build . --target web_app_backend -t web_app_backend
```

### Create PostGIS Database

```bash
psql -U postgres
CREATE DATABASE waste_detection_database;
\c waste_detection_database
CREATE EXTENSION postgis;
\q
```

### Docker Run (Basic)

```bash
docker run -d --name web_app_backend_container \
  -e FLASK_SECRET_KEY=your_secret \
  -e PSQL_DATABASE_URL=postgresql://user:password@localhost:5432/dbname \
  -e API_URL="https://hydroinfo.hu/WSCSS/ovszws/api.php" \
  -e OVSZ_TOKEN="your_token" \
  -e VARID=4 \
  -e data_folder="/app/data" \
  -e HUNGARY_ELEVATION_MODEL="output_slope.tif" \
  -e STATIONS_DISTANCE_LIMIT=40000 \
  -e FLOOD_ZONE_MEDIUM="HU_HU1000/HU_HU1000_HMP_20140322.shp" \
  -e FLOOD_ZONE_LOW="HU_HU1000/HU_HU1000_HLP_2_20140322.shp" \
  -e FLOOD_ZONE_HIGH="HU_HU1000/HU_HU1000_HHP_20140322.shp" \
  -e FLOOD_ZONE_NAGYVIZ="Adat/nagyviz_shp/Nagyvizi_meder_hatar.shp" \
  -e POINT_CRS="EPSG:23700" \
  -e DEM_CRS="EPSG:32634" \
  -e FLASK_DEBUG=True \
  -e FLASK_CORS_ORIGIN="http://localhost:5173" \
  -v /absolute/path/to/data:/app/data \
  --net=host \
  --restart always \
  web_app_backend
```

## Running Locally (without Docker)

Make sure you have Python, PostgreSQL, and PostGIS installed.

```bash
export $(cat .env | xargs)  # Or use direnv
flask run --host=0.0.0.0 --port=5000
```

## API Endpoints – Examples via curl

### Login

```bash
curl -c cookies.txt -X POST http://127.0.0.1:5000/login \
  -H "Content-Type: application/json" \
  -d '{"email": "john@example.com", "password": "password123"}'
```

### Create User

```bash
curl -X POST http://127.0.0.1:5000/users \
  -H "Content-Type: application/json" \
  -d '{"name": "John Doe", "email": "john@example.com", "password": "password123", "role": "admin"}'
```

### Add Satellite Image

```bash
curl -b cookies.txt -X POST http://127.0.0.1:5000/satellite-images \
  -H "Content-Type: application/json" \
  -d '{"filename": "image1.tif", "acquisition_date": "2023-06-01", "satellite_type": "Landsat", "src": "NASA", "min": 0.0, "max": 255.0}'
```

### Flood Forecast

```bash
curl "http://127.0.0.1:5000/flood-forecast?lat=47.0&lon=19.0&disable_filtering=false"
```

## Notes

- Always replace sensitive values before committing or sharing (`OVSZ_TOKEN`, DB credentials).
- This backend is meant to be used in conjunction with a frontend running at `http://localhost:5173`.
- For persistent volumes or logs, consider mounting additional volumes (e.g., `/app/logs`).